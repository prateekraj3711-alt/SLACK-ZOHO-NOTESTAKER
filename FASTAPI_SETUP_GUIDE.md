# FastAPI Slack File Share Middleware Setup Guide

This guide explains how to set up and use the FastAPI middleware for handling Slack file share events with automatic audio file processing.

## Overview

The FastAPI middleware provides a robust solution for:
- **Listening to Slack file share events** (`file_shared`, `message.file_share`)
- **Automatic audio file detection** and validation
- **Secure file downloads** using OAuth tokens
- **Local file storage** with meaningful naming
- **RESTful API endpoints** for file management
- **Integration with existing workflows**

## Features

### 🎵 **Audio File Processing**
- **MIME Type Validation**: Supports `audio/mpeg`, `audio/wav`, `audio/m4a`, `audio/ogg`, `audio/webm`, `audio/mp4`, `audio/aac`, `audio/flac`
- **Extension Detection**: Fallback validation using file extensions
- **Secure Downloads**: Uses Slack OAuth tokens for protected file access
- **Smart Naming**: Creates meaningful filenames like `audio_<file_id>_<original_name>.mp3`

### 🔧 **API Endpoints**
- `GET /` - Service information
- `GET /health` - Health check with service status
- `POST /webhook/slack` - Main Slack webhook endpoint
- `GET /download/{file_id}` - Download specific file by ID
- `GET /files` - List all downloaded files
- `DELETE /files/{filename}` - Delete downloaded file

### 🛡️ **Security & Validation**
- **Token Validation**: Validates Slack bot tokens before API calls
- **URL Validation**: Ensures all URLs are valid before processing
- **File Type Checking**: Validates audio files before download
- **Error Handling**: Comprehensive error handling with detailed logging

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements_fastapi.txt
```

### 2. Environment Variables
Create a `.env` file:
```env
# Required
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Optional
TRANSCRIPTION_API_KEY=your-transcription-api-key
TRANSCRIPTION_PROVIDER=whisper
SLACK_DOWNLOAD_DIR=downloads
PORT=8000
```

### 3. Slack App Configuration

#### Required OAuth Scopes
```
files:read          # Read files shared in channels
channels:history    # Access channel messages
links:read          # Read shared links
```

#### Event Subscriptions
Configure your Slack app to send these events:
- `file_shared` - When files are shared
- `message.channels` - Messages in channels (for file attachments)

#### Webhook URL
Set your webhook URL to: `https://your-domain.com/webhook/slack`

## Usage

### 1. Start the Server
```bash
python slack_file_middleware.py
```

### 2. Test the Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "services": {
    "slack_token": true,
    "transcription": true
  },
  "audio_support": {
    "mime_types": ["audio/mpeg", "audio/wav", ...],
    "extensions": [".mp3", ".wav", ".m4a", ...]
  },
  "download_directory": "downloads"
}
```

### 3. Test File Download
```bash
curl http://localhost:8000/download/F1234567890
```

## API Reference

### Webhook Endpoint
**POST** `/webhook/slack`

Handles Slack file share events automatically.

**Event Types Supported:**
- `file_shared` - Direct file shares
- `message` with `files` - Messages with file attachments

**Response:**
```json
{
  "success": true,
  "message": "File processed successfully",
  "file_path": "/path/to/downloaded/file.mp3",
  "file_size": 1024000
}
```

### Download Endpoint
**GET** `/download/{file_id}`

Download a specific file by Slack file ID.

**Parameters:**
- `file_id` (string): Slack file ID

**Response:**
```json
{
  "success": true,
  "file_metadata": {
    "file_id": "F1234567890",
    "name": "audio_recording.mp3",
    "mimetype": "audio/mpeg",
    "size": 1024000,
    "is_audio": true
  },
  "local_path": "/downloads/audio_F1234567890_audio_recording.mp3",
  "file_size": 1024000
}
```

### File Management
**GET** `/files` - List all downloaded files
**DELETE** `/files/{filename}` - Delete a specific file

## Integration Examples

### 1. Basic File Processing
```python
import requests

# Process a Slack file
response = requests.post(
    "http://localhost:8000/webhook/slack",
    json={
        "type": "event_callback",
        "event": {
            "type": "file_shared",
            "file": {
                "id": "F1234567890",
                "name": "meeting_audio.mp3",
                "mimetype": "audio/mpeg"
            }
        }
    }
)

result = response.json()
if result["success"]:
    print(f"File downloaded: {result['file_path']}")
```

### 2. Direct File Download
```python
import requests

# Download specific file
response = requests.get("http://localhost:8000/download/F1234567890")
result = response.json()

if result["success"]:
    print(f"Downloaded: {result['local_path']}")
    print(f"File size: {result['file_size']} bytes")
```

### 3. List Downloaded Files
```python
import requests

# Get list of files
response = requests.get("http://localhost:8000/files")
files = response.json()["files"]

for file_info in files:
    print(f"File: {file_info['filename']} ({file_info['size']} bytes)")
```

## Error Handling

### Common Error Responses

#### Invalid File ID
```json
{
  "detail": "File not found"
}
```

#### Non-Audio File
```json
{
  "success": false,
  "error": "File is not audio type: image/jpeg"
}
```

#### Download Failure
```json
{
  "success": false,
  "error": "Download failed: 403 - Forbidden"
}
```

### Logging

The middleware provides detailed logging:
```
INFO: Received Slack event: file_shared
INFO: Fetching metadata for file: F1234567890
INFO: File metadata: meeting_audio.mp3 (audio/mpeg) - Audio: True
INFO: Downloading audio file: meeting_audio.mp3 -> audio_F1234567890_meeting_audio.mp3
INFO: Downloaded file: /downloads/audio_F1234567890_meeting_audio.mp3 (1024000 bytes)
```

## Advanced Configuration

### Custom Download Directory
```env
SLACK_DOWNLOAD_DIR=/custom/path/to/downloads
```

### Custom Port
```env
PORT=9000
```

### Transcription Integration
```python
# Add to your environment
TRANSCRIPTION_API_KEY=your-openai-api-key
TRANSCRIPTION_PROVIDER=whisper
```

## Security Considerations

### 1. Token Security
- Store `SLACK_BOT_TOKEN` securely
- Use environment variables, not hardcoded values
- Rotate tokens regularly

### 2. File Access
- Downloaded files are stored locally
- Implement proper file permissions
- Consider encryption for sensitive files

### 3. API Security
- Use HTTPS in production
- Implement rate limiting
- Validate all incoming requests

## Troubleshooting

### Common Issues

#### 1. "SLACK_BOT_TOKEN not configured"
**Solution**: Set the `SLACK_BOT_TOKEN` environment variable

#### 2. "Download failed: 403 - Forbidden"
**Solution**: Check bot permissions and token validity

#### 3. "File is not audio type"
**Solution**: Verify file MIME type is in supported audio types

#### 4. "No file ID found in event data"
**Solution**: Check Slack event payload structure

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

### 1. Using Gunicorn
```bash
pip install gunicorn
gunicorn slack_file_middleware:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 2. Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_fastapi.txt .
RUN pip install -r requirements_fastapi.txt

COPY slack_file_middleware.py .
EXPOSE 8000

CMD ["python", "slack_file_middleware.py"]
```

### 3. Environment Variables
```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
SLACK_DOWNLOAD_DIR=/app/downloads
PORT=8000
```

## Integration with Existing Systems

### Zapier Integration
The middleware can be integrated with Zapier:
1. Use Zapier's HTTP request action
2. Point to your middleware webhook URL
3. Process the response for downstream actions

### Zoho Desk Integration
```python
# Example: Process downloaded file and create ticket
def process_audio_for_zoho(file_path):
    # Transcribe audio
    transcript = transcribe_audio(file_path)
    
    # Create Zoho Desk ticket
    create_zoho_ticket(transcript, file_path)
```

This FastAPI middleware provides a robust, scalable solution for handling Slack file share events with comprehensive audio file processing capabilities.
