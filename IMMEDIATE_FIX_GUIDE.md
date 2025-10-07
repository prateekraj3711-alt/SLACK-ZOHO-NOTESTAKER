# Immediate Fix Guide

This guide provides step-by-step instructions to fix the current errors.

## 🚨 Current Issues

1. **Audio conversion failed** - Canvas file processing issue
2. **Deepgram API 401 error** - Invalid credentials

## 🔧 Step-by-Step Fix

### **Step 1: Set Environment Variables**

#### **A. Create .env File**
```bash
# The script already created .env from env.example
# Now edit it with your actual values
```

#### **B. Get Required API Keys**

##### **1. Slack Bot Token**
1. Go to [Slack API](https://api.slack.com/apps)
2. Select your app
3. Go to "OAuth & Permissions"
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

##### **2. Deepgram API Key**
1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Sign up or log in
3. Create a new project
4. Go to "API Keys" section
5. Copy your API key

##### **3. Zoho Desk Access Token**
1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Create a new app
3. Get the access token and refresh token

#### **C. Edit .env File**
```bash
# Edit the .env file with your actual values
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
TRANSCRIPTION_API_KEY=your-actual-deepgram-key-here
ZOHO_DESK_ACCESS_TOKEN=your-actual-zoho-token-here
ZOHO_DESK_REFRESH_TOKEN=your-actual-refresh-token-here
ZOHO_DESK_CLIENT_ID=your-actual-client-id-here
ZOHO_DESK_CLIENT_SECRET=your-actual-client-secret-here
ZOHO_DESK_ORG_ID=your-actual-org-id-here
ZOHO_DESK_DOMAIN=desk.zoho.com
TRANSCRIPTION_PROVIDER=deepgram
```

### **Step 2: Test the Fix**

#### **A. Run Diagnostic Script**
```bash
python quick_fix.py
```

#### **B. Test Canvas Processing**
```bash
# Test with your actual Canvas file
curl -X POST http://localhost:5000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F09HRKKGYEB",
    "slack_token": "xoxb-your-actual-token"
  }'
```

### **Step 3: Verify Bot Permissions**

#### **A. Check Slack Bot Scopes**
Your bot needs these scopes:
- `files:read` - To read files and Canvas
- `channels:history` - To read channel messages
- `chat:write` - To post messages (optional)

#### **B. Test Bot Permissions**
```bash
# Test bot authentication
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/auth.test"
```

### **Step 4: Test Canvas API Access**

#### **A. Test Canvas Info API**
```bash
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/canvas.info?canvas_id=F09HRKKGYEB"
```

#### **B. Check Canvas Response**
The response should contain:
- `"ok": true`
- Canvas blocks with audio files
- Accessible audio URLs

### **Step 5: Test Deepgram API**

#### **A. Test Deepgram Connection**
```bash
curl -H "Authorization: Token your-deepgram-key" \
  "https://api.deepgram.com/v1/projects"
```

#### **B. Test Audio Transcription**
```bash
curl -X POST "https://api.deepgram.com/v1/listen" \
  -H "Authorization: Token your-deepgram-key" \
  -H "Content-Type: audio/mp3" \
  --data-binary @test_audio.mp3
```

## 🚀 Quick Commands

### **1. Set Environment Variables (Windows)**
```powershell
# Set environment variables for current session
$env:SLACK_BOT_TOKEN="xoxb-your-token"
$env:TRANSCRIPTION_API_KEY="your-deepgram-key"
$env:ZOHO_DESK_ACCESS_TOKEN="your-zoho-token"

# Or set permanently
[Environment]::SetEnvironmentVariable("SLACK_BOT_TOKEN", "xoxb-your-token", "User")
```

### **2. Test All Components**
```bash
# Run diagnostic script
python quick_fix.py

# Test health endpoint
curl http://localhost:5000/health

# Test webhook endpoint
curl -X POST http://localhost:5000/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### **3. Start the Application**
```bash
# Start Flask middleware
python main.py

# Or start FastAPI middleware
python main_fastapi.py
```

## 🔍 Debugging

### **1. Check Logs**
```bash
# Check application logs for detailed error messages
tail -f logs/middleware.log
```

### **2. Test Individual Components**
```bash
# Test Slack API
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/auth.test"

# Test Deepgram API
curl -H "Authorization: Token your-deepgram-key" \
  "https://api.deepgram.com/v1/projects"
```

### **3. Verify Canvas Processing**
```bash
# Test Canvas info API
curl -H "Authorization: Bearer xoxb-your-token" \
  "https://slack.com/api/canvas.info?canvas_id=F09HRKKGYEB"
```

## ✅ Success Indicators

### **1. Environment Variables**
- All required variables set with actual values
- No default placeholder values

### **2. API Connections**
- Slack API returns `"ok": true`
- Deepgram API returns project list
- Canvas API returns canvas data

### **3. Application Startup**
- No error messages during startup
- Health endpoint returns 200
- Webhook endpoint accepts requests

### **4. Canvas Processing**
- Canvas files are processed successfully
- Audio files are extracted and downloaded
- Audio conversion works correctly
- Transcription completes successfully

## 🆘 If Issues Persist

### **1. Check Bot Permissions**
- Ensure bot has `files:read` scope
- Ensure bot has `channels:history` scope
- Reinstall bot if needed

### **2. Verify API Keys**
- Double-check all API keys are correct
- Ensure keys are not expired
- Test keys individually

### **3. Check FFmpeg**
- Ensure FFmpeg is installed and in PATH
- Test FFmpeg with a simple audio file
- Check FFmpeg version compatibility

### **4. Review Logs**
- Check application logs for detailed errors
- Look for specific error messages
- Test with simple files first

This guide should resolve your audio conversion and transcription issues!
