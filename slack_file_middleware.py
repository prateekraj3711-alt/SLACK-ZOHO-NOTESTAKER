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
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
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

@app.post("/webhook/slack")
async def slack_webhook(request: Request, background_tasks: BackgroundTasks):
    """Main webhook endpoint for Slack events"""
    try:
        # Parse request body
        body = await request.body()
        payload = json.loads(body)
        
        logger.info(f"Received Slack event: {payload.get('type', 'unknown')}")
        
        # Handle different event types
        event_type = payload.get('type')
        
        if event_type == 'url_verification':
            # Slack URL verification
            return {"challenge": payload.get('challenge')}
        
        elif event_type == 'event_callback':
            # Process event
            event = payload.get('event', {})
            event_subtype = event.get('type')
            
            if event_subtype == 'file_shared':
                # Handle file share event
                logger.info("Processing file_shared event")
                result = file_processor.process_file_share_event(event)
                
                if result.success:
                    logger.info(f"Successfully processed file: {result.local_path}")
                    return {
                        "success": True,
                        "message": "File processed successfully",
                        "file_path": result.local_path,
                        "file_size": result.file_size
                    }
                else:
                    logger.error(f"Failed to process file: {result.error}")
                    return {
                        "success": False,
                        "error": result.error
                    }
            
            elif event_subtype == 'message' and event.get('files'):
                # Handle message with file attachments
                logger.info("Processing message with file attachments")
                results = []
                
                for file_data in event.get('files', []):
                    file_id = file_data.get('id')
                    if file_id:
                        # Create event-like structure
                        file_event = {'file': file_data}
                        result = file_processor.process_file_share_event(file_event)
                        results.append({
                            "file_id": file_id,
                            "success": result.success,
                            "file_path": result.local_path if result.success else None,
                            "error": result.error if not result.success else None
                        })
                
                return {
                    "success": True,
                    "message": f"Processed {len(results)} files",
                    "results": results
                }
        
        # Event not handled
        logger.info(f"Unhandled event type: {event_type}")
        return {"message": "Event received but not processed"}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
