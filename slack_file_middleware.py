#!/usr/bin/env python3
"""
FastAPI Middleware for Slack File Share Events
Handles audio file downloads and processing from Slack channels/threads
"""

import os
import json
import logging
import requests
import tempfile
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, APIRouter, Form
from fastapi.responses import JSONResponse
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
TRANSCRIPTION_API_KEY = os.getenv('TRANSCRIPTION_API_KEY')
TRANSCRIPTION_PROVIDER = os.getenv('TRANSCRIPTION_PROVIDER', 'whisper')

# Slack API configuration
SLACK_API_BASE = "https://slack.com/api"

# Audio file validation
AUDIO_MIME_TYPES = {
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/m4a': '.m4a',
    'audio/ogg': '.ogg',
    'audio/webm': '.webm',
    'audio/mp4': '.mp4',
    'audio/aac': '.aac',
    'audio/flac': '.flac'
}

AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.mp4', '.aac', '.flac']

# Canvas-specific functions
def get_canvas_info(canvas_id: str, token: str) -> Optional[Dict[str, Any]]:
    """Get Canvas information from Slack API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{SLACK_API_BASE}/canvas.info?canvas_id={canvas_id}", headers=headers)
        if resp.ok:
            return resp.json()
        else:
            logger.error(f"Canvas info failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching Canvas info: {str(e)}")
        return None

def get_file_info(file_id: str, slack_token: str) -> Optional[Dict[str, Any]]:
    """Defensive files.info wrapper with comprehensive error handling"""
    try:
        headers = {"Authorization": f"Bearer {slack_token}"}
        response = requests.get(f"https://slack.com/api/files.info?file={file_id}", headers=headers, timeout=30)

        if not response.ok:
            logger.error(f"Slack API error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            logger.error(f"Slack API returned failure: {error} - {data}")
            
            # Handle specific Slack API errors
            if error == "invalid_auth":
                logger.error("Invalid authentication token")
            elif error == "file_not_found":
                logger.error(f"File not found: {file_id}")
            elif error == "not_authed":
                logger.error("Not authenticated - check bot token permissions")
            elif error == "account_inactive":
                logger.error("Slack account is inactive")
            elif error == "token_revoked":
                logger.error("Slack token has been revoked")
            
            return None

        file_info = data.get("file", {})
        logger.info(f"Extracted file info keys: {list(file_info.keys())}")
        logger.info(f"File info: id={file_info.get('id')}, name={file_info.get('name')}, mimetype={file_info.get('mimetype')}")
        return file_info
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching file info for {file_id}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching file info for {file_id}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching file info: {str(e)}")
        return None

def extract_audio_links(canvas_json: Dict[str, Any]) -> List[str]:
    """Extract audio links from Canvas block structure"""
    audio_links = []
    blocks = canvas_json.get("canvas", {}).get("blocks", [])
    
    for block in blocks:
        if block.get("type") == "file":
            file = block.get("file", {})
            url = file.get("url_private_download", "")
            if url.endswith((".mp3", ".m4a", ".wav", ".mp4", ".ogg", ".webm")):
                audio_links.append(url)
                logger.info(f"Found audio file in Canvas: {url}")
        elif block.get("type") == "rich_text":
            for el in block.get("elements", []):
                if el.get("type") == "link" and el.get("url", "").endswith((".mp3", ".m4a", ".wav", ".mp4", ".ogg", ".webm")):
                    audio_links.append(el["url"])
                    logger.info(f"Found audio link in Canvas: {el['url']}")
    
    logger.info(f"Extracted {len(audio_links)} audio links from Canvas")
    return audio_links

def download_audio(url: str, token: str, save_path: str) -> Optional[str]:
    """Download audio file securely with bot token"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        if resp.ok:
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info(f"Audio saved to {save_path}")
            return save_path
        else:
            logger.error(f"Audio download failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        return None

@dataclass
class SlackFileMetadata:
    """Data class for Slack file metadata"""
    file_id: str
    name: str
    title: str
    mimetype: str
    size: int
    url_private_download: str
    user_id: str
    channel_id: str
    timestamp: str
    permalink: Optional[str] = None
    is_audio: bool = False
    local_path: Optional[str] = None

@dataclass
class FileDownloadResult:
    """Result of file download operation"""
    success: bool
    file_metadata: Optional[SlackFileMetadata] = None
    local_path: Optional[str] = None
    error: Optional[str] = None
    file_size: int = 0

class SlackFileProcessor:
    """Main processor for Slack file share events"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.download_dir = os.getenv('SLACK_DOWNLOAD_DIR', 'downloads')
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """Create download directory if it doesn't exist"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Created download directory: {self.download_dir}")
    
    def validate_slack_token(self) -> bool:
        """Validate Slack bot token"""
        if not SLACK_BOT_TOKEN:
            logger.error("SLACK_BOT_TOKEN not configured")
            return False
        return True
    
    def is_audio_file(self, mimetype: str, filename: str = None) -> bool:
        """Check if file is an audio file based on MIME type and extension"""
        # Check MIME type
        if mimetype in AUDIO_MIME_TYPES:
            return True
        
        # Check file extension as fallback
        if filename:
            file_ext = os.path.splitext(filename)[1].lower()
            return file_ext in AUDIO_EXTENSIONS
        
        return False
    
    def get_file_extension(self, mimetype: str, filename: str = None) -> str:
        """Get appropriate file extension for audio file"""
        if mimetype in AUDIO_MIME_TYPES:
            return AUDIO_MIME_TYPES[mimetype]
        
        if filename:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in AUDIO_EXTENSIONS:
                return file_ext
        
        return '.mp4'  # Default fallback
    
    def get_slack_file_metadata(self, file_id: str) -> Optional[SlackFileMetadata]:
        """Get file metadata from Slack API"""
        try:
            if not self.validate_slack_token():
                return None
            
            url = "https://slack.com/api/files.info"
            headers = {
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
                'Content-Type': 'application/json'
            }
            params = {'file': file_id}
            
            logger.info(f"Fetching metadata for file: {file_id}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if not response.ok:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            if not data.get('ok'):
                logger.error(f"Slack API error: {data.get('error', 'Unknown error')}")
                return None
            
            file_data = data.get('file', {})
            
            # Extract metadata
            metadata = SlackFileMetadata(
                file_id=file_id,
                name=file_data.get('name', 'unknown'),
                title=file_data.get('title', ''),
                mimetype=file_data.get('mimetype', ''),
                size=file_data.get('size', 0),
                url_private_download=file_data.get('url_private_download', ''),
                user_id=file_data.get('user', ''),
                channel_id=file_data.get('channels', [''])[0] if file_data.get('channels') else '',
                timestamp=file_data.get('timestamp', str(datetime.now().timestamp())),
                permalink=file_data.get('permalink', ''),
                is_audio=self.is_audio_file(file_data.get('mimetype', ''), file_data.get('name', ''))
            )
            
            logger.info(f"File metadata: {metadata.name} ({metadata.mimetype}) - Audio: {metadata.is_audio}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching file metadata: {str(e)}")
            return None
    
    def download_audio_file(self, metadata: SlackFileMetadata) -> FileDownloadResult:
        """Download audio file from Slack"""
        try:
            if not metadata.url_private_download:
                return FileDownloadResult(
                    success=False,
                    error="No download URL available"
                )
            
            if not metadata.is_audio:
                return FileDownloadResult(
                    success=False,
                    error=f"File is not audio type: {metadata.mimetype}"
                )
            
            # Create meaningful filename
            file_ext = self.get_file_extension(metadata.mimetype, metadata.name)
            safe_name = self._sanitize_filename(metadata.name)
            filename = f"audio_{metadata.file_id}_{safe_name}{file_ext}"
            local_path = os.path.join(self.download_dir, filename)
            
            logger.info(f"Downloading audio file: {metadata.name} -> {filename}")
            
            # Download file with authentication
            headers = {
                'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
            }
            
            response = requests.get(
                metadata.url_private_download,
                headers=headers,
                stream=True,
                timeout=60
            )
            
            if not response.ok:
                return FileDownloadResult(
                    success=False,
                    error=f"Download failed: {response.status_code} - {response.text}"
                )
            
            # Save file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(local_path)
            logger.info(f"Downloaded file: {local_path} ({file_size} bytes)")
            
            # Update metadata with local path
            metadata.local_path = local_path
            
            return FileDownloadResult(
                success=True,
                file_metadata=metadata,
                local_path=local_path,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return FileDownloadResult(
                success=False,
                error=str(e)
            )
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        return safe_name
    
    def process_file_share_event(self, event_data: Dict[str, Any]) -> FileDownloadResult:
        """Process Slack file share event"""
        try:
            # Extract file ID from event
            file_id = None
            
            # Handle different event types
            if 'file' in event_data:
                file_id = event_data['file'].get('id')
            elif 'file_id' in event_data:
                file_id = event_data['file_id']
            elif 'files' in event_data and event_data['files']:
                file_id = event_data['files'][0].get('id')
            
            if not file_id:
                return FileDownloadResult(
                    success=False,
                    error="No file ID found in event data"
                )
            
            # Get file metadata
            metadata = self.get_slack_file_metadata(file_id)
            if not metadata:
                return FileDownloadResult(
                    success=False,
                    error="Failed to get file metadata"
                )
            
            # Download audio file
            return self.download_audio_file(metadata)
            
        except Exception as e:
            logger.error(f"Error processing file share event: {str(e)}")
            return FileDownloadResult(
                success=False,
                error=str(e)
            )

# Initialize processor
file_processor = SlackFileProcessor()

# FastAPI app
app = FastAPI(
    title="Slack File Share Middleware",
    description="Handles Slack file share events and audio file processing",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Slack File Share Middleware",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/slack",
            "health": "/health",
            "download": "/download/{file_id}"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "slack_token": bool(SLACK_BOT_TOKEN),
            "transcription": bool(TRANSCRIPTION_API_KEY)
        },
        "audio_support": {
            "mime_types": list(AUDIO_MIME_TYPES.keys()),
            "extensions": AUDIO_EXTENSIONS
        },
        "download_directory": file_processor.download_dir
    }

async def process_canvas_file(canvas_id: str, slack_token: str) -> Dict[str, Any]:
    """Process Canvas file and extract audio files"""
    try:
        logger.info(f"Processing Canvas file: {canvas_id}")
        
        # Get Canvas information using canvas.info API
        canvas_json = get_canvas_info(canvas_id, slack_token)
        if not canvas_json:
            logger.error("Canvas fetch failed")
            return {
                "status": "canvas fetch failed", 
                "error": "Could not retrieve Canvas information"
            }
        
        # Extract audio links from Canvas block structure
        audio_links = extract_audio_links(canvas_json)
        if not audio_links:
            logger.info("No audio links found in Canvas")
            return {
                "status": "no audio found", 
                "message": "Canvas contains no audio files"
            }
        
        logger.info(f"Found {len(audio_links)} audio links in Canvas")
        
        # Download each audio file
        downloaded_files = []
        for i, url in enumerate(audio_links):
            # Create unique filename
            file_extension = os.path.splitext(url.split('/')[-1])[1] or '.m4a'
            save_path = os.path.join(
                file_processor.download_dir, 
                f"audio_{canvas_id}_{i}{file_extension}"
            )
            
            # Download audio file with bot token authentication
            result_path = download_audio(url, slack_token, save_path)
            if result_path:
                file_size = os.path.getsize(result_path) if os.path.exists(result_path) else 0
                downloaded_files.append({
                    "index": i,
                    "url": url,
                    "local_path": result_path,
                    "file_size": file_size
                })
                logger.info(f"Downloaded audio {i+1}/{len(audio_links)}: {result_path}")
            else:
                logger.error(f"Failed to download audio {i+1}/{len(audio_links)}: {url}")
        
        if downloaded_files:
            logger.info(f"Successfully downloaded {len(downloaded_files)} audio files from Canvas")
            return {
                "status": "audio extracted",
                "canvas_id": canvas_id,
                "audio_count": len(audio_links),
                "downloaded_count": len(downloaded_files),
                "files": downloaded_files
            }
        else:
            logger.error("Failed to download any audio files from Canvas")
            return {
                "status": "download failed",
                "error": "Could not download any audio files from Canvas"
            }
            
    except Exception as e:
        logger.error(f"Error processing Canvas file: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def process_audio_file(file_id: str, slack_token: str) -> Dict[str, Any]:
    """Process regular audio file"""
    try:
        logger.info(f"Processing regular audio file: {file_id}")
        
        # Get file info with defensive wrapper
        file_info = get_file_info(file_id, slack_token)
        if not file_info:
            logger.error("Failed to fetch file info")
            return {"status": "error", "error": "Failed to fetch file info"}
        
        # Extract download URL
        file_url = file_info.get("url_private_download")
        if not file_url:
            logger.error("Missing url_private_download in file_info")
            return {"status": "error", "error": "No downloadable URL found"}
        
        # Download the file
        file_name = file_info.get("name", "unknown")
        file_extension = os.path.splitext(file_name)[1] or '.mp4'
        save_path = os.path.join(
            file_processor.download_dir,
            f"audio_{file_id}_{file_name}"
        )
        
        result_path = download_audio(file_url, slack_token, save_path)
        if result_path:
            file_size = os.path.getsize(result_path) if os.path.exists(result_path) else 0
            logger.info(f"Successfully processed regular file: {result_path}")
            return {
                "status": "file processed",
                "file_id": file_id,
                "file_path": result_path,
                "file_size": file_size,
                "file_name": file_name
            }
        else:
            logger.error(f"Failed to download regular file: {file_url}")
            return {
                "status": "download failed",
                "error": "Could not download file"
            }
            
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/webhook/slack")
async def slack_webhook(request: Request):
    """Unified webhook endpoint supporting both JSON and form-encoded payloads"""
    try:
        # Get content type and log it
        content_type = request.headers.get("content-type", "").lower()
        logger.info(f"Received webhook request with content-type: {content_type}")
        
        # Auto-detect content type and parse accordingly
        if "application/json" in content_type:
            # Handle JSON payloads
            payload = await request.json()
            logger.info("Parsed JSON payload successfully")
        elif "application/x-www-form-urlencoded" in content_type:
            # Handle form-encoded payloads (Zapier compatibility)
            form_data = await request.form()
            payload = dict(form_data)
            logger.info("Parsed form-encoded payload successfully")
            
            # Try to parse JSON from form data if it exists
            if "payload" in payload:
                try:
                    parsed_payload = json.loads(payload["payload"])
                    payload.update(parsed_payload)
                    logger.info("Merged JSON payload from form data")
                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON from form payload field")
        else:
            # Try to parse as JSON anyway (fallback)
            try:
                body = await request.body()
                payload = json.loads(body.decode('utf-8'))
                logger.info("Parsed payload as JSON (fallback)")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse request body: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request format - expected JSON or form data"}
                )
        
        logger.info(f"Processing webhook payload: {json.dumps(payload, indent=2)}")
        
        # Handle Slack event callbacks (for direct Slack webhooks)
        if payload.get('type') == 'event_callback':
            event = payload.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'file_shared':
                file_data = event.get('file', {})
                file_id = file_data.get('id')
                file_type = file_data.get('filetype', '')
                
                logger.info(f"Processing Slack file_shared event: {file_id} (type: {file_type})")
                
                # Create payload for processing
                processing_payload = {
                    "file_type": file_type,
                    "file_id": file_id,
                    "slack_token": SLACK_BOT_TOKEN
                }
                
                return await process_webhook_payload(processing_payload)
        
        # Handle URL verification
        elif payload.get('type') == 'url_verification':
            logger.info("Handling Slack URL verification")
            return {"challenge": payload.get('challenge')}
        
        # Process other payloads (Zapier, direct API calls)
        else:
            return await process_webhook_payload(payload)
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download specific file by ID"""
    try:
        # Get file metadata
        metadata = file_processor.get_slack_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Download file
        result = file_processor.download_audio_file(metadata)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)
        
        return {
            "success": True,
            "file_metadata": {
                "file_id": metadata.file_id,
                "name": metadata.name,
                "mimetype": metadata.mimetype,
                "size": metadata.size,
                "is_audio": metadata.is_audio
            },
            "local_path": result.local_path,
            "file_size": result.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_downloaded_files():
    """List all downloaded files"""
    try:
        files = []
        if os.path.exists(file_processor.download_dir):
            for filename in os.listdir(file_processor.download_dir):
                file_path = os.path.join(file_processor.download_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        "filename": filename,
                        "path": file_path,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a downloaded file"""
    try:
        file_path = os.path.join(file_processor.download_dir, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        logger.info(f"Deleted file: {file_path}")
        
        return {"success": True, "message": f"File {filename} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process webhook payload with unified Canvas and audio file handling"""
    try:
        logger.info(f"Processing webhook payload: {json.dumps(payload, indent=2)}")
        
        # Extract key information with validation
        file_type = payload.get("file_type")
        file_id = payload.get("file_id")
        slack_token = payload.get("slack_token", SLACK_BOT_TOKEN)
        
        # Validate required fields
        if not file_type:
            logger.error("Missing file_type in payload")
            return {"status": "error", "error": "Missing required field: file_type"}
        
        if not file_id:
            logger.error("Missing file_id in payload")
            return {"status": "error", "error": "Missing required field: file_id"}
        
        if not slack_token:
            logger.error("Missing slack_token in payload")
            return {"status": "error", "error": "Missing required field: slack_token"}
        
        logger.info(f"Processing {file_type} file: {file_id}")
        
        # Handle Canvas files (quip type)
        if file_type == "quip":
            return await process_canvas_file(file_id, slack_token)
        
        # Handle regular audio files
        elif file_type in ["mp3", "mp4", "wav", "m4a", "ogg", "webm"]:
            return await process_audio_file(file_id, slack_token)
        
        # Unhandled event type
        else:
            logger.info(f"Non-Canvas file or unhandled event received: {file_type}")
            return {
                "status": "ignored",
                "message": f"File type '{file_type}' not supported or no processing needed"
            }
        
    except Exception as e:
        logger.error(f"Error processing webhook payload: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    # Check required environment variables
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN environment variable is required")
        exit(1)
    
    logger.info("Starting Slack File Share Middleware...")
    logger.info(f"Download directory: {file_processor.download_dir}")
    logger.info(f"Supported audio types: {list(AUDIO_MIME_TYPES.keys())}")
    
    uvicorn.run(
        "slack_file_middleware:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        reload=False
    )
