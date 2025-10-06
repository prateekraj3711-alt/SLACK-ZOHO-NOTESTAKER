# Slack Voice Middleware - Deployment Guide

## 🚀 Quick Deploy to Render

### Step 1: Upload to GitHub

1. Create a new GitHub repository
2. Upload all files from this folder to the repository
3. Make sure to include:
   - `main.py`
   - `requirements.txt`
   - `render.yaml`
   - `README.md`
   - `.gitignore`

### Step 2: Deploy to Render

1. Go to [Render.com](https://render.com)
2. Sign up/Login with your GitHub account
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Select the repository with your code
6. Configure the service:
   - **Name**: `slack-voice-middleware`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### Step 3: Set Environment Variables

In Render dashboard, go to your service → Environment:

- `DEEPGRAM_API_KEY`: `3e43c56e7bda92b003f12bcb46ae94dcd2c1b8f4`
- `ZAPIER_WEBHOOK_URL`: Your Zapier webhook URL

### Step 4: Deploy

1. Click "Deploy" in Render
2. Wait for deployment to complete
3. Copy your service URL (e.g., `https://slack-voice-middleware.onrender.com`)

## 🔧 Zapier Configuration

### Step 1: Create Zapier Workflow

1. Go to [Zapier.com](https://zapier.com)
2. Create a new Zap
3. **Trigger**: "New File in Channel" (Slack)
4. **Action**: "Webhooks by Zapier" → "POST"

### Step 2: Configure Slack Trigger

1. Select your Slack workspace
2. Choose the channel to monitor
3. Set up authentication if needed

### Step 3: Configure Webhook Action

1. **URL**: Your Render service URL + `/slack-webhook``
2. **Method**: POST
3. **Data**: Map Slack fields to webhook:
   - `file_url`: `{{Url Private Download}}`
   - `slack_token`: Your Slack bot token
   - `user_email`: `{{User Email}}`
   - `user_phone`: `{{User Phone}}`
   - `user_name`: `{{User Name}}`
   - `channel_name`: `{{Channel Name}}`

### Step 4: Test and Activate

1. Test the Zap with a sample file
2. Activate the Zap
3. Upload a voice message to test the full flow

## 🎯 Testing Your Deployment

### Test Health Check
```bash
curl https://your-service-url.onrender.com/
```

### Test Status
```bash
curl https://your-service-url.onrender.com/status
```

### Test Webhook (with sample data)
```bash
curl -X POST https://your-service-url.onrender.com/slack-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://files.slack.com/files-pri/...",
    "slack_token": "xoxb-your-token",
    "user_email": "test@example.com",
    "user_phone": "+1234567890",
    "user_name": "Test User",
    "channel_name": "general"
  }'
```

## 🔍 Troubleshooting

### Common Issues

1. **"Missing required fields"**
   - Check Zapier webhook configuration
   - Ensure all required fields are mapped

2. **"Failed to download audio"**
   - Verify Slack bot token has file access
   - Check if file URL is accessible

3. **"Transcription failed"**
   - Verify Deepgram API key
   - Check audio file format and size

4. **"Failed to send to Zapier"**
   - Verify Zapier webhook URL
   - Check Zapier webhook configuration

### Logs and Monitoring

- Check Render service logs for detailed error messages
- Use `/status` endpoint to monitor system health
- Monitor processed files count for duplicate prevention

## 🎉 Success!

Once deployed, your Slack voice messages will be automatically transcribed and sent to Zapier for further processing!
