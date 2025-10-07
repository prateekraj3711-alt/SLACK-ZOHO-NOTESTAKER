# Zapier Canvas Fix Guide

This guide explains the fix for the "415 Unsupported Media Type" error when processing Canvas files from Zapier webhooks.

## Problem Analysis

### **Root Cause**
Zapier was sending webhook requests with:
- **Content-Type**: `application/json` 
- **Actual Data**: Form-encoded fields (not JSON)
- **Result**: FastAPI rejected the request with "415 Unsupported Media Type"

### **Zapier Payload Structure**
```
Content-Type: application/json
Headers: Authorization: Bearer xoxb-token

Data (form-encoded):
file_id: F09HRKKGYEB
file_type: quip
file_title: :tada::heartpulse::stuck_out_tongue_winking_eye:
slack_token: xoxb-9603666278855-9636828305797-P7bW2wj059dGPt2i0nc4VnzY
event: {...}
token: xoxb-9603666278855-9636828305797-P7bW2wj059dGPt2i0nc4VnzY
```

## Solution Implemented

### **1. Enhanced Content Type Detection**
```python
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
            return JSONResponse(status_code=400, content={"error": "Invalid request format"})
```

### **2. Flexible Field Mapping**
```python
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
```

### **3. Debug Endpoint**
```python
@app.post("/debug/webhook")
async def debug_webhook(request: Request):
    """Debug endpoint to inspect webhook requests"""
    # Returns detailed information about the request
    # Helps troubleshoot content type and payload issues
```

## Canvas Processing Flow

### **Canvas File Processing**
```
Zapier Canvas Webhook
    ↓
Content-Type: application/json (but form data)
    ↓
Enhanced parsing: Try JSON, fallback to form data
    ↓
Extract file_type: "quip", file_id: "F09HRKKGYEB"
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

## Testing

### **Test Script**
```bash
python test_zapier_payload.py
```

### **Manual Testing**

#### **Test Canvas Processing**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F09HRKKGYEB",
    "slack_token": "xoxb-your-token"
  }'
```

#### **Test Debug Endpoint**
```bash
curl -X POST http://localhost:8000/debug/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F09HRKKGYEB",
    "slack_token": "xoxb-your-token"
  }'
```

## Zapier Configuration

### **Webhook Settings**
- **URL**: `https://slack-zoho-notestaker.onrender.com/webhook/slack`
- **Method**: POST
- **Content-Type**: `application/json` (Zapier default)
- **Body**: Form data with Canvas fields

### **Required Fields**
- `file_type`: "quip" (for Canvas files)
- `file_id`: Slack file ID (e.g., "F09HRKKGYEB")
- `slack_token`: Bot token for API calls

### **Optional Fields**
- `file_title`: Canvas title
- `file_url`: Canvas URL
- `user_id`: User who created the Canvas
- `event`: Full Slack event structure

## Response Formats

### **Successful Canvas Processing**
```json
{
  "status": "audio extracted",
  "canvas_id": "F09HRKKGYEB",
  "audio_count": 2,
  "downloaded_count": 2,
  "files": [
    {
      "index": 0,
      "url": "https://files.slack.com/.../audio1.mp3",
      "local_path": "/downloads/audio_F09HRKKGYEB_0.mp3",
      "file_size": 1024000
    },
    {
      "index": 1,
      "url": "https://files.slack.com/.../audio2.m4a",
      "local_path": "/downloads/audio_F09HRKKGYEB_1.m4a",
      "file_size": 2048000
    }
  ]
}
```

### **Error Responses**
```json
{
  "status": "canvas fetch failed",
  "error": "Could not retrieve Canvas information"
}
```

```json
{
  "status": "no audio found",
  "message": "Canvas contains no audio files"
}
```

## Logging

### **Request Logging**
```
INFO: Received webhook request with content-type: application/json
WARNING: JSON parsing failed: Expecting value: line 1 column 1 (char 0), trying form data
INFO: Parsed as form data despite JSON content-type
INFO: Processing webhook payload: {"file_type": "quip", "file_id": "F09HRKKGYEB", ...}
INFO: Processing quip file: F09HRKKGYEB
```

### **Canvas Processing Logging**
```
INFO: Processing Canvas file: F09HRKKGYEB
INFO: Found 2 audio links in Canvas
INFO: Downloaded audio 1/2: /downloads/audio_F09HRKKGYEB_0.mp3
INFO: Downloaded audio 2/2: /downloads/audio_F09HRKKGYEB_1.m4a
INFO: Successfully downloaded 2 audio files from Canvas
```

### **Error Logging**
```
ERROR: Canvas fetch failed: 403 - Forbidden
ERROR: Failed to download audio 1/2: https://files.slack.com/.../audio1.mp3
ERROR: Failed to download any audio files from Canvas
```

## Troubleshooting

### **Common Issues**

#### **1. Content Type Mismatch**
**Error**: `415 Unsupported Media Type`
**Solution**: The enhanced parsing now handles this automatically

#### **2. Missing Fields**
**Error**: `Missing required field: file_type`
**Solution**: Check that Zapier is sending the correct field names

#### **3. Canvas API Failures**
**Error**: `Canvas fetch failed`
**Solution**: Verify the bot token has proper permissions

#### **4. Audio Download Failures**
**Error**: `Failed to download audio`
**Solution**: Check that the audio URLs are accessible with the bot token

### **Debug Steps**

1. **Check server logs** for detailed error messages
2. **Use debug endpoint** to inspect the exact payload structure
3. **Test with curl** to verify endpoint functionality
4. **Verify Zapier configuration** matches the expected format
5. **Check Slack bot permissions** for Canvas access

## Benefits

### **🔄 Robust Content Type Handling**
- **Automatic detection** of actual content type vs. declared type
- **Fallback parsing** for mixed content types
- **Comprehensive error handling** for parsing failures

### **🎯 Flexible Field Mapping**
- **Multiple field name support** (file_type, filetype, etc.)
- **Nested structure handling** (event.file.filetype)
- **Token field mapping** (slack_token, token)

### **🛡️ Enhanced Error Handling**
- **Detailed logging** for debugging
- **Graceful fallbacks** for parsing failures
- **Clear error messages** for troubleshooting

### **📊 Debug Capabilities**
- **Debug endpoint** for payload inspection
- **Comprehensive logging** for all processing steps
- **Error categorization** for quick diagnosis

This fix ensures that Zapier Canvas webhooks work reliably regardless of content type mismatches or field name variations.
