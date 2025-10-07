# Deployment Guide

This guide explains how to deploy your Slack middleware system with both Flask and FastAPI options.

## Deployment Options

### **Option 1: Flask Middleware (Recommended for Zapier)**
- **File**: `main.py`
- **Port**: 5000 (default)
- **Features**: Canvas processing, audio conversion, Zapier integration
- **Best for**: Zapier webhooks, existing integrations

### **Option 2: FastAPI Middleware (Recommended for Direct API)**
- **File**: `main_fastapi.py`
- **Port**: 8000 (default)
- **Features**: Unified webhook, Canvas processing, RESTful API
- **Best for**: Direct API calls, modern webhook handling

## Configuration Files

### **Procfile (Heroku/Render)**
```
# For Flask (default)
web: python main.py

# For FastAPI (alternative)
web: python main_fastapi.py
```

### **render.yaml (Render.com)**
```yaml
services:
  - type: web
    name: slack-webhook-middleware
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py  # or python main_fastapi.py
    healthCheckPath: /health
```

## Environment Variables

### **Required Variables**
```env
SLACK_BOT_TOKEN=xoxb-your-token
ZOHO_DESK_API_KEY=your-zoho-key
ZOHO_DESK_ORG_ID=your-org-id
ZOHO_DESK_DOMAIN=your-domain.zohodesk.com
TRANSCRIPTION_API_KEY=your-transcription-key
```

### **Optional Variables**
```env
TRANSCRIPTION_PROVIDER=deepgram  # deepgram, assemblyai, whisper
OPENAI_API_KEY=your-openai-key   # required for whisper
PORT=5000                        # Flask default
PORT=8000                        # FastAPI default
```

## Deployment Steps

### **1. Choose Your Middleware**
- **Flask**: Use `main.py` for Zapier integration
- **FastAPI**: Use `main_fastapi.py` for direct API calls

### **2. Update Configuration**
- **Procfile**: Set the correct entry point
- **render.yaml**: Update startCommand if needed

### **3. Set Environment Variables**
- Add all required environment variables
- Ensure Slack bot token has proper permissions

### **4. Deploy**
- Push to your repository
- Deploy to your chosen platform
- Test the webhook endpoint

## Testing Deployment

### **Health Check**
```bash
curl https://your-domain.com/health
```

### **Webhook Test**
```bash
curl -X POST https://your-domain.com/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "quip",
    "file_id": "F1234567890",
    "slack_token": "xoxb-your-token"
  }'
```

## Troubleshooting

### **Common Issues**

#### **1. Port Configuration**
- **Flask**: Default port 5000
- **FastAPI**: Default port 8000
- **Deployment**: Use `$PORT` environment variable

#### **2. Entry Point Errors**
- **Error**: `can't open file '/opt/render/project/src/main.py'`
- **Solution**: Ensure `main.py` is in the root directory

#### **3. Import Errors**
- **Error**: `ModuleNotFoundError`
- **Solution**: Check that all dependencies are in requirements.txt

#### **4. Health Check Failures**
- **Error**: Health check endpoint not found
- **Solution**: Ensure the app has a `/health` endpoint

## Platform-Specific Notes

### **Render.com**
- Uses `render.yaml` for configuration
- Automatically detects Python projects
- Supports both Flask and FastAPI

### **Heroku**
- Uses `Procfile` for configuration
- Requires `requirements.txt`
- Supports both Flask and FastAPI

### **Railway**
- Uses `Procfile` or `main.py`
- Automatically detects entry point
- Supports both Flask and FastAPI

## Recommendations

### **For Zapier Integration**
- Use **Flask middleware** (`main.py`)
- Better compatibility with Zapier webhooks
- Established Canvas processing

### **For Direct API Calls**
- Use **FastAPI middleware** (`main_fastapi.py`)
- Better content type handling
- More robust error handling

### **For Development**
- Use **FastAPI** for testing
- Better debugging capabilities
- More detailed error messages

This deployment guide ensures your Slack middleware works correctly on any platform!
