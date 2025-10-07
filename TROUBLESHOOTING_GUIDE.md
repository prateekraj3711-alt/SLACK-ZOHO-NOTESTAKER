# Troubleshooting Guide

This guide helps you resolve common issues with the Slack middleware system.

## Common Issues and Solutions

### **1. Audio Conversion Failed**

#### **Error**: `Audio conversion failed for: :tada::heartpulse::stuck_out_tongue_winking_eye:`

#### **Root Cause**: Canvas file processing issues
- Canvas files are not being processed correctly
- Audio files are not being extracted from Canvas
- FFmpeg is not installed or not working

#### **Solutions**:

##### **A. Check Canvas Processing**
```bash
# Test Canvas processing
curl -X POST http://localhost:5000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F09HRKKGYEB",
    "slack_token": "xoxb-your-token"
  }'
```

##### **B. Install FFmpeg**
```bash
# Windows (PowerShell)
.\setup_ffmpeg_windows.ps1

# Or manually install FFmpeg
# Download from https://ffmpeg.org/download.html
# Add to PATH environment variable
```

##### **C. Check Canvas API Access**
- Ensure your Slack bot token has `files:read` scope
- Test Canvas API access manually:
```bash
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/canvas.info?canvas_id=F09HRKKGYEB"
```

### **2. Deepgram API Authentication Failed**

#### **Error**: `Deepgram API error: 401 - {"err_code":"INVALID_AUTH","err_msg":"Invalid credentials."}`

#### **Root Cause**: Invalid or missing Deepgram API key

#### **Solutions**:

##### **A. Get Deepgram API Key**
1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Sign up or log in
3. Create a new project
4. Get your API key from the project settings

##### **B. Set Environment Variables**
```bash
# Set the environment variable
export TRANSCRIPTION_API_KEY=your-deepgram-api-key-here
export TRANSCRIPTION_PROVIDER=deepgram
```

##### **C. Test Deepgram API**
```bash
# Test Deepgram API directly
curl -X POST "https://api.deepgram.com/v1/listen" \
  -H "Authorization: Token your-api-key-here" \
  -H "Content-Type: audio/mp3" \
  --data-binary @test_audio.mp3
```

### **3. Canvas File Processing Issues**

#### **Error**: Canvas files not being processed correctly

#### **Solutions**:

##### **A. Check Canvas File Structure**
```python
# Test Canvas info API
import requests

headers = {"Authorization": "Bearer xoxb-your-token"}
response = requests.get(f"https://slack.com/api/canvas.info?canvas_id=F09HRKKGYEB", headers=headers)
print(response.json())
```

##### **B. Verify Audio Links Extraction**
- Check if Canvas contains audio files
- Verify audio file URLs are accessible
- Test audio file downloads

##### **C. Check Bot Permissions**
- Ensure bot has `files:read` scope
- Ensure bot has `channels:history` scope
- Test with a simple file first

### **4. Environment Configuration Issues**

#### **Error**: Missing or invalid environment variables

#### **Solutions**:

##### **A. Check Required Variables**
```bash
# Check if all required variables are set
echo $SLACK_BOT_TOKEN
echo $TRANSCRIPTION_API_KEY
echo $ZOHO_DESK_ACCESS_TOKEN
```

##### **B. Create .env File**
```bash
# Create .env file with all required variables
cp env.example .env
# Edit .env file with your actual values
```

##### **C. Test Environment Variables**
```python
# Test in Python
import os
print("SLACK_BOT_TOKEN:", os.getenv("SLACK_BOT_TOKEN"))
print("TRANSCRIPTION_API_KEY:", os.getenv("TRANSCRIPTION_API_KEY"))
```

### **5. FFmpeg Installation Issues**

#### **Error**: FFmpeg not found or not working

#### **Solutions**:

##### **A. Install FFmpeg (Windows)**
```powershell
# Run the setup script
.\setup_ffmpeg_windows.ps1

# Or install manually
# 1. Download FFmpeg from https://ffmpeg.org/download.html
# 2. Extract to C:\ffmpeg
# 3. Add C:\ffmpeg\bin to PATH
```

##### **B. Test FFmpeg Installation**
```bash
# Test FFmpeg
ffmpeg -version

# Test audio conversion
ffmpeg -i input.mp4 -acodec mp3 output.mp3
```

##### **C. Check FFmpeg in Python**
```python
# Test FFmpeg in Python
import subprocess
result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
print(result.stdout)
```

## Debugging Steps

### **1. Enable Debug Logging**
```python
# Add to your middleware
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **2. Test Individual Components**
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test webhook endpoint
curl -X POST http://localhost:5000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### **3. Check Logs**
```bash
# Check application logs
tail -f logs/middleware.log

# Check system logs
journalctl -u your-service-name
```

### **4. Test API Endpoints**
```bash
# Test Slack API
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/auth.test"

# Test Deepgram API
curl -X POST "https://api.deepgram.com/v1/listen" \
  -H "Authorization: Token your-api-key-here" \
  -H "Content-Type: audio/mp3" \
  --data-binary @test_audio.mp3
```

## Quick Fixes

### **1. Reset Environment**
```bash
# Restart the application
sudo systemctl restart your-service

# Or if running locally
pkill -f python
python main.py
```

### **2. Clear Cache**
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### **3. Reinstall Dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### **4. Test with Simple File**
```bash
# Test with a simple audio file first
curl -X POST http://localhost:5000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "mp3",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

## Prevention

### **1. Regular Health Checks**
- Monitor application logs
- Set up health check endpoints
- Use monitoring tools

### **2. Environment Validation**
- Validate all environment variables on startup
- Test API connections during initialization
- Provide clear error messages for missing variables

### **3. Graceful Error Handling**
- Handle API failures gracefully
- Provide fallback options
- Log detailed error information

This troubleshooting guide should help you resolve the audio conversion and transcription issues!
