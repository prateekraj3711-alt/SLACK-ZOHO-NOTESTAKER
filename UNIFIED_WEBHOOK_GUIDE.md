# Unified Webhook Guide

This guide explains the unified `/webhook/slack` endpoint that supports both JSON and form-encoded payloads for maximum compatibility with Zapier and direct API calls.

## Overview

The unified webhook endpoint automatically detects the incoming content type and processes both JSON and form-encoded requests through a single, modular interface.

## Key Features

### 🔄 **Unified Content Type Support**
- ✅ **JSON requests** (`application/json`)
- ✅ **Form-encoded requests** (`application/x-www-form-urlencoded`)
- ✅ **Automatic detection** of content type
- ✅ **Fallback parsing** for unknown types

### 🎯 **Modular Processing**
- ✅ **Canvas processing** (`file_type: "quip"`)
- ✅ **Audio file processing** (mp3, mp4, wav, etc.)
- ✅ **Slack event callbacks** (direct Slack webhooks)
- ✅ **URL verification** (Slack app setup)

### 🛡️ **Robust Error Handling**
- ✅ **Field validation** with clear error messages
- ✅ **Defensive API calls** with timeout protection
- ✅ **Comprehensive logging** for debugging
- ✅ **Graceful failure** handling

## Endpoint Details

### **Single Endpoint**
```
POST /webhook/slack
```

### **Supported Content Types**
- `application/json` - Standard JSON requests
- `application/x-www-form-urlencoded` - Form-encoded requests (Zapier)
- `text/plain` - Raw text requests (fallback)
- `text/json` - Alternative JSON content type

## Request Formats

### **JSON Format**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

### **Form Format**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_type=mp3&file_id=F1234567890&slack_token=xoxb-your-token"
```

## Required Fields

### **Core Fields**
- `file_type` - Type of file (e.g., "quip", "mp3", "wav", "mp4")
- `file_id` - Slack file ID
- `slack_token` - Bot token for authenticated API calls

### **Field Validation**
```python
# Validate required fields
if not file_type:
    return {"status": "error", "error": "Missing required field: file_type"}

if not file_id:
    return {"status": "error", "error": "Missing required field: file_id"}

if not slack_token:
    return {"status": "error", "error": "Missing required field: slack_token"}
```

## Processing Logic

### **Content Type Detection**
```python
content_type = request.headers.get("content-type", "").lower()

if "application/json" in content_type:
    payload = await request.json()
elif "application/x-www-form-urlencoded" in content_type:
    form_data = await request.form()
    payload = dict(form_data)
else:
    # Fallback to JSON parsing
    body = await request.body()
    payload = json.loads(body.decode('utf-8'))
```

### **File Type Routing**
```python
if file_type == "quip":
    # Canvas processing
    return await process_canvas_file(file_id, slack_token)
elif file_type in ["mp3", "mp4", "wav", "m4a", "ogg", "webm"]:
    # Audio file processing
    return await process_audio_file(file_id, slack_token)
```

## Canvas Processing

### **Canvas File Flow**
```
Canvas File (file_type: "quip")
    ↓
Call canvas.info API with file_id as canvas_id
    ↓
Parse Canvas block structure
    ↓
Extract audio links from file and rich_text blocks
    ↓
Download each audio file with bot token
    ↓
Save with unique naming: audio_<file_id>_<index>.ext
    ↓
Return processing results
```

### **Canvas Response**
```json
{
  "status": "audio extracted",
  "canvas_id": "F1234567890",
  "audio_count": 3,
  "downloaded_count": 3,
  "files": [
    {
      "index": 0,
      "url": "https://files.slack.com/.../audio1.mp3",
      "local_path": "/downloads/audio_F1234567890_0.mp3",
      "file_size": 1024000
    }
  ]
}
```

## Audio File Processing

### **Audio File Flow**
```
Audio File (file_type: "mp3", "mp4", etc.)
    ↓
Call files.info API with defensive wrapper
    ↓
Extract url_private_download
    ↓
Download file with bot token authentication
    ↓
Save with unique naming: audio_<file_id>_<filename>
    ↓
Return processing results
```

### **Audio Response**
```json
{
  "status": "file processed",
  "file_id": "F1234567890",
  "file_path": "/downloads/audio_F1234567890_audio.mp3",
  "file_size": 1024000,
  "file_name": "audio.mp3"
}
```

## Slack Event Callbacks

### **Event Processing**
```python
if payload.get('type') == 'event_callback':
    event = payload.get('event', {})
    if event.get('type') == 'file_shared':
        file_data = event.get('file', {})
        file_id = file_data.get('id')
        file_type = file_data.get('filetype', '')
        
        # Process as regular file
        return await process_webhook_payload({
            "file_type": file_type,
            "file_id": file_id,
            "slack_token": SLACK_BOT_TOKEN
        })
```

### **URL Verification**
```python
elif payload.get('type') == 'url_verification':
    return {"challenge": payload.get('challenge')}
```

## Error Handling

### **Content Type Errors**
```json
{
  "error": "Invalid request format - expected JSON or form data"
}
```

### **Missing Fields**
```json
{
  "status": "error",
  "error": "Missing required field: file_type"
}
```

### **API Failures**
```json
{
  "status": "canvas fetch failed",
  "error": "Could not retrieve Canvas information"
}
```

### **File Access Errors**
```json
{
  "status": "error",
  "error": "No downloadable URL found"
}
```

## Logging

### **Request Logging**
```
INFO: Received webhook request with content-type: application/json
INFO: Parsed JSON payload successfully
INFO: Processing webhook payload: {"file_type": "mp3", "file_id": "F1234567890", "slack_token": "xoxb-token"}
INFO: Processing mp3 file: F1234567890
```

### **Processing Logging**
```
INFO: Processing Canvas file: F1234567890
INFO: Found 2 audio links in Canvas
INFO: Downloaded audio 1/2: /downloads/audio_F1234567890_0.mp3
INFO: Downloaded audio 2/2: /downloads/audio_F1234567890_1.m4a
INFO: Successfully downloaded 2 audio files from Canvas
```

### **Error Logging**
```
ERROR: Missing file_type in payload
ERROR: Canvas fetch failed
ERROR: Failed to download audio 1/2: https://files.slack.com/.../audio1.mp3
```

## Testing

### **Test Script**
```bash
python test_unified_webhook.py
```

### **Manual Testing**

#### **Test JSON Request**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

#### **Test Form Request**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_type=mp3&file_id=F1234567890&slack_token=xoxb-your-token"
```

#### **Test Canvas Request**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

## Zapier Integration

### **Zapier Configuration**
- **URL**: `https://your-domain.com/webhook/slack`
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded` (recommended)
- **Body**: Form data with required fields

### **Zapier Webhook Fields**
- `file_type` - Type of file (quip, mp3, wav, etc.)
- `file_id` - Slack file ID
- `slack_token` - Your Slack bot token

### **Zapier Response**
```json
{
  "status": "file processed",
  "file_id": "F1234567890",
  "file_path": "/downloads/audio_F1234567890_audio.mp3",
  "file_size": 1024000,
  "file_name": "audio.mp3"
}
```

## Deployment

### **Environment Variables**
```env
SLACK_BOT_TOKEN=xoxb-your-token
ZOHO_DESK_ACCESS_TOKEN=your-zoho-token
TRANSCRIPTION_API_KEY=your-transcription-key
```

### **Server Startup**
```bash
# Start the server
python slack_file_middleware.py

# Or with uvicorn directly
uvicorn slack_file_middleware:app --host 0.0.0.0 --port 8000
```

### **Health Check**
```bash
curl http://localhost:8000/health
```

## Benefits

### **🔄 Unified Interface**
- **Single endpoint** for all request types
- **Automatic content type detection**
- **Consistent response format**
- **Simplified integration**

### **🛡️ Robust Error Handling**
- **Field validation** with clear messages
- **API failure handling** with retry logic
- **Comprehensive logging** for debugging
- **Graceful degradation** on errors

### **🎯 Modular Design**
- **Separate processing functions** for Canvas and audio files
- **Reusable components** for future features
- **Easy to extend** for new file types
- **Clean separation** of concerns

### **📊 Production Ready**
- **Defensive API calls** with timeout protection
- **Comprehensive logging** for monitoring
- **Error categorization** for troubleshooting
- **Performance optimization** with async processing

This unified webhook provides a single, robust endpoint that handles all Slack file processing scenarios with maximum compatibility and reliability.
