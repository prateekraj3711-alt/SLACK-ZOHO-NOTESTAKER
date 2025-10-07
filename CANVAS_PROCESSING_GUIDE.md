# Slack Canvas Processing Guide

This guide explains how the enhanced middleware handles Slack Canvas files with embedded audio content.

## Overview

Slack Canvas files can contain embedded audio files that need to be extracted, converted, and transcribed. The middleware now supports:

- **Canvas File Detection**: Automatically identifies Canvas files
- **Audio Link Extraction**: Parses Canvas blocks to find embedded audio
- **Multi-Audio Processing**: Handles multiple audio files in a single Canvas
- **Combined Transcription**: Merges all audio transcripts into one ticket

## How Canvas Processing Works

### 1. Canvas File Detection
```python
# The system detects Canvas files by:
- File type: 'canvas'
- MIME type: 'application/vnd.slack.canvas'
- File extension patterns
```

### 2. Canvas Parsing Pipeline
```
Canvas File Upload
    ↓
Extract File ID from URL
    ↓
Call files.info API
    ↓
Download Canvas Content
    ↓
Call canvas.info API
    ↓
Parse Canvas Blocks
    ↓
Extract Audio Links
    ↓
Process Each Audio File
    ↓
Combine Transcripts
    ↓
Create Zoho Desk Ticket
```

### 3. Audio Link Extraction
The system extracts audio links from Canvas blocks:

#### Rich Text Blocks
```json
{
  "type": "rich_text",
  "elements": [
    {
      "type": "link",
      "url": "https://files.slack.com/.../audio.mp4"
    }
  ]
}
```

#### File Blocks
```json
{
  "type": "file",
  "file": {
    "url_private_download": "https://files.slack.com/.../audio.mp3"
  }
}
```

## Supported Audio Formats

**Input Formats**: MP3, MP4, WAV, M4A, AAC, OGG, FLAC  
**Output Format**: MP3 (optimized for transcription)

## Processing Flow

### Single Audio File
```
Canvas File → Extract Audio → Convert → Transcribe → Zoho Ticket
```

### Multiple Audio Files
```
Canvas File → Extract Audio Links → Process Each Audio → Combine Transcripts → Zoho Ticket
```

## Canvas Ticket Structure

When a Canvas file is processed, the Zoho Desk ticket includes:

### Subject
```
Canvas File with Audio - [filename]
```

### Description
```
Canvas File: [filename]

Canvas Content:
[First 1000 characters of Canvas text]

Audio Transcripts ([N] audio files):
[Combined transcripts with separators]

Source: Slack Canvas File
Channel: [channel_id]
User: [user_id]
Timestamp: [timestamp]
```

## API Endpoints Used

### 1. files.info
```http
GET https://slack.com/api/files.info?file={file_id}
Authorization: Bearer {slack_token}
```

### 2. canvas.info
```http
GET https://slack.com/api/canvas.info?canvas_id={file_id}
Authorization: Bearer {slack_token}
```

### 3. File Download
```http
GET {file_url}
Authorization: Bearer {slack_token}
```

## Error Handling

### Canvas Parsing Failures
- **API Errors**: Logs error and skips Canvas processing
- **Invalid File ID**: Attempts alternative extraction methods
- **Network Issues**: Retries with exponential backoff

### Audio Processing Failures
- **Download Failures**: Skips failed audio, continues with others
- **Conversion Failures**: Uses original file as fallback
- **Transcription Failures**: Logs error, continues with other audio

### Partial Success Handling
- **Some Audio Fails**: Processes successful audio files
- **All Audio Fails**: Creates ticket with Canvas content only
- **No Audio Found**: Creates ticket with Canvas content only

## Configuration

### Environment Variables
```env
# Existing variables work for Canvas processing
SLACK_BOT_TOKEN=your_slack_bot_token
ZOHO_DESK_ACCESS_TOKEN=your_zoho_access_token
# ... other existing variables
```

### Canvas-Specific Settings
```python
# Canvas detection patterns
CANVAS_INDICATORS = [
    'canvas',
    'application/vnd.slack.canvas',
    'text/canvas'
]

# Audio file extensions
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.mp4']
```

## Monitoring and Logging

### Canvas Processing Logs
```
INFO: Canvas file contains 3 audio files
INFO: Processing audio 1/3: https://files.slack.com/...
INFO: Transcribed audio 1: 245 characters
INFO: Combined transcript length: 1,234 characters
INFO: Created Canvas Zoho ticket: TICKET-12345
```

### Error Logs
```
ERROR: Failed to parse Canvas file: canvas_file_name
ERROR: Could not extract file ID from URL: https://...
ERROR: Transcription failed for audio 2: API quota exceeded
```

## Health Check

The `/health` endpoint now includes Canvas processing status:

```json
{
  "canvas_processing": {
    "enabled": true,
    "supported_types": ["canvas", "application/vnd.slack.canvas"],
    "audio_extraction": "embedded_audio_links",
    "multi_audio_support": true
  }
}
```

## Testing Canvas Processing

### 1. Test Canvas Detection
```python
from slack_webhook_middleware import CanvasParser

parser = CanvasParser("your_slack_token")
is_canvas = parser.is_canvas_file("canvas", "application/vnd.slack.canvas")
print(f"Is Canvas: {is_canvas}")
```

### 2. Test Canvas Parsing
```python
canvas_data = parser.download_and_parse_canvas("file_id")
if canvas_data:
    print(f"Audio links: {len(canvas_data.audio_links)}")
    print(f"Canvas text: {canvas_data.canvas_text[:100]}...")
```

### 3. Test Complete Pipeline
```bash
# Upload a Canvas file with embedded audio to Slack
# Check logs for processing status
# Verify Zoho Desk ticket creation
```

## Performance Considerations

### Canvas Processing Time
- **Small Canvas (1-2 audio)**: 30-60 seconds
- **Large Canvas (5+ audio)**: 2-5 minutes
- **Canvas with no audio**: 5-10 seconds

### Memory Usage
- **Temporary files**: Cleaned up automatically
- **Concurrent processing**: Up to 5 Canvas files simultaneously
- **Audio conversion**: ~1-2 seconds per minute of audio

### API Rate Limits
- **Slack API**: Respects rate limits with backoff
- **Transcription API**: Queues requests to avoid limits
- **Zoho API**: Uses existing OAuth token management

## Troubleshooting

### Common Issues

#### Canvas Not Detected
```
Issue: Canvas file processed as regular file
Solution: Check file type and MIME type in payload
```

#### Audio Links Not Found
```
Issue: Canvas parsed but no audio links extracted
Solution: Check Canvas block structure and audio file extensions
```

#### File ID Extraction Failed
```
Issue: Could not extract file ID from URL
Solution: Check URL pattern and update regex patterns
```

#### Transcription Timeout
```
Issue: Large audio files timeout during transcription
Solution: Increase timeout settings or split large files
```

## Integration with Existing Workflow

The Canvas processing integrates seamlessly with your existing setup:

1. **Zapier Trigger**: Canvas file upload triggers webhook
2. **Middleware Processing**: Detects Canvas, extracts audio, processes
3. **Zoho Desk**: Creates comprehensive ticket with Canvas content and audio transcripts
4. **Slack Feedback**: Posts confirmation message

No changes needed to your existing Zapier configuration!
