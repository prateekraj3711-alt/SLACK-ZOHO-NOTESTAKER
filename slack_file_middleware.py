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
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "xoxb-your-token")
SLACK_API_BASE = "https://slack.com/api"

# Audio file support
AUDIO_MIME_TYPES = {
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/mp4': '.mp4',
    'audio/ogg': '.ogg',
    'audio/webm': '.webm',
    'audio/m4a': '.m4a',
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

@dataclass
class FileDownloadResult:
    """Data class for file download results"""
    success: bool
    local_path: Optional[str] = None
    file_size: int = 0
    error: Optional[str] = None

class SlackFileProcessor:
    """Handles Slack file operations"""
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """Create download directory if it doesn't exist"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Created download directory: {self.download_dir}")
    
    def process_file_share_event(self, event_data: Dict[str, Any]) -> FileDownloadResult:
        """Process a file share event"""
        try:
            file_data = event_data.get('file', {})
            file_id = file_data.get('id')
            
            if not file_id:
                return FileDownloadResult(success=False, error="No file ID found")
            
            # Get file metadata
            metadata = self._get_file_metadata(file_id)
            if not metadata:
                return FileDownloadResult(success=False, error="Failed to get file metadata")
            
            # Download the file
            return self._download_file(file_id, metadata)
            
        except Exception as e:
            logger.error(f"Error processing file share event: {str(e)}")
            return FileDownloadResult(success=False, error=str(e))
    
    def _get_file_metadata(self, file_id: str) -> Optional[SlackFileMetadata]:
        """Get file metadata from Slack API"""
        try:
            headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
            response = requests.get(f"{SLACK_API_BASE}/files.info?file={file_id}", headers=headers)
            
            if response.ok:
                data = response.json()
                if data.get("ok"):
                    file_info = data.get("file", {})
                    return SlackFileMetadata(
                        file_id=file_info.get("id", ""),
                        name=file_info.get("name", ""),
                        title=file_info.get("title", ""),
                        mimetype=file_info.get("mimetype", "")
                    )
            
            logger.error(f"Failed to get file metadata: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None
    
    def _download_file(self, file_id: str, metadata: SlackFileMetadata) -> FileDownloadResult:
        """Download file from Slack"""
        try:
            # Get download URL
            headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
            response = requests.get(f"{SLACK_API_BASE}/files.info?file={file_id}", headers=headers)
            
            if not response.ok:
                return FileDownloadResult(success=False, error=f"API error: {response.status_code}")
            
            data = response.json()
            if not data.get("ok"):
                return FileDownloadResult(success=False, error=f"API error: {data.get('error')}")
            
            file_info = data.get("file", {})
            download_url = file_info.get("url_private_download")
            
            if not download_url:
                return FileDownloadResult(success=False, error="No download URL found")
            
            # Create local file path
            file_extension = os.path.splitext(metadata.name)[1] or '.mp4'
            local_path = os.path.join(self.download_dir, f"{file_id}{file_extension}")
            
            # Download the file
            download_response = requests.get(download_url, headers=headers, stream=True)
            if download_response.ok:
                with open(local_path, "wb") as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(local_path)
                logger.info(f"Downloaded file: {local_path} ({file_size} bytes)")
                
                return FileDownloadResult(
                    success=True,
                    local_path=local_path,
                    file_size=file_size
                )
            else:
                return FileDownloadResult(success=False, error=f"Download failed: {download_response.status_code}")
                
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return FileDownloadResult(success=False, error=str(e))

# Initialize FastAPI app
app = FastAPI(title="Slack File Middleware", version="1.0.0")

# Initialize file processor
file_processor = SlackFileProcessor()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Slack File Middleware API",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/slack",
            "health": "/health",
            "files": "/files",
            "debug": "/debug/webhook"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "slack_api": "connected",
            "file_processor": "active"
        },
        "audio_support": {
            "mime_types": list(AUDIO_MIME_TYPES.keys()),
            "extensions": AUDIO_EXTENSIONS
        },
        "download_directory": file_processor.download_dir
    }

@app.post("/debug/webhook")
async def debug_webhook(request: Request):
    """Debug endpoint to inspect webhook requests"""
    try:
        # Get all headers
        headers = dict(request.headers)
        
        # Get content type
        content_type = request.headers.get("content-type", "")
        
        # Try to get body
        body = await request.body()
        
        # Try to parse as JSON
        json_payload = None
        try:
            json_payload = json.loads(body.decode('utf-8'))
        except:
            pass
        
        # Try to parse as form data
        form_payload = None
        try:
            form_data = await request.form()
            form_payload = dict(form_data)
        except:
            pass
        
        return {
            "content_type": content_type,
            "headers": headers,
            "body_raw": body.decode('utf-8', errors='ignore'),
            "body_length": len(body),
            "json_payload": json_payload,
            "form_payload": form_payload,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
            # Handle JSON payloads - but also check if it's actually form data
            try:
                payload = await request.json()
                logger.info("Parsed JSON payload successfully")
            except Exception as json_error:
                # If JSON parsing fails, try form data (Zapier sometimes sends form data with JSON content-type)
                logger.warning(f"JSON parsing failed: {json_error}, trying form data")
                try:
                    form_data = await request.form()
                    payload = dict(form_data)
                    logger.info("Parsed as form data despite JSON content-type")
                except Exception as form_error:
                    logger.error(f"Both JSON and form parsing failed: JSON={json_error}, Form={form_error}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request format - could not parse as JSON or form data"}
                    )
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
        elif "multipart/form-data" in content_type:
            # Handle multipart form data
            form_data = await request.form()
            payload = dict(form_data)
            logger.info("Parsed multipart form data successfully")
        elif "text/plain" in content_type:
            # Handle plain text (try to parse as JSON)
            try:
                body = await request.body()
                payload = json.loads(body.decode('utf-8'))
                logger.info("Parsed plain text as JSON successfully")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse plain text as JSON: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON format in plain text"}
                )
        else:
            # Try to parse as JSON anyway (fallback for unknown content types)
            try:
                body = await request.body()
                payload = json.loads(body.decode('utf-8'))
                logger.info(f"Parsed payload as JSON (fallback for content-type: {content_type})")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse request body as JSON: {e}")
                # Try form data as last resort
                try:
                    form_data = await request.form()
                    payload = dict(form_data)
                    logger.info("Parsed as form data (last resort)")
                except Exception as form_error:
                    logger.error(f"Failed to parse as form data: {form_error}")
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Invalid request format",
                            "content_type": content_type,
                            "supported_types": ["application/json", "application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]
                        }
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

async def process_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process webhook payload with unified Canvas and audio file handling"""
    try:
        logger.info(f"Processing webhook payload: {json.dumps(payload, indent=2)}")
        
        # Extract key information with validation (handle both direct fields and nested event structure)
        file_type = payload.get("file_type")
        file_id = payload.get("file_id")
        slack_token = payload.get("slack_token", SLACK_BOT_TOKEN)
        
        # Handle nested event structure from Slack
        if not file_type and payload.get("event"):
            event = payload.get("event", {})
            file_data = event.get("file", {})
            file_type = file_data.get("filetype", "")
            file_id = file_data.get("id", "")
            slack_token = payload.get("token", SLACK_BOT_TOKEN)
        
        # Handle Zapier field mapping
        if not file_type:
            file_type = payload.get("filetype", "")
        if not file_id:
            file_id = payload.get("id", "")
        if not slack_token or slack_token == SLACK_BOT_TOKEN:
            slack_token = payload.get("token", SLACK_BOT_TOKEN)
        
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

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download specific file by ID"""
    try:
        # Get file metadata
        metadata = file_processor._get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if file exists locally
        file_extension = os.path.splitext(metadata.name)[1] or '.mp4'
        local_path = os.path.join(file_processor.download_dir, f"{file_id}{file_extension}")
        
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="File not found locally")
        
        return {
            "file_id": file_id,
            "name": metadata.name,
            "local_path": local_path,
            "size": os.path.getsize(local_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files():
    """List all downloaded files"""
    try:
        files = []
        if os.path.exists(file_processor.download_dir):
            for filename in os.listdir(file_processor.download_dir):
                file_path = os.path.join(file_processor.download_dir, filename)
                if os.path.isfile(file_path):
                    files.append({
                        "name": filename,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        
        return {
            "files": files,
            "count": len(files),
            "directory": file_processor.download_dir
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def get_file(filename: str):
    """Get specific file information"""
    try:
        file_path = os.path.join(file_processor.download_dir, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "name": filename,
            "path": file_path,
            "size": os.path.getsize(file_path),
            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file: {str(e)}")
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
    if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN == "xoxb-your-token":
        logger.warning("SLACK_BOT_TOKEN not set or using default value")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
