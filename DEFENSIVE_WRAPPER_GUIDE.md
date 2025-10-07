# Defensive File Info Wrapper Guide

This guide explains the defensive `files.info` wrapper implementation that provides robust error handling for Slack API calls.

## Overview

The defensive wrapper replaces direct Slack API calls with comprehensive error handling, logging, and graceful failure management.

## Key Features

### 🛡️ **Comprehensive Error Handling**
- **HTTP errors**: Network failures, timeouts, connection issues
- **Slack API errors**: Authentication, permissions, file access
- **Data validation**: Missing fields, malformed responses
- **Timeout protection**: 30-second timeout for API calls

### 📊 **Detailed Logging**
- **API failures**: Status codes, error messages, response content
- **Slack errors**: Specific error types with explanations
- **File information**: Extracted keys, file metadata
- **Network issues**: Timeouts, connection errors

### 🔍 **Specific Slack Error Handling**
- `invalid_auth` - Invalid authentication token
- `file_not_found` - File doesn't exist or not accessible
- `not_authed` - Not authenticated, check bot permissions
- `account_inactive` - Slack account is inactive
- `token_revoked` - Slack token has been revoked

## Implementation

### Core Function
```python
def get_file_info(file_id: str, slack_token: str) -> Optional[Dict[str, Any]]:
    """Defensive files.info wrapper with comprehensive error handling"""
    try:
        headers = {"Authorization": f"Bearer {slack_token}"}
        response = requests.get(
            f"https://slack.com/api/files.info?file={file_id}", 
            headers=headers, 
            timeout=30
        )

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
```

### Webhook Integration
```python
# Get file info with defensive wrapper
file_info = get_file_info(file_id, slack_token)
if not file_info:
    logger.error("Failed to fetch file info")
    return JSONResponse(
        status_code=400, 
        content={"error": "Failed to fetch file info"}
    )

# Extract download URL
file_url = file_info.get("url_private_download")
if not file_url:
    logger.error("Missing url_private_download in file_info")
    return JSONResponse(
        status_code=400, 
        content={"error": "No downloadable URL found"}
    )
```

## Error Scenarios

### 1. Network Errors
```
ERROR: Timeout fetching file info for F1234567890
ERROR: Connection error fetching file info for F1234567890
ERROR: Unexpected error fetching file info: Connection timeout
```

### 2. Slack API Errors
```
ERROR: Slack API error: 403 - Forbidden
ERROR: Slack API returned failure: invalid_auth - {"ok": false, "error": "invalid_auth"}
ERROR: Invalid authentication token
```

### 3. File Access Errors
```
ERROR: Slack API returned failure: file_not_found - {"ok": false, "error": "file_not_found"}
ERROR: File not found: F1234567890
```

### 4. Authentication Errors
```
ERROR: Slack API returned failure: not_authed - {"ok": false, "error": "not_authed"}
ERROR: Not authenticated - check bot token permissions
```

## Response Handling

### Successful Response
```json
{
  "status": "file processed",
  "file_id": "F1234567890",
  "file_path": "/downloads/audio_F1234567890_audio.mp3",
  "file_size": 1024000,
  "file_name": "audio.mp3"
}
```

### Error Responses
```json
{
  "error": "Failed to fetch file info"
}
```

```json
{
  "error": "No downloadable URL found"
}
```

## Logging Examples

### Successful File Info
```
INFO: Extracted file info keys: ['id', 'name', 'title', 'mimetype', 'size', 'url_private_download', 'user', 'channels']
INFO: File info: id=F1234567890, name=audio.mp3, mimetype=audio/mpeg
```

### API Failure
```
ERROR: Slack API error: 403 - Forbidden
ERROR: Slack API returned failure: invalid_auth - {"ok": false, "error": "invalid_auth"}
ERROR: Invalid authentication token
```

### Network Issues
```
ERROR: Timeout fetching file info for F1234567890
ERROR: Connection error fetching file info for F1234567890
```

## Testing

### Test Script
```bash
python test_defensive_wrapper.py
```

### Manual Testing
```bash
# Test with valid file ID
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'

# Test with invalid file ID
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F9999999999",
    "slack_token": "xoxb-your-token"
  }'
```

## Benefits

### 🛡️ **Robust Error Handling**
- **Graceful failures**: No crashes on API errors
- **Detailed logging**: Clear error messages for debugging
- **Timeout protection**: Prevents hanging requests
- **Network resilience**: Handles connection issues

### 📊 **Better Monitoring**
- **Specific error types**: Know exactly what went wrong
- **File metadata logging**: Track what files are being processed
- **Performance insights**: Monitor API response times
- **Debug information**: Detailed logs for troubleshooting

### 🔧 **Easier Debugging**
- **Clear error messages**: Know exactly what failed
- **Context information**: File IDs, tokens, response data
- **Error categorization**: Network vs API vs data issues
- **Stack traces**: Full error context when needed

## Integration Points

### Webhook Handler
```python
@app.post("/webhook/slack")
async def slack_webhook(request: Request):
    # Extract file_id and slack_token
    file_info = get_file_info(file_id, slack_token)
    if not file_info:
        return JSONResponse(status_code=400, content={"error": "Failed to fetch file info"})
    
    file_url = file_info.get("url_private_download")
    if not file_url:
        return JSONResponse(status_code=400, content={"error": "No downloadable URL found"})
```

### Canvas Processing
```python
# Canvas files use canvas.info API
canvas_json = get_canvas_info(canvas_id, slack_token)
if not canvas_json:
    return {"status": "canvas fetch failed"}
```

### Regular File Processing
```python
# Regular files use files.info API
file_info = get_file_info(file_id, slack_token)
if not file_info:
    return {"error": "Failed to fetch file info"}
```

## Configuration

### Timeout Settings
```python
# 30-second timeout for API calls
response = requests.get(url, timeout=30)
```

### Retry Logic (Optional)
```python
# Add retry logic for transient failures
import time

def get_file_info_with_retry(file_id: str, slack_token: str, max_retries: int = 3):
    for attempt in range(max_retries):
        result = get_file_info(file_id, slack_token)
        if result:
            return result
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Log Monitoring
```bash
# Monitor for API errors
grep "Slack API error" logs/middleware.log

# Monitor for authentication issues
grep "invalid_auth\|not_authed" logs/middleware.log

# Monitor for file access issues
grep "file_not_found" logs/middleware.log
```

This defensive wrapper provides robust, production-ready error handling for Slack API interactions with comprehensive logging and graceful failure management.
