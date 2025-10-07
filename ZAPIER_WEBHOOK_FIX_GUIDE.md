# Zapier Webhook Fix Guide

This guide explains the fix for the "415 Unsupported Media Type" error when using Zapier webhooks with the FastAPI middleware.

## Problem

Zapier was sending webhook requests with the wrong Content-Type header, causing this error:
```
Internal server error: 415 Unsupported Media Type: Did not attempt to load JSON data because the request Content-Type was not 'application/json'.
```

## Solution

The middleware now supports multiple content types and provides alternative endpoints for different request formats.

## Available Endpoints

### 1. JSON Webhook (Original)
```
POST /webhook/slack
Content-Type: application/json
```

**Usage:**
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

### 2. Form Webhook (Zapier Compatible)
```
POST /webhook/slack-form
Content-Type: application/x-www-form-urlencoded
```

**Usage:**
```bash
curl -X POST http://localhost:8000/webhook/slack-form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_type=mp3&file_id=F1234567890&slack_token=xoxb-your-token"
```

## Content Type Support

### Supported Content Types
- ✅ `application/json` - Standard JSON requests
- ✅ `application/x-www-form-urlencoded` - Form-encoded requests (Zapier)
- ✅ `text/plain` - Raw text requests
- ✅ `text/json` - Alternative JSON content type

### Automatic Detection
The middleware automatically detects the content type and parses the request accordingly:

```python
content_type = request.headers.get("content-type", "").lower()

if "application/json" in content_type:
    payload = await request.json()
elif "application/x-www-form-urlencoded" in content_type:
    form_data = await request.form()
    payload = dict(form_data)
else:
    # Try to parse as JSON anyway
    body = await request.body()
    payload = json.loads(body.decode('utf-8'))
```

## Zapier Configuration

### Option 1: Use Form Endpoint
Configure your Zapier webhook to use:
- **URL**: `https://your-domain.com/webhook/slack-form`
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded`
- **Body**: Form data with fields:
  - `file_type`: mp3, mp4, wav, etc.
  - `file_id`: Slack file ID
  - `slack_token`: Your Slack bot token

### Option 2: Use JSON Endpoint with Headers
Configure your Zapier webhook to use:
- **URL**: `https://your-domain.com/webhook/slack`
- **Method**: POST
- **Content-Type**: `application/json`
- **Body**: JSON payload:
  ```json
  {
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }
  ```

## Testing

### Test Script
```bash
python test_zapier_webhook.py
```

### Manual Testing

#### Test JSON Endpoint
```bash
curl -X POST http://localhost:8000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

#### Test Form Endpoint
```bash
curl -X POST http://localhost:8000/webhook/slack-form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_type=mp3&file_id=F1234567890&slack_token=xoxb-your-token"
```

## Error Handling

### Content Type Errors
```json
{
  "error": "Invalid request format"
}
```

### Missing Fields
```json
{
  "error": "Failed to fetch file info"
}
```

### File Access Errors
```json
{
  "error": "No downloadable URL found"
}
```

## Logging

### Request Logging
```
INFO: Received request with content-type: application/x-www-form-urlencoded
INFO: Received form webhook: file_type=mp3, file_id=F1234567890
INFO: Processing webhook payload: {"file_type": "mp3", "file_id": "F1234567890", "slack_token": "xoxb-your-token"}
```

### Error Logging
```
ERROR: Failed to parse request body: Expecting value: line 1 column 1 (char 0)
ERROR: Form webhook error: 'file_type'
```

## Response Formats

### Successful Processing
```json
{
  "status": "file processed",
  "file_id": "F1234567890",
  "file_path": "/downloads/audio_F1234567890_audio.mp3",
  "file_size": 1024000,
  "file_name": "audio.mp3"
}
```

### Canvas Processing
```json
{
  "status": "audio extracted",
  "canvas_id": "F1234567890",
  "audio_count": 2,
  "downloaded_count": 2,
  "files": [
    {
      "index": 0,
      "url": "https://files.slack.com/.../audio1.mp3",
      "local_path": "/downloads/audio_F1234567890_0.mp3",
      "file_size": 512000
    }
  ]
}
```

## Deployment

### Environment Variables
```env
SLACK_BOT_TOKEN=xoxb-your-token
ZOHO_DESK_ACCESS_TOKEN=your-zoho-token
TRANSCRIPTION_API_KEY=your-transcription-key
```

### Server Configuration
```python
# Start the server
python slack_file_middleware.py

# Or with uvicorn directly
uvicorn slack_file_middleware:app --host 0.0.0.0 --port 8000
```

### Nginx Configuration (Optional)
```nginx
location /webhook/ {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Troubleshooting

### Common Issues

#### 1. Content Type Mismatch
**Error**: `415 Unsupported Media Type`
**Solution**: Use the form endpoint `/webhook/slack-form` or ensure JSON requests have `Content-Type: application/json`

#### 2. Missing Fields
**Error**: `Failed to fetch file info`
**Solution**: Ensure all required fields are provided in the webhook payload

#### 3. Authentication Issues
**Error**: `Invalid authentication token`
**Solution**: Check that the Slack bot token is valid and has proper permissions

#### 4. File Access Issues
**Error**: `No downloadable URL found`
**Solution**: Ensure the file exists and the bot has access to it

### Debug Steps

1. **Check server logs** for detailed error messages
2. **Test with curl** to verify endpoint functionality
3. **Verify Zapier configuration** matches the expected format
4. **Check Slack bot permissions** for file access
5. **Test with different content types** to find the working combination

## Best Practices

### For Zapier Integration
1. **Use the form endpoint** (`/webhook/slack-form`) for better compatibility
2. **Include all required fields** in the webhook payload
3. **Test with sample data** before deploying to production
4. **Monitor logs** for any issues

### For Direct Integration
1. **Use JSON endpoint** (`/webhook/slack`) for better performance
2. **Set proper Content-Type headers**
3. **Handle errors gracefully** in your client code
4. **Implement retry logic** for transient failures

This fix ensures compatibility with Zapier webhooks while maintaining support for direct JSON requests and other content types.
