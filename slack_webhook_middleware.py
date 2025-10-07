#!/usr/bin/env python3
"""
Slack Webhook Middleware for Zapier Integration
Processes Slack audio files and creates Zoho Desk tickets
Uses OAuth token authentication (like zoho-call-tickets project)
"""

import os
import json
import logging
import asyncio
import aiohttp
import tempfile
import re
import hashlib
import sqlite3
import requests
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from flask import Flask, request, jsonify
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
ZOHO_DESK_ACCESS_TOKEN = os.getenv('ZOHO_DESK_ACCESS_TOKEN')
ZOHO_DESK_REFRESH_TOKEN = os.getenv('ZOHO_DESK_REFRESH_TOKEN')
ZOHO_DESK_CLIENT_ID = os.getenv('ZOHO_DESK_CLIENT_ID')
ZOHO_DESK_CLIENT_SECRET = os.getenv('ZOHO_DESK_CLIENT_SECRET')
ZOHO_DESK_ORG_ID = os.getenv('ZOHO_DESK_ORG_ID')
ZOHO_DESK_DOMAIN = os.getenv('ZOHO_DESK_DOMAIN', 'desk.zoho.com')
ZOHO_DESK_DEPARTMENT_ID = os.getenv('ZOHO_DESK_DEPARTMENT_ID')
TRANSCRIPTION_API_KEY = os.getenv('TRANSCRIPTION_API_KEY')
TRANSCRIPTION_PROVIDER = os.getenv('TRANSCRIPTION_PROVIDER', 'deepgram')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@dataclass
class SlackFileInfo:
    """Data class for Slack file information"""
    file_url: str
    file_name: str
    user_id: str
    channel_id: str
    timestamp: str
    file_type: str
    is_canvas: bool = False
    canvas_audio_links: list = None

@dataclass
class CanvasData:
    """Data class for Canvas file information"""
    canvas_text: str
    audio_links: list
    file_id: str

@dataclass
class TranscriptionResult:
    """Data class for transcription results"""
    success: bool
    transcript: Optional[str] = None
    error: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class ZohoTicket:
    """Data class for Zoho Desk ticket"""
    ticket_id: str
    subject: str
    status: str
    priority: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class FileTracker:
    """Tracks processed files to prevent duplicates"""
    
    def __init__(self, db_path="processed_files.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for file tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    file_hash TEXT PRIMARY KEY,
                    file_name TEXT,
                    file_url TEXT,
                    user_id TEXT,
                    channel_id TEXT,
                    processed_at TIMESTAMP,
                    status TEXT,
                    ticket_id TEXT
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("File tracking database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def get_file_hash(self, file_url: str, file_name: str, user_id: str, channel_id: str) -> str:
        """Generate unique hash for file identification"""
        content = f"{file_url}_{file_name}_{user_id}_{channel_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_file_processed(self, file_url: str, file_name: str, user_id: str, channel_id: str) -> bool:
        """Check if file has already been processed"""
        try:
            file_hash = self.get_file_hash(file_url, file_name, user_id, channel_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_files WHERE file_hash = ?",
                (file_hash,)
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking file status: {str(e)}")
            return False
    
    def mark_file_processed(self, file_url: str, file_name: str, user_id: str, channel_id: str, status: str = "completed", ticket_id: str = None):
        """Mark file as processed"""
        try:
            file_hash = self.get_file_hash(file_url, file_name, user_id, channel_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO processed_files 
                (file_hash, file_name, file_url, user_id, channel_id, processed_at, status, ticket_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_hash, file_name, file_url, user_id, channel_id, datetime.now().isoformat(), status, ticket_id))
            conn.commit()
            conn.close()
            logger.info(f"File marked as processed: {file_name}")
        except Exception as e:
            logger.error(f"Error marking file as processed: {str(e)}")
    
    def get_processing_status(self, file_url: str, file_name: str, user_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status of a file"""
        try:
            file_hash = self.get_file_hash(file_url, file_name, user_id, channel_id)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM processed_files WHERE file_hash = ?",
                (file_hash,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'file_hash': result[0],
                    'file_name': result[1],
                    'file_url': result[2],
                    'user_id': result[3],
                    'channel_id': result[4],
                    'processed_at': result[5],
                    'status': result[6],
                    'ticket_id': result[7]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting file status: {str(e)}")
            return None

class ZohoOAuthManager:
    """Manages Zoho Desk OAuth authentication using pre-obtained tokens (like zoho-call-tickets)"""
    
    def __init__(self):
        self.access_token = ZOHO_DESK_ACCESS_TOKEN
        self.refresh_token = ZOHO_DESK_REFRESH_TOKEN
        self.client_id = ZOHO_DESK_CLIENT_ID
        self.client_secret = ZOHO_DESK_CLIENT_SECRET
        self.org_id = ZOHO_DESK_ORG_ID
        self.token_expires_at = None
    
    async def get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        try:
            # Check if we have a valid token
            if self.access_token and self.token_expires_at and datetime.now().timestamp() < self.token_expires_at:
                return self.access_token
            
            # Need to refresh token
            if self.refresh_token:
                return await self._refresh_access_token()
            else:
                logger.error("No refresh token available")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    async def _refresh_access_token(self) -> Optional[str]:
        """Refresh access token using refresh token (like zoho-call-tickets)"""
        try:
            url = "https://accounts.zoho.com/oauth/v2/token"
            data = {
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result['access_token']
                        self.token_expires_at = datetime.now().timestamp() + result['expires_in']
                        logger.info("Zoho access token refreshed successfully")
                        return self.access_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to refresh Zoho token: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {str(e)}")
            return None
    
    def get_headers(self):
        """Get API headers with authentication (like zoho-call-tickets)"""
        return {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "orgId": self.org_id,
            "Content-Type": "application/json"
        }

class CanvasParser:
    """Handles Slack Canvas file parsing and audio extraction"""
    
    def __init__(self, slack_token: str):
        self.slack_token = slack_token
    
    def download_and_parse_canvas(self, file_id: str) -> Optional[CanvasData]:
        """Download and parse Canvas file to extract audio links"""
        try:
            # Step 1: Get file info
            file_info_url = f"https://slack.com/api/files.info?file={file_id}"
            headers = {"Authorization": f"Bearer {self.slack_token}"}
            file_info_resp = requests.get(file_info_url, headers=headers)

            if not file_info_resp.ok:
                logger.error(f"Failed to fetch file info: {file_info_resp.text}")
                return None

            file_data = file_info_resp.json().get("file", {})
            file_url = file_data.get("url_private_download")
            mimetype = file_data.get("mimetype")

            # Step 2: Download Canvas file
            if not isinstance(file_url, str):
                logger.error(f"Invalid file_url: {file_url}")
                return None

            canvas_resp = requests.get(file_url, headers=headers)
            if not canvas_resp.ok:
                logger.error(f"Failed to download canvas file: {canvas_resp.text}")
                return None

            canvas_content = canvas_resp.content

            # Step 3: Parse Canvas blocks via canvas.info
            canvas_info_url = f"https://slack.com/api/canvas.info?canvas_id={file_id}"
            canvas_info_resp = requests.get(canvas_info_url, headers=headers)

            if not canvas_info_resp.ok:
                logger.error(f"Failed to fetch canvas info: {canvas_info_resp.text}")
                return None

            blocks = canvas_info_resp.json().get("canvas", {}).get("blocks", [])

            audio_links = []
            for block in blocks:
                if block.get("type") == "rich_text":
                    elements = block.get("elements", [])
                    for el in elements:
                        if el.get("type") == "link" and el.get("url", "").endswith((".mp3", ".wav", ".m4a", ".mp4")):
                            audio_links.append(el["url"])
                elif block.get("type") == "file":
                    file_url = block.get("file", {}).get("url_private_download")
                    if file_url and file_url.endswith((".mp3", ".wav", ".m4a", ".mp4")):
                        audio_links.append(file_url)

            logger.info(f"Extracted {len(audio_links)} audio links from Canvas")

            return CanvasData(
                canvas_text=canvas_content.decode("utf-8", errors="ignore"),
                audio_links=audio_links,
                file_id=file_id
            )
            
        except Exception as e:
            logger.error(f"Error parsing Canvas file: {str(e)}")
            return None
    
    def is_canvas_file(self, file_type: str, mimetype: str = None) -> bool:
        """Check if file is a Slack Canvas file"""
        canvas_indicators = [
            'canvas',
            'application/vnd.slack.canvas',
            'text/canvas'
        ]
        
        if mimetype:
            return any(indicator in mimetype.lower() for indicator in canvas_indicators)
        
        return file_type.lower() == 'canvas'

class AudioConverter:
    """Handles audio file conversion from MP4 to MP3"""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH"""
        try:
            # Check if ffmpeg is in PATH
            result = subprocess.run(['ffmpeg', '-version'], 
                                 capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'ffmpeg'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check common installation paths
        common_paths = [
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("FFmpeg not found in PATH or common locations")
        return None
    
    def is_audio_file(self, file_path: str) -> bool:
        """Check if file is an audio file using FFprobe"""
        try:
            if not self.ffmpeg_path:
                # Fallback: check file extension
                audio_extensions = ['.mp3', '.mp4', '.wav', '.m4a', '.aac', '.ogg', '.flac']
                return any(file_path.lower().endswith(ext) for ext in audio_extensions)
            
            # Use ffprobe to detect audio streams
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-v', 'quiet',
                '-select_streams', 'a',
                '-show_entries', 'stream=codec_type',
                '-of', 'csv=p=0',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return 'audio' in result.stdout.lower()
            
        except Exception as e:
            logger.error(f"Error checking audio file: {str(e)}")
            # Fallback to extension check
            audio_extensions = ['.mp3', '.mp4', '.wav', '.m4a', '.aac', '.ogg', '.flac']
            return any(file_path.lower().endswith(ext) for ext in audio_extensions)
    
    def convert_to_mp3(self, input_path: str, output_path: str = None) -> Optional[str]:
        """Convert audio file to MP3 format"""
        try:
            if not self.ffmpeg_path:
                logger.error("FFmpeg not available for audio conversion")
                return None
            
            if not output_path:
                # Create output path with .mp3 extension
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_converted.mp3"
            
            # FFmpeg command for audio conversion
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-acodec', 'mp3',
                '-ab', '128k',  # 128 kbps bitrate
                '-ar', '44100',  # 44.1 kHz sample rate
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Converting audio: {input_path} -> {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Audio conversion successful: {output_path}")
                return output_path
            else:
                logger.error(f"Audio conversion failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Audio conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            return None
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """Get audio file duration in seconds"""
        try:
            if not self.ffmpeg_path:
                return None
            
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return None

class SlackWebhookProcessor:
    """Main processor for handling Slack webhook requests"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.file_tracker = FileTracker()
        self.zoho_oauth = ZohoOAuthManager()
        self.audio_converter = AudioConverter()
        self.canvas_parser = CanvasParser(SLACK_BOT_TOKEN)
    
    async def process_slack_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Slack webhook from Zapier"""
        try:
            # Extract Slack file information
            file_info = self._extract_slack_file_info(payload)
            if not file_info:
                return {
                    'success': False,
                    'error': 'Invalid payload: missing required Slack file information'
                }
            
            # Check if file has already been processed
            if self.file_tracker.is_file_processed(
                file_info.file_url, file_info.file_name, file_info.user_id, file_info.channel_id
            ):
                existing_status = self.file_tracker.get_processing_status(
                    file_info.file_url, file_info.file_name, file_info.user_id, file_info.channel_id
                )
                logger.info(f"File already processed: {file_info.file_name}")
                return {
                    'success': True,
                    'message': 'File already processed - skipping duplicate',
                    'file_name': file_info.file_name,
                    'status': existing_status.get('status', 'completed'),
                    'ticket_id': existing_status.get('ticket_id'),
                    'processed_at': existing_status.get('processed_at'),
                    'duplicate': True
                }
            
            logger.info(f"Processing new Slack file: {file_info.file_name} from user {file_info.user_id}")
            
            # Mark file as being processed
            self.file_tracker.mark_file_processed(
                file_info.file_url, file_info.file_name, file_info.user_id, file_info.channel_id,
                status="processing"
            )
            
            # Start async processing
            self.executor.submit(self._process_file_async, file_info)
            
            # Return immediate response to Zapier
            return {
                'success': True,
                'message': 'File processing started',
                'file_name': file_info.file_name,
                'timestamp': datetime.now().isoformat(),
                'duplicate': False
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}'
            }
    
    def _extract_slack_file_info(self, payload: Dict[str, Any]) -> Optional[SlackFileInfo]:
        """Extract Slack file information from webhook payload"""
        try:
            # Expected payload structure from Zapier
            file_info = payload.get('file_info', {})
            file_type = file_info.get('filetype', 'unknown')
            mimetype = file_info.get('mimetype', '')
            
            # Check if it's a Canvas file
            is_canvas = self.canvas_parser.is_canvas_file(file_type, mimetype)
            
            return SlackFileInfo(
                file_url=file_info.get('url_private'),
                file_name=file_info.get('name', 'unknown'),
                user_id=payload.get('user_id'),
                channel_id=payload.get('channel_id'),
                timestamp=payload.get('timestamp', str(datetime.now().timestamp())),
                file_type=file_type,
                is_canvas=is_canvas,
                canvas_audio_links=[]
            )
        except Exception as e:
            logger.error(f"Error extracting file info: {str(e)}")
            return None
    
    def _process_file_async(self, file_info: SlackFileInfo):
        """Process file asynchronously in background thread"""
        try:
            # Run async processing in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_process_file(file_info))
            loop.close()
        except Exception as e:
            logger.error(f"Error in async processing: {str(e)}")
    
    async def _async_process_file(self, file_info: SlackFileInfo):
        """Async file processing pipeline"""
        audio_file_path = None
        converted_audio_path = None
        
        try:
            if file_info.is_canvas:
                # Handle Canvas file with embedded audio
                await self._process_canvas_file(file_info)
            else:
                # Handle regular audio file
                await self._process_regular_audio_file(file_info)
            
        except Exception as e:
            logger.error(f"Error in file processing pipeline: {str(e)}")
        finally:
            # Cleanup temporary files
            for file_path in [audio_file_path, converted_audio_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")
    
    async def _process_canvas_file(self, file_info: SlackFileInfo):
        """Process Canvas file with embedded audio"""
        try:
            # Extract file ID from URL or payload
            file_id = self._extract_file_id_from_url(file_info.file_url)
            if not file_id:
                logger.error(f"Could not extract file ID from URL: {file_info.file_url}")
                return
            
            # Parse Canvas file
            canvas_data = self.canvas_parser.download_and_parse_canvas(file_id)
            if not canvas_data:
                logger.error(f"Failed to parse Canvas file: {file_info.file_name}")
                return
            
            logger.info(f"Canvas file contains {len(canvas_data.audio_links)} audio files")
            
            # Process each audio file
            all_transcripts = []
            for i, audio_url in enumerate(canvas_data.audio_links):
                try:
                    logger.info(f"Processing audio {i+1}/{len(canvas_data.audio_links)}: {audio_url}")
                    
                    # Download audio file
                    audio_file_path = await self._download_audio_from_url(audio_url, f"canvas_audio_{i}")
                    if not audio_file_path:
                        continue
                    
                    # Convert to MP3 if needed
                    converted_path = await self._convert_audio_if_needed(audio_file_path, file_info)
                    if not converted_path:
                        continue
                    
                    # Transcribe audio
                    transcript_result = await self._transcribe_audio(converted_path)
                    if transcript_result.success:
                        all_transcripts.append(transcript_result.transcript)
                        logger.info(f"Transcribed audio {i+1}: {len(transcript_result.transcript)} characters")
                    else:
                        logger.error(f"Transcription failed for audio {i+1}: {transcript_result.error}")
                    
                    # Cleanup
                    for path in [audio_file_path, converted_path]:
                        if path and os.path.exists(path):
                            os.remove(path)
                            
                except Exception as e:
                    logger.error(f"Error processing audio {i+1}: {str(e)}")
                    continue
            
            if not all_transcripts:
                logger.error("No audio files were successfully transcribed")
                return
            
            # Combine all transcripts
            combined_transcript = "\n\n--- Audio Segment ---\n\n".join(all_transcripts)
            logger.info(f"Combined transcript length: {len(combined_transcript)} characters")
            
            # Extract contact information from combined transcript
            contact_info = self._extract_contact_info(combined_transcript)
            
            # Create Zoho Desk ticket with Canvas content and audio transcripts
            ticket = await self._create_canvas_zoho_ticket(
                canvas_data, combined_transcript, contact_info, file_info
            )
            
            # Post feedback to Slack
            if ticket:
                await self._post_slack_feedback(file_info, ticket)
            
            # Mark file as completed
            self.file_tracker.mark_file_processed(
                file_info.file_url, file_info.file_name, file_info.user_id, file_info.channel_id,
                status="completed", ticket_id=ticket.ticket_id if ticket else None
            )
            
        except Exception as e:
            logger.error(f"Error processing Canvas file: {str(e)}")
    
    async def _process_regular_audio_file(self, file_info: SlackFileInfo):
        """Process regular audio file (non-Canvas)"""
        audio_file_path = None
        converted_audio_path = None
        
        try:
            # Step 1: Download audio file from Slack
            audio_file_path = await self._download_slack_file(file_info)
            if not audio_file_path:
                logger.error(f"Failed to download file: {file_info.file_name}")
                return
            
            # Step 2: Check if file is audio and convert if needed
            if not self.audio_converter.is_audio_file(audio_file_path):
                logger.warning(f"File may not be audio: {file_info.file_name}")
                # Continue anyway, let transcription service handle it
            
            # Step 3: Convert to MP3 if needed
            converted_audio_path = await self._convert_audio_if_needed(audio_file_path, file_info)
            if not converted_audio_path:
                logger.error(f"Audio conversion failed for: {file_info.file_name}")
                return
            
            # Step 4: Transcribe audio
            transcript_result = await self._transcribe_audio(converted_audio_path)
            if not transcript_result.success:
                logger.error(f"Transcription failed: {transcript_result.error}")
                return
            
            # Step 5: Extract contact information
            contact_info = self._extract_contact_info(transcript_result.transcript)
            
            # Step 6: Search/create Zoho Desk ticket
            ticket = await self._handle_zoho_desk_ticket(
                transcript_result.transcript, contact_info, file_info
            )
            
            # Step 7: Post feedback to Slack (optional)
            if ticket:
                await self._post_slack_feedback(file_info, ticket)
            
            # Mark file as completed with ticket ID
            self.file_tracker.mark_file_processed(
                file_info.file_url, file_info.file_name, file_info.user_id, file_info.channel_id,
                status="completed", ticket_id=ticket.ticket_id if ticket else None
            )
            
        except Exception as e:
            logger.error(f"Error in regular audio processing: {str(e)}")
        finally:
            # Cleanup temporary files
            for file_path in [audio_file_path, converted_audio_path]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")
    
    async def _download_slack_file(self, file_info: SlackFileInfo) -> Optional[str]:
        """Download audio file from Slack"""
        try:
            headers = {
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(file_info.file_url, headers=headers) as response:
                    if response.status == 200:
                        # Create temporary file with original extension
                        temp_file = tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix=f'.{file_info.file_type}'
                        )
                        temp_file.write(await response.read())
                        temp_file.close()
                        logger.info(f"Downloaded file: {temp_file.name}")
                        return temp_file.name
                    else:
                        logger.error(f"Failed to download file: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading Slack file: {str(e)}")
            return None
    
    async def _convert_audio_if_needed(self, audio_file_path: str, file_info: SlackFileInfo) -> Optional[str]:
        """Convert audio file to MP3 if needed"""
        try:
            # Check if file is already MP3
            if audio_file_path.lower().endswith('.mp3'):
                logger.info(f"File is already MP3: {file_info.file_name}")
                return audio_file_path
            
            # Check if conversion is needed
            if not self.audio_converter.is_audio_file(audio_file_path):
                logger.warning(f"File may not be audio, attempting conversion anyway: {file_info.file_name}")
            
            # Convert to MP3
            converted_path = self.audio_converter.convert_to_mp3(audio_file_path)
            
            if converted_path and os.path.exists(converted_path):
                # Get audio duration for logging
                duration = self.audio_converter.get_audio_duration(converted_path)
                if duration:
                    logger.info(f"Audio conversion successful: {file_info.file_name} ({duration:.2f}s)")
                else:
                    logger.info(f"Audio conversion successful: {file_info.file_name}")
                return converted_path
            else:
                logger.error(f"Audio conversion failed for: {file_info.file_name}")
                # Return original file as fallback
                return audio_file_path
                
        except Exception as e:
            logger.error(f"Error in audio conversion: {str(e)}")
            # Return original file as fallback
            return audio_file_path
    
    def _extract_file_id_from_url(self, file_url: str) -> Optional[str]:
        """Extract file ID from Slack file URL"""
        try:
            # Extract file ID from URL pattern like: https://files.slack.com/files-pri/...
            import re
            match = re.search(r'/files-pri/[^/]+/([^/]+)/', file_url)
            if match:
                return match.group(1)
            
            # Alternative pattern
            match = re.search(r'/files/([^/]+)/', file_url)
            if match:
                return match.group(1)
            
            logger.warning(f"Could not extract file ID from URL: {file_url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting file ID: {str(e)}")
            return None
    
    async def _download_audio_from_url(self, audio_url: str, filename_prefix: str) -> Optional[str]:
        """Download audio file from URL"""
        try:
            headers = {
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url, headers=headers) as response:
                    if response.status == 200:
                        # Create temporary file
                        temp_file = tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix='.mp4',  # Default to MP4 for Canvas audio
                            prefix=filename_prefix
                        )
                        temp_file.write(await response.read())
                        temp_file.close()
                        logger.info(f"Downloaded audio: {temp_file.name}")
                        return temp_file.name
                    else:
                        logger.error(f"Failed to download audio: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading audio from URL: {str(e)}")
            return None
    
    async def _create_canvas_zoho_ticket(self, canvas_data: CanvasData, combined_transcript: str, contact_info: Dict[str, Optional[str]], file_info: SlackFileInfo) -> Optional[ZohoTicket]:
        """Create Zoho Desk ticket for Canvas file with embedded audio"""
        try:
            # Get OAuth access token
            access_token = await self.zoho_oauth.get_access_token()
            if not access_token:
                logger.error("No valid Zoho access token available")
                return None
            
            url = f"https://{ZOHO_DESK_DOMAIN}/api/v1/tickets"
            headers = self.zoho_oauth.get_headers()
            
            # Create comprehensive ticket description
            description = f"""Canvas File: {file_info.file_name}

Canvas Content:
{canvas_data.canvas_text[:1000]}{'...' if len(canvas_data.canvas_text) > 1000 else ''}

Audio Transcripts ({len(canvas_data.audio_links)} audio files):
{combined_transcript}

Source: Slack Canvas File
Channel: {file_info.channel_id}
User: {file_info.user_id}
Timestamp: {file_info.timestamp}
"""
            
            # Create ticket data
            ticket_data = {
                'subject': f'Canvas File with Audio - {file_info.file_name}',
                'description': description,
                'status': 'Open',
                'priority': 'Medium',
                'channel': 'Slack Canvas',
                'source': 'Canvas File with Audio'
            }
            
            # Add department if configured
            if ZOHO_DESK_DEPARTMENT_ID:
                ticket_data['departmentId'] = ZOHO_DESK_DEPARTMENT_ID
            
            # Add contact information if available
            if contact_info.get('email'):
                ticket_data['email'] = contact_info['email']
            if contact_info.get('phone'):
                ticket_data['phone'] = contact_info['phone']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=ticket_data) as response:
                    if response.status == 201:
                        result = await response.json()
                        ticket_id = result['data']['id']
                        
                        logger.info(f"Created Canvas Zoho ticket: {ticket_id}")
                        return ZohoTicket(
                            ticket_id=ticket_id,
                            subject=ticket_data['subject'],
                            status='Open',
                            priority='Medium',
                            contact_email=contact_info.get('email'),
                            contact_phone=contact_info.get('phone')
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create Canvas Zoho ticket: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error creating Canvas Zoho ticket: {str(e)}")
            return None
    
    async def _transcribe_audio(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe audio using configured service"""
        try:
            if TRANSCRIPTION_PROVIDER == 'deepgram':
                return await self._transcribe_with_deepgram(audio_file_path)
            elif TRANSCRIPTION_PROVIDER == 'assemblyai':
                return await self._transcribe_with_assemblyai(audio_file_path)
            elif TRANSCRIPTION_PROVIDER == 'whisper':
                return await self._transcribe_with_whisper(audio_file_path)
            else:
                return TranscriptionResult(
                    success=False,
                    error=f"Unsupported transcription provider: {TRANSCRIPTION_PROVIDER}"
                )
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return TranscriptionResult(success=False, error=str(e))
    
    async def _transcribe_with_deepgram(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe using Deepgram API"""
        try:
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                'Authorization': f'Token {TRANSCRIPTION_API_KEY}',
                'Content-Type': 'audio/*'
            }
            
            with open(audio_file_path, 'rb') as audio_file:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=audio_file) as response:
                        if response.status == 200:
                            result = await response.json()
                            transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                            confidence = result['results']['channels'][0]['alternatives'][0]['confidence']
                            return TranscriptionResult(
                                success=True,
                                transcript=transcript,
                                confidence=confidence
                            )
                        else:
                            error_text = await response.text()
                            return TranscriptionResult(
                                success=False,
                                error=f"Deepgram API error: {response.status} - {error_text}"
                            )
        except Exception as e:
            return TranscriptionResult(success=False, error=str(e))
    
    async def _transcribe_with_assemblyai(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe using AssemblyAI API"""
        try:
            # Upload file
            upload_url = "https://api.assemblyai.com/v2/upload"
            headers = {'authorization': TRANSCRIPTION_API_KEY}
            
            with open(audio_file_path, 'rb') as audio_file:
                async with aiohttp.ClientSession() as session:
                    async with session.post(upload_url, headers=headers, data=audio_file) as response:
                        if response.status == 200:
                            upload_result = await response.json()
                            audio_url = upload_result['upload_url']
                            
                            # Start transcription
                            transcribe_url = "https://api.assemblyai.com/v2/transcript"
                            transcribe_data = {'audio_url': audio_url}
                            
                            async with session.post(transcribe_url, headers=headers, json=transcribe_data) as transcribe_response:
                                if transcribe_response.status == 200:
                                    transcribe_result = await transcribe_response.json()
                                    transcript_id = transcribe_result['id']
                                    
                                    # Poll for completion
                                    return await self._poll_assemblyai_transcription(session, headers, transcript_id)
                                else:
                                    return TranscriptionResult(success=False, error="Failed to start transcription")
                        else:
                            return TranscriptionResult(success=False, error="Failed to upload audio")
        except Exception as e:
            return TranscriptionResult(success=False, error=str(e))
    
    async def _poll_assemblyai_transcription(self, session, headers, transcript_id) -> TranscriptionResult:
        """Poll AssemblyAI for transcription completion"""
        poll_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        
        while True:
            async with session.get(poll_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    status = result['status']
                    
                    if status == 'completed':
                        return TranscriptionResult(
                            success=True,
                            transcript=result['text'],
                            confidence=result.get('confidence', 0.0)
                        )
                    elif status == 'error':
                        return TranscriptionResult(
                            success=False,
                            error=result.get('error', 'Transcription failed')
                        )
                    else:
                        # Still processing, wait and retry
                        await asyncio.sleep(2)
                else:
                    return TranscriptionResult(success=False, error="Failed to poll transcription status")
    
    async def _transcribe_with_whisper(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe using OpenAI Whisper API"""
        try:
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}'
            }
            
            with open(audio_file_path, 'rb') as audio_file:
                data = aiohttp.FormData()
                data.add_field('file', audio_file, filename='audio.mp3')
                data.add_field('model', 'whisper-1')
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return TranscriptionResult(
                                success=True,
                                transcript=result['text']
                            )
                        else:
                            error_text = await response.text()
                            return TranscriptionResult(
                                success=False,
                                error=f"Whisper API error: {response.status} - {error_text}"
                            )
        except Exception as e:
            return TranscriptionResult(success=False, error=str(e))
    
    def _extract_contact_info(self, transcript: str) -> Dict[str, Optional[str]]:
        """Extract phone number and email from transcript"""
        contact_info = {
            'phone': None,
            'email': None
        }
        
        try:
            # Phone number patterns
            phone_patterns = [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
                r'\b\+?1?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b',  # US with country code
                r'\b\d{10}\b'  # 10 digits
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, transcript)
                if match:
                    contact_info['phone'] = match.group(0)
                    break
            
            # Email pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, transcript)
            if email_match:
                contact_info['email'] = email_match.group(0)
            
            logger.info(f"Extracted contact info: {contact_info}")
            return contact_info
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
            return contact_info
    
    async def _handle_zoho_desk_ticket(self, transcript: str, contact_info: Dict[str, Optional[str]], file_info: SlackFileInfo) -> Optional[ZohoTicket]:
        """Handle Zoho Desk ticket creation or update"""
        try:
            # Search for existing ticket
            existing_ticket = await self._search_zoho_ticket(contact_info)
            
            if existing_ticket:
                # Update existing ticket
                await self._update_zoho_ticket(existing_ticket.ticket_id, transcript, file_info)
                return existing_ticket
            else:
                # Create new ticket
                return await self._create_zoho_ticket(transcript, contact_info, file_info)
                
        except Exception as e:
            logger.error(f"Error handling Zoho Desk ticket: {str(e)}")
            return None
    
    async def _search_zoho_ticket(self, contact_info: Dict[str, Optional[str]]) -> Optional[ZohoTicket]:
        """Search for existing Zoho Desk ticket by contact info"""
        try:
            if not contact_info.get('email') and not contact_info.get('phone'):
                return None
            
            # Search by email
            if contact_info.get('email'):
                tickets = await self._search_tickets_by_email(contact_info['email'])
                if tickets:
                    return tickets[0]  # Return first match
            
            # Search by phone
            if contact_info.get('phone'):
                tickets = await self._search_tickets_by_phone(contact_info['phone'])
                if tickets:
                    return tickets[0]  # Return first match
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Zoho tickets: {str(e)}")
            return None
    
    async def _search_tickets_by_email(self, email: str) -> list:
        """Search Zoho tickets by email"""
        try:
            # Get OAuth access token
            access_token = await self.zoho_oauth.get_access_token()
            if not access_token:
                logger.error("No valid Zoho access token available")
                return []
            
            url = f"https://{ZOHO_DESK_DOMAIN}/api/v1/tickets/search"
            headers = self.zoho_oauth.get_headers()
            params = {
                'email': email,
                'limit': 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('data', [])
                    else:
                        logger.error(f"Zoho search error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching tickets by email: {str(e)}")
            return []
    
    async def _search_tickets_by_phone(self, phone: str) -> list:
        """Search Zoho tickets by phone"""
        try:
            # Get OAuth access token
            access_token = await self.zoho_oauth.get_access_token()
            if not access_token:
                logger.error("No valid Zoho access token available")
                return []
            
            url = f"https://{ZOHO_DESK_DOMAIN}/api/v1/tickets/search"
            headers = self.zoho_oauth.get_headers()
            params = {
                'phone': phone,
                'limit': 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('data', [])
                    else:
                        logger.error(f"Zoho search error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching tickets by phone: {str(e)}")
            return []
    
    async def _create_zoho_ticket(self, transcript: str, contact_info: Dict[str, Optional[str]], file_info: SlackFileInfo) -> Optional[ZohoTicket]:
        """Create new Zoho Desk ticket"""
        try:
            # Get OAuth access token
            access_token = await self.zoho_oauth.get_access_token()
            if not access_token:
                logger.error("No valid Zoho access token available")
                return None
            
            url = f"https://{ZOHO_DESK_DOMAIN}/api/v1/tickets"
            headers = self.zoho_oauth.get_headers()
            
            # Create ticket data
            ticket_data = {
                'subject': f'Voice Message from Slack - {file_info.file_name}',
                'description': f'Transcription from Slack voice message:\n\n{transcript}',
                'status': 'Open',
                'priority': 'Medium',
                'channel': 'Slack',
                'source': 'Voice Message'
            }
            
            # Add department if configured
            if ZOHO_DESK_DEPARTMENT_ID:
                ticket_data['departmentId'] = ZOHO_DESK_DEPARTMENT_ID
            
            # Add contact information if available
            if contact_info.get('email'):
                ticket_data['email'] = contact_info['email']
            if contact_info.get('phone'):
                ticket_data['phone'] = contact_info['phone']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=ticket_data) as response:
                    if response.status == 201:
                        result = await response.json()
                        ticket_id = result['data']['id']
                        
                        logger.info(f"Created Zoho ticket: {ticket_id}")
                        return ZohoTicket(
                            ticket_id=ticket_id,
                            subject=ticket_data['subject'],
                            status='Open',
                            priority='Medium',
                            contact_email=contact_info.get('email'),
                            contact_phone=contact_info.get('phone')
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create Zoho ticket: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error creating Zoho ticket: {str(e)}")
            return None
    
    async def _update_zoho_ticket(self, ticket_id: str, transcript: str, file_info: SlackFileInfo):
        """Update existing Zoho Desk ticket with transcript"""
        try:
            # Get OAuth access token
            access_token = await self.zoho_oauth.get_access_token()
            if not access_token:
                logger.error("No valid Zoho access token available")
                return
            
            # Add comment to existing ticket
            url = f"https://{ZOHO_DESK_DOMAIN}/api/v1/tickets/{ticket_id}/comments"
            headers = self.zoho_oauth.get_headers()
            
            comment_data = {
                'content': f'New voice message transcription from Slack:\n\n{transcript}',
                'isPublic': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=comment_data) as response:
                    if response.status == 201:
                        logger.info(f"Updated Zoho ticket {ticket_id} with transcript")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update ticket: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error updating Zoho ticket: {str(e)}")
    
    async def _post_slack_feedback(self, file_info: SlackFileInfo, ticket: ZohoTicket):
        """Post feedback message to Slack thread"""
        try:
            if not SLACK_BOT_TOKEN:
                logger.warning("Slack bot token not configured, skipping feedback")
                return
            
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            message = {
                'channel': file_info.channel_id,
                'text': f'✅ Transcript posted to Zoho Desk ticket #{ticket.ticket_id}',
                'thread_ts': file_info.timestamp
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=message) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info(f"Posted Slack feedback for ticket {ticket.ticket_id}")
                        else:
                            logger.error(f"Slack API error: {result.get('error')}")
                    else:
                        logger.error(f"Failed to post Slack feedback: {response.status}")
        except Exception as e:
            logger.error(f"Error posting Slack feedback: {str(e)}")

# Initialize processor
processor = SlackWebhookProcessor()

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'service': 'Slack Webhook Middleware',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook/slack',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'slack': bool(SLACK_BOT_TOKEN),
            'zoho': bool(ZOHO_DESK_ACCESS_TOKEN and ZOHO_DESK_REFRESH_TOKEN),
            'transcription': bool(TRANSCRIPTION_API_KEY)
        },
        'audio_processing': {
            'ffmpeg_available': bool(processor.audio_converter.ffmpeg_path),
            'conversion_support': 'mp4_to_mp3',
            'supported_formats': ['mp3', 'mp4', 'wav', 'm4a', 'aac', 'ogg', 'flac']
        },
        'canvas_processing': {
            'enabled': True,
            'supported_types': ['canvas', 'application/vnd.slack.canvas'],
            'audio_extraction': 'embedded_audio_links',
            'multi_audio_support': True
        },
        'file_tracking': {
            'database': 'active',
            'duplicate_prevention': 'enabled'
        }
    })

@app.route('/webhook/slack', methods=['POST'])
def slack_webhook():
    """Main webhook endpoint for Zapier integration"""
    try:
        # Get JSON payload
        payload = request.get_json()
        if not payload:
            return jsonify({
                'success': False,
                'error': 'No JSON payload received'
            }), 400
        
        logger.info(f"Received webhook: {json.dumps(payload, indent=2)}")
        
        # Process webhook asynchronously
        result = asyncio.run(processor.process_slack_webhook(payload))
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Check required environment variables
    required_vars = [
        'SLACK_BOT_TOKEN', 
        'ZOHO_DESK_ACCESS_TOKEN', 
        'ZOHO_DESK_REFRESH_TOKEN',
        'ZOHO_DESK_CLIENT_ID',
        'ZOHO_DESK_CLIENT_SECRET',
        'ZOHO_DESK_ORG_ID',
        'TRANSCRIPTION_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set the following environment variables:")
        for var in missing_vars:
            logger.error(f"  {var}=your_value_here")
        exit(1)
    
    logger.info("Starting Slack Webhook Middleware...")
    logger.info(f"Transcription provider: {TRANSCRIPTION_PROVIDER}")
    logger.info(f"Zoho Desk domain: {ZOHO_DESK_DOMAIN}")
    
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
