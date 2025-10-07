# ⚡ Zapier Quick Start Guide

## 🚀 Get Your Zapier Integration Running in 5 Minutes

### Step 1: Deploy Your Middleware (2 minutes)

1. **Upload to GitHub**:
   ```bash
   cd slack-webhook-middleware
   git init
   git add .
   git commit -m "Deploy Slack webhook middleware"
   git remote add origin https://github.com/your-username/slack-webhook-middleware.git
   git push -u origin main
   ```

2. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Set environment variables (see below)
   - Deploy!

### Step 2: Set Environment Variables

In Render dashboard, add these environment variables:

```
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
ZOHO_DESK_API_KEY=your-zoho-desk-api-key-here
ZOHO_DESK_ORG_ID=your-zoho-org-id-here
ZOHO_DESK_DOMAIN=your-domain.zohodesk.com
TRANSCRIPTION_API_KEY=your-transcription-api-key-here
TRANSCRIPTION_PROVIDER=deepgram
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 3: Create Zapier Zap (3 minutes)

1. **Go to [zapier.com](https://zapier.com)**
2. **Click "Create Zap"**
3. **Choose Trigger**: "Slack - New File in Channel"
4. **Choose Action**: "Webhooks - POST"
5. **Configure Webhook**:
   - **URL**: `https://your-app-name.onrender.com/webhook/slack`
   - **Method**: POST
   - **Data**: Use the payload from `zapier_webhook_payload.json`

### Step 4: Test Your Integration

1. **Upload test audio file** to Slack
2. **Check Zapier execution** in dashboard
3. **Verify middleware logs** in Render
4. **Check Zoho Desk** for new ticket

## 🎯 Expected Workflow

```
1. User uploads audio file to Slack
2. Zapier detects new file
3. Zapier sends webhook to your middleware
4. Middleware downloads and transcribes audio
5. Middleware creates/updates Zoho Desk ticket
6. Middleware posts feedback to Slack
```

## ✅ Success Indicators

- **Zapier**: Shows successful webhook execution
- **Middleware**: Logs show file processing
- **Zoho Desk**: New ticket created with transcription
- **Slack**: Feedback message posted to thread

## 🔧 Troubleshooting

### Common Issues

1. **Zapier not triggering**:
   - Check Slack permissions
   - Verify channel selection
   - Test with manual upload

2. **Webhook failing**:
   - Verify middleware URL
   - Check environment variables
   - Review middleware logs

3. **No tickets created**:
   - Verify Zoho API credentials
   - Check transcription service
   - Review error logs

### Quick Tests

```bash
# Test middleware health
curl https://your-app-name.onrender.com/health

# Test webhook manually
curl -X POST https://your-app-name.onrender.com/webhook/slack \
  -H "Content-Type: application/json" \
  -d '{
    "file_info": {
      "url_private": "https://example.com/test.mp3",
      "name": "test.mp3",
      "filetype": "mp3"
    },
    "user_id": "U1234567890",
    "channel_id": "C1234567890",
    "timestamp": "1640995200.123456"
  }'
```

## 🎉 You're Done!

Your Slack audio files will now automatically:
- ✅ **Get transcribed** using AI
- ✅ **Create Zoho Desk tickets**
- ✅ **Post feedback to Slack**
- ✅ **Never process duplicates**

**No manual work required!** 🚀
