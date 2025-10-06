from flask import Flask, request, jsonify
import requests
import json
import os
import tempfile
import logging
import hashlib
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', '3e43c56e7bda92b003f12bcb46ae94dcd2c1b8f4')
ZAPIER_WEBHOOK_URL = os.getenv('ZAPIER_WEBHOOK_URL')

# In-memory storage for processed files (in production, use Redis or database)
processed_files = {}
PROCESSED_FILES_CLEANUP_HOURS = 24  # Clean up old entries after 24 hours

def generate_file_hash(file_url, file_size, timestamp):
    """Generate a unique hash for the file to prevent duplicates"""
    try:
        # Create a unique identifier based on file URL, size, and timestamp
        unique_string = f"{file_url}_{file_size}_{timestamp}"
        file_hash = hashlib.md5(unique_string.encode()).hexdigest()
        return file_hash
    except Exception as e:
        logger.error(f"❌ Error generating file hash: {str(e)}")
        return None

def is_file_processed(file_hash):
    """Check if file has already been processed"""
    try:
        if file_hash in processed_files:
            # Check if the entry is still valid (not expired)
            entry_time = processed_files[file_hash]['timestamp']
            if datetime.now() - entry_time < timedelta(hours=PROCESSED_FILES_CLEANUP_HOURS):
                logger.info(f"🔄 File already processed: {file_hash}")
                return True
            else:
                # Remove expired entry
                del processed_files[file_hash]
                logger.info(f"🗑️ Removed expired entry: {file_hash}")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking processed files: {str(e)}")
        return False

def mark_file_processed(file_hash, transcript, metadata):
    """Mark file as processed with timestamp"""
    try:
        processed_files[file_hash] = {
            'timestamp': datetime.now(),
            'transcript': transcript,
            'metadata': metadata,
            'status': 'completed'
        }
        logger.info(f"✅ File marked as processed: {file_hash}")
        return True
    except Exception as e:
        logger.error(f"❌ Error marking file as processed: {str(e)}")
        return False

def cleanup_old_entries():
    """Clean up old processed file entries"""
    try:
        current_time = datetime.now()
        expired_entries = []
        
        for file_hash, entry in processed_files.items():
            if current_time - entry['timestamp'] > timedelta(hours=PROCESSED_FILES_CLEANUP_HOURS):
                expired_entries.append(file_hash)
        
        for file_hash in expired_entries:
            del processed_files[file_hash]
        
        if expired_entries:
            logger.info(f"🗑️ Cleaned up {len(expired_entries)} expired entries")
        
        return len(expired_entries)
    except Exception as e:
        logger.error(f"❌ Error cleaning up old entries: {str(e)}")
        return 0

def download_file_from_slack(file_url, slack_token):
    """Download file from Slack (audio or Quip document)"""
    try:
        logger.info(f"📥 Downloading file from Slack: {file_url}")
        
        headers = {
            'Authorization': f'Bearer {slack_token}'
        }
        
        response = requests.get(file_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            file_size = len(response.content)
            logger.info(f"📥 Content-Type: {content_type}")
            logger.info(f"📥 File size: {file_size} bytes")
            
            # Determine file extension based on content type
            if 'audio/mpeg' in content_type:
                ext = '.mp3'
            elif 'audio/wav' in content_type:
                ext = '.wav'
            elif 'audio/mp4' in content_type:
                ext = '.m4a'
            elif 'application/vnd.slack-docs' in content_type:
                ext = '.quip'
            else:
                ext = '.mp3'  # Default
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            logger.info(f"✅ File downloaded successfully: {temp_file_path}")
            return temp_file_path, file_size, content_type
        else:
            logger.error(f"❌ Failed to download file: {response.status_code}")
            return None, 0, None
            
    except Exception as e:
        logger.error(f"❌ Error downloading file: {str(e)}")
        return None, 0, None

def process_quip_document(file_path):
    """Process Quip document to extract text content"""
    try:
        logger.info("📄 Processing Quip document...")
        
        with open(file_path, 'rb') as file:
            content = file.read()
        
        logger.info(f"📄 Document size: {len(content)} bytes")
        
        # Try to decode as text first
        try:
            text_content = content.decode('utf-8')
            logger.info("✅ Document read as text")
            logger.info(f"📄 Text content length: {len(text_content)}")
            
            # If it's HTML, try to extract text content
            if '<html' in text_content.lower() or '<body' in text_content.lower():
                logger.info("📄 Detected HTML content, extracting text...")
                # Simple HTML text extraction (remove tags)
                import re
                clean_text = re.sub(r'<[^>]+>', '', text_content)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                logger.info(f"📄 Extracted text length: {len(clean_text)}")
                return clean_text
            else:
                return text_content
                
        except Exception as e:
            logger.info(f"📄 UTF-8 decode failed: {str(e)}")
            # Try base64 decode
            try:
                decoded_content = base64.b64decode(content).decode('utf-8')
                logger.info("✅ Base64 decoded successfully")
                logger.info(f"📄 Decoded content length: {len(decoded_content)}")
                return decoded_content
            except Exception as e2:
                logger.error(f"❌ Base64 decode failed: {str(e2)}")
                # Try to return raw content as string
                try:
                    raw_content = str(content)
                    logger.info("✅ Returning raw content as string")
                    return raw_content
                except Exception as e3:
                    logger.error(f"❌ All decode methods failed: {str(e3)}")
                    return None
                
    except Exception as e:
        logger.error(f"❌ Error processing document: {str(e)}")
        return None

def transcribe_with_deepgram(audio_file_path):
    """Transcribe audio using Deepgram API"""
    try:
        logger.info("🎤 Transcribing with Deepgram...")
        
        with open(audio_file_path, 'rb') as audio_file:
            headers = {
                'Authorization': f'Token {DEEPGRAM_API_KEY}',
                'Content-Type': 'audio/mp3'
            }
            
            response = requests.post(
                'https://api.deepgram.com/v1/listen',
                headers=headers,
                data=audio_file,
                params={
                    'model': 'nova-2',
                    'language': 'en-US',
                    'punctuate': 'true',
                    'smart_format': 'true'
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                logger.info("✅ Deepgram transcription successful")
                return transcript.strip()
            else:
                logger.error(f"❌ Deepgram transcription failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Deepgram transcription error: {str(e)}")
        return None

def process_file_content(file_path, content_type):
    """Process file content based on type (audio or Quip)"""
    try:
        if 'audio/' in content_type:
            # Process as audio file
            logger.info("🎤 Processing as audio file")
            return transcribe_with_deepgram(file_path)
        elif 'application/vnd.slack-docs' in content_type or 'text/html' in content_type:
            # Process as Quip document or HTML content
            logger.info("📄 Processing as Quip document or HTML content")
            return process_quip_document(file_path)
        else:
            logger.error(f"❌ Unsupported content type: {content_type}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error processing file content: {str(e)}")
        return None

def send_to_zapier(transcript, metadata):
    """Send transcription data to Zapier webhook"""
    try:
        logger.info("📤 Sending data to Zapier...")
        
        if not ZAPIER_WEBHOOK_URL:
            logger.error("❌ Zapier webhook URL not configured")
            return None
        
        data = {
            'transcript': transcript,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(ZAPIER_WEBHOOK_URL, json=data, timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Data sent to Zapier successfully")
            return True
        else:
            logger.error(f"❌ Failed to send to Zapier: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Zapier webhook error: {str(e)}")
        return False

@app.route('/', methods=['GET'])
def home():
    # Clean up old entries on health check
    cleanup_old_entries()
    
    return jsonify({
        'status': 'running',
        'message': 'Slack Voice to Zapier Middleware (Supports Audio & Quip)',
        'version': '1.1.0',
        'endpoints': {
            'slack_webhook': '/slack-webhook',
            'health': '/',
            'status': '/status'
        },
        'processed_files_count': len(processed_files),
        'duplicate_prevention': 'enabled',
        'supported_formats': ['audio/mpeg', 'audio/wav', 'audio/mp4', 'application/vnd.slack-docs', 'text/html']
    })

@app.route('/status', methods=['GET'])
def status():
    """Get detailed status including processed files"""
    cleanup_old_entries()
    
    return jsonify({
        'status': 'healthy',
        'processed_files_count': len(processed_files),
        'duplicate_prevention': 'enabled',
        'cleanup_hours': PROCESSED_FILES_CLEANUP_HOURS,
        'recent_files': list(processed_files.keys())[-10:],  # Last 10 processed files
        'supported_formats': ['audio/mpeg', 'audio/wav', 'audio/mp4', 'application/vnd.slack-docs', 'text/html']
    })

@app.route('/slack-webhook', methods=['POST'])
def slack_webhook():
    """Handle Slack file webhooks with support for audio and Quip documents"""
    try:
        data = request.get_json()
        logger.info(f"📨 Received Slack webhook: {json.dumps(data, indent=2)}")
        
        # Extract Slack data
        file_url = data.get('file_url')
        slack_token = data.get('slack_token')
        user_email = data.get('user_email')
        user_phone = data.get('user_phone')
        user_name = data.get('user_name')
        channel_name = data.get('channel_name')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if not file_url or not slack_token:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Step 1: Download file to get content type and size
        file_path, file_size, content_type = download_file_from_slack(file_url, slack_token)
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'Failed to download file'
            }), 400
        
        # Step 2: Generate file hash for duplicate prevention
        file_hash = generate_file_hash(file_url, file_size, timestamp)
        if not file_hash:
            return jsonify({
                'success': False,
                'error': 'Failed to generate file hash'
            }), 400
        
        # Step 3: Check if file has already been processed
        if is_file_processed(file_hash):
            logger.info(f"🔄 File already processed, skipping: {file_hash}")
            return jsonify({
                'success': True,
                'message': 'File already processed, skipping duplicate',
                'file_hash': file_hash,
                'duplicate_prevention': 'triggered'
            })
        
        # Step 4: Process file content (audio transcription or Quip text extraction)
        transcript = process_file_content(file_path, content_type)
        if not transcript:
            logger.error(f"❌ Failed to process file content. Content type: {content_type}")
            return jsonify({
                'success': False,
                'error': f'Failed to process file content. Content type: {content_type}',
                'content_type': content_type,
                'file_size': file_size
            }), 400
        
        # Step 5: Mark file as processed
        metadata = {
            'user_email': user_email,
            'user_phone': user_phone,
            'user_name': user_name,
            'channel_name': channel_name,
            'file_url': file_url,
            'file_hash': file_hash,
            'content_type': content_type,
            'file_size': file_size
        }
        
        mark_file_processed(file_hash, transcript, metadata)
        
        # Step 6: Send to Zapier
        zapier_success = send_to_zapier(transcript, metadata)
        
        # Clean up temporary file
        try:
            os.unlink(file_path)
        except:
            pass
        
        if zapier_success:
            return jsonify({
                'success': True,
                'message': 'File processed and sent to Zapier',
                'transcript': transcript,
                'file_hash': file_hash,
                'content_type': content_type,
                'duplicate_prevention': 'passed'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send to Zapier'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Slack webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Slack Voice to Zapier Middleware on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
