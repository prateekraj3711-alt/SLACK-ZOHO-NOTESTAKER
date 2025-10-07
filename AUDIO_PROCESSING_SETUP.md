# Slack Audio Processing Setup Guide

This guide explains how to set up audio conversion for Slack files that appear as .mp4 format and convert them to MP3 for transcription and posting to Zoho Desk via Zapier.

## Overview

Slack audio files are often downloaded as `.mp4` files because they use MP4 containers for audio content. This middleware now includes:

- **Automatic audio detection** regardless of file extension
- **MP4 to MP3 conversion** using FFmpeg
- **Enhanced error handling** for conversion failures
- **Fallback mechanisms** when conversion fails

## Prerequisites

### 1. FFmpeg Installation

FFmpeg is required for audio conversion. Choose your platform:

#### Windows
```powershell
# Run the setup script
.\setup_ffmpeg_windows.ps1

# Or install manually:
# 1. Download from https://ffmpeg.org/download.html
# 2. Extract to C:\ffmpeg\bin\
# 3. Add C:\ffmpeg\bin\ to your PATH
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### 2. Python Dependencies

```bash
pip install -r requirements_audio.txt
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Existing variables...
SLACK_BOT_TOKEN=your_slack_bot_token
ZOHO_DESK_ACCESS_TOKEN=your_zoho_access_token
ZOHO_DESK_REFRESH_TOKEN=your_zoho_refresh_token
ZOHO_DESK_CLIENT_ID=your_zoho_client_id
ZOHO_DESK_CLIENT_SECRET=your_zoho_client_secret
ZOHO_DESK_ORG_ID=your_zoho_org_id
TRANSCRIPTION_API_KEY=your_transcription_api_key
TRANSCRIPTION_PROVIDER=deepgram  # or assemblyai, whisper

# Audio processing settings (optional)
AUDIO_CONVERSION_ENABLED=true
AUDIO_BITRATE=128k
AUDIO_SAMPLE_RATE=44100
```

## How It Works

### 1. File Detection
- Downloads Slack files with original extensions (.mp4, .m4a, etc.)
- Uses FFprobe to detect audio content regardless of extension
- Falls back to extension-based detection if FFprobe unavailable

### 2. Audio Conversion
- Automatically converts MP4/M4A files to MP3
- Uses optimized settings: 128kbps, 44.1kHz
- Preserves original file as fallback if conversion fails

### 3. Processing Pipeline
```
Slack Audio File (.mp4)
    ↓
Download with original extension
    ↓
Detect audio content (FFprobe)
    ↓
Convert to MP3 (FFmpeg)
    ↓
Transcribe audio
    ↓
Extract contact information
    ↓
Create/Update Zoho Desk ticket
    ↓
Post feedback to Slack
    ↓
Cleanup temporary files
```

## Testing

### 1. Health Check
```bash
curl http://localhost:5000/health
```

Expected response includes:
```json
{
  "audio_processing": {
    "ffmpeg_available": true,
    "conversion_support": "mp4_to_mp3",
    "supported_formats": ["mp3", "mp4", "wav", "m4a", "aac", "ogg", "flac"]
  }
}
```

### 2. Test Audio Conversion
```python
# Test script
from slack_webhook_middleware import AudioConverter

converter = AudioConverter()
print(f"FFmpeg available: {bool(converter.ffmpeg_path)}")

# Test with a sample file
if converter.is_audio_file("sample.mp4"):
    converted = converter.convert_to_mp3("sample.mp4")
    print(f"Conversion result: {converted}")
```

## Troubleshooting

### FFmpeg Not Found
```
Error: FFmpeg not found in PATH or common locations
```
**Solution**: Install FFmpeg and ensure it's in your PATH

### Conversion Fails
```
Error: Audio conversion failed
```
**Solutions**:
1. Check FFmpeg installation
2. Verify file is actually audio
3. Check file permissions
4. Review FFmpeg logs

### Transcription Fails
```
Error: Transcription failed
```
**Solutions**:
1. Check transcription API key
2. Verify audio file quality
3. Check API quotas/limits

## Supported Formats

### Input Formats (Slack)
- MP4 (audio in MP4 container)
- M4A (AAC audio)
- MP3 (direct)
- WAV (uncompressed)
- AAC (compressed)

### Output Format
- MP3 (128kbps, 44.1kHz)

## Performance Considerations

- **Conversion time**: ~1-2 seconds per minute of audio
- **File size**: MP3 typically 10-20% of original MP4
- **Memory usage**: Temporary files cleaned up automatically
- **Concurrent processing**: Up to 5 files simultaneously

## Error Handling

The system includes multiple fallback mechanisms:

1. **FFmpeg unavailable**: Falls back to original file
2. **Conversion fails**: Uses original file for transcription
3. **Audio detection fails**: Attempts conversion anyway
4. **Transcription fails**: Logs error, continues with other files

## Monitoring

Check logs for:
- Audio conversion success/failure
- File processing status
- FFmpeg availability
- Transcription results

## Zapier Integration

The enhanced middleware works seamlessly with your existing Zapier setup:

1. **Slack Trigger**: File uploaded to channel
2. **Zapier Action**: POST to your middleware webhook
3. **Middleware Processing**: Download → Convert → Transcribe → Post to Zoho
4. **Zoho Desk**: Ticket created/updated with transcription

No changes needed to your Zapier configuration!
