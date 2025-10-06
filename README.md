# Slack Voice to Zapier Middleware

A Flask middleware service that processes Slack voice messages and sends transcriptions to Zapier for further processing.

## Features

- Downloads audio files from Slack
- Transcribes audio using Deepgram API
- Sends transcription data to Zapier webhook
- Handles multiple audio formats
- Comprehensive error handling
- **Duplicate Prevention System** - No audio uploaded twice
- Automatic cleanup of processed files

## Environment Variables

- `DEEPGRAM_API_KEY` - Your Deepgram API key
- `ZAPIER_WEBHOOK_URL` - Your Zapier webhook URL

## Endpoints

- `GET /` - Health check
- `GET /status` - Detailed system status
- `POST /slack-webhook` - Handle Slack voice message webhooks

## Duplicate Prevention

The system includes a built-in duplicate prevention mechanism:

- **File Hash Generation** - Creates unique identifiers for each file
- **Processed Files Tracking** - In-memory storage of processed files
- **Duplicate Detection** - Prevents processing the same file twice
- **Automatic Cleanup** - Removes old entries after 24 hours

## Deployment

This service is designed to be deployed on Render.com

### Quick Deploy to Render

1. Upload this code to a GitHub repository
2. Connect your GitHub repository to Render
3. Set the environment variables in Render dashboard
4. Deploy!

## Usage

1. Set up Zapier to trigger on new Slack files
2. Configure Zapier to send data to your Render webhook URL
3. The middleware will process audio and send transcriptions to Zapier

## API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Voice message processed and sent to Zapier",
  "transcript": "Your transcribed text here",
  "file_hash": "unique_file_identifier",
  "duplicate_prevention": "passed"
}
```

### Duplicate Prevention Response
```json
{
  "success": true,
  "message": "File already processed, skipping duplicate",
  "file_hash": "unique_file_identifier",
  "duplicate_prevention": "triggered"
}
```

## Status Endpoints

### Health Check
```bash
GET /
```

### System Status
```bash
GET /status
```

Returns detailed system information including processed files count and recent activity.
