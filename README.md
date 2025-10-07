# 🔗 Slack Zapier Middleware - Complete Package

## 🎯 Overview

A production-ready Flask middleware that automatically processes Slack audio files via Zapier webhooks and creates Zoho Desk tickets with AI transcriptions.

## ✨ Key Features

- **🔗 Zapier Integration** - Automatic Slack file detection
- **🚫 Duplicate Prevention** - Each audio file processed only once
- **🎯 Multi-Provider Transcription** - Deepgram, AssemblyAI, OpenAI Whisper
- **📋 Zoho Desk Integration** - Automatic ticket creation and updates
- **💬 Slack Feedback** - Posts processing status back to Slack
- **🔄 Async Processing** - Background processing prevents timeouts
- **📊 Health Monitoring** - Built-in health checks and status endpoints

## 🏗️ Complete Workflow

```
Slack (New File) → Zapier → Middleware → Transcription → Zoho Desk
     ↓              ↓         ↓            ↓           ↓
  Audio File    Webhook    Download    AI Analysis   Ticket
  Upload        Trigger    & Process    & Extract    Creation
```

## 🚀 Quick Start (5 Minutes)

### Step 1: Deploy to Render (2 minutes)

1. **Upload to GitHub**:
   ```bash
   cd slack-zapier-middleware
   git init
   git add .
   git commit -m "Deploy Slack Zapier middleware"
   git remote add origin https://github.com/your-username/slack-zapier-middleware.git
   git push -u origin main
   ```

2. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Set environment variables (see below)
   - Deploy!

### Step 2: Set Up Zapier (3 minutes)

1. **Go to [zapier.com](https://zapier.com)**
2. **Create new Zap**
3. **Choose Trigger**: "Slack - New File in Channel"
4. **Choose Action**: "Webhooks - POST"
5. **Configure webhook**:
   - **URL**: `https://your-app-name.onrender.com/webhook/slack`
   - **Method**: POST
   - **Data**: Use payload from `zapier_webhook_payload.json`
6. **Test and activate!**

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here

# Zoho Desk Configuration
ZOHO_DESK_API_KEY=your-zoho-desk-api-key-here
ZOHO_DESK_ORG_ID=your-zoho-org-id-here
ZOHO_DESK_DOMAIN=your-domain.zohodesk.com

# Transcription Service
TRANSCRIPTION_API_KEY=your-transcription-api-key-here
TRANSCRIPTION_PROVIDER=deepgram  # or assemblyai, whisper

# OpenAI (if using whisper)
OPENAI_API_KEY=your-openai-api-key-here
```

## 📁 Files Included

### Core Application
- **`slack_webhook_middleware.py`** - Main Flask application with duplicate prevention
- **`requirements.txt`** - Python dependencies
- **`env.example`** - Environment configuration template

### Render Configuration
- **`render.yaml`** - Auto-configuration for Render
- **`Procfile`** - Process configuration
- **`runtime.txt`** - Python version specification

### Zapier Integration
- **`zapier_webhook_payload.json`** - Exact payload structure for Zapier
- **`ZAPIER_SETUP_GUIDE.md`** - Complete step-by-step Zapier setup
- **`ZAPIER_QUICK_START.md`** - 5-minute quick start guide

### Documentation
- **`README.md`** - This file
- **`RENDER_DEPLOYMENT_GUIDE.md`** - Detailed deployment instructions
- **`DUPLICATE_PREVENTION_GUIDE.md`** - Duplicate prevention documentation

### Testing
- **`test_slack_middleware.py`** - General middleware testing
- **`test_zapier_integration.py`** - Zapier-specific testing

## 🧪 Testing Your Setup

### Test 1: Health Check
```bash
curl https://your-app-name.onrender.com/health
```

### Test 2: Zapier Webhook
```bash
curl -X POST https://your-app-name.onrender.com/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_info": {
      "url_private": "https://files.slack.com/files-pri/123/test.mp3",
      "name": "test.mp3",
      "filetype": "mp3"
    },
    "user_id": "U1234567890",
    "channel_id": "C1234567890",
    "timestamp": "1640995200.123456"
  }'
```

### Test 3: Duplicate Prevention
```bash
# Send same payload twice - second should be rejected as duplicate
```

## 🚫 Duplicate Prevention

The system includes comprehensive duplicate prevention:

- **SQLite Database** - Tracks all processed files
- **Unique Hash Generation** - Based on file URL, name, user, channel
- **Status Tracking** - Processing, completed, failed
- **Automatic Detection** - Prevents duplicate processing
- **Audit Trail** - Complete processing history

## 📊 Monitoring

### Health Endpoints
- `GET /` - Service information
- `GET /health` - Health check with service status
- `GET /status/<file_hash>` - File processing status
- `GET /processed-files` - List of processed files

### Zapier Monitoring
- Check Zapier dashboard for execution history
- Monitor webhook success rates
- Set up alerts for failures

## 🔧 Troubleshooting

### Common Issues

1. **Zapier not triggering**:
   - Check Slack permissions
   - Verify channel selection
   - Test with manual upload

2. **Webhook failing**:
   - Verify middleware URL is correct
   - Check environment variables
   - Review middleware logs

3. **No tickets created**:
   - Verify Zoho API credentials
   - Check transcription service
   - Review error logs

### Debug Commands

```bash
# Test middleware health
curl https://your-app-name.onrender.com/health

# Test webhook manually
curl -X POST https://your-app-name.onrender.com/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{"file_info": {"url_private": "https://example.com/test.mp3", "name": "test.mp3", "filetype": "mp3"}, "user_id": "U1234567890", "channel_id": "C1234567890", "timestamp": "1640995200.123456"}'
```

## 🎯 What Happens Automatically

Once your Zapier integration is active:

1. **User uploads audio file** to Slack
2. **Zapier detects** the new file
3. **Zapier sends webhook** to your middleware
4. **Middleware processes** the file:
   - Downloads audio from Slack
   - Transcribes using AI
   - Extracts contact information
   - Creates/updates Zoho Desk ticket
   - Posts feedback to Slack
5. **No duplicates** - Each file processed only once

## 🚀 Deployment Options

- **Render** (recommended) - Easy setup, auto-scaling
- **Railway** - Modern platform, GitHub integration
- **Heroku** - Traditional PaaS
- **Docker** - Containerized deployment
- **Local** - Development and testing

## 📚 Documentation

- [Zapier Setup Guide](ZAPIER_SETUP_GUIDE.md) - Complete Zapier configuration
- [Zapier Quick Start](ZAPIER_QUICK_START.md) - 5-minute setup
- [Render Deployment Guide](RENDER_DEPLOYMENT_GUIDE.md) - Detailed deployment
- [Duplicate Prevention Guide](DUPLICATE_PREVENTION_GUIDE.md) - Duplicate prevention

## 🆘 Support

### Getting Help

1. **Check the logs** in Render dashboard
2. **Test components individually**:
   - Test Slack trigger manually
   - Test webhook endpoint directly
   - Test transcription service
   - Test Zoho Desk API
3. **Review error messages** in logs
4. **Verify all API keys** are correct

### Quick Tests

```bash
# Test middleware health
curl https://your-app-name.onrender.com/health

# Test Zapier integration
python test_zapier_integration.py

# Test general middleware
python test_slack_middleware.py
```

## 🎉 Benefits

- ✅ **Zero Manual Work** - Fully automated processing
- ✅ **No Duplicates** - Each file processed only once
- ✅ **Cost Efficient** - No wasted API calls
- ✅ **Production Ready** - Health checks, error handling, monitoring
- ✅ **Easy Deployment** - One-click Render deployment
- ✅ **Complete Audit Trail** - Track all processed files

---

## 🚀 **Your Slack Zapier Middleware is Ready!**

Upload this folder to GitHub, deploy to Render, configure Zapier, and you'll have a fully automated system that:

- **Detects new audio files** in Slack
- **Processes them automatically** via Zapier
- **Creates Zoho Desk tickets** with transcriptions
- **Posts feedback** back to Slack
- **Never processes duplicates**

**No manual intervention required!** 🎯