# 🔗 Zapier Integration Setup Guide

## Overview

This guide will help you set up Zapier to automatically trigger your Slack webhook middleware when new audio files are uploaded to Slack channels.

## 🎯 Complete Zapier Workflow

```
Slack (New File) → Zapier → Your Middleware → Transcription → Zoho Desk
```

## 📋 Prerequisites

1. **Slack Workspace** with audio file uploads
2. **Zapier Account** (free or paid)
3. **Deployed Middleware** on Render
4. **API Keys** configured in middleware

## 🚀 Step-by-Step Zapier Setup

### Step 1: Create New Zap

1. **Go to [zapier.com](https://zapier.com)**
2. **Click "Create Zap"**
3. **Name your Zap**: "Slack Audio to Zoho Desk"

### Step 2: Configure Slack Trigger

1. **Choose Trigger App**: Search for "Slack"
2. **Choose Trigger Event**: "New File in Channel"
3. **Connect Slack Account**:
   - Click "Sign in to Slack"
   - Authorize Zapier to access your Slack workspace
   - Select the workspace you want to monitor

4. **Configure Trigger Settings**:
   - **Channel**: Choose specific channel or "Any Channel"
   - **File Types**: Select "Audio" or "All Files"
   - **Test the trigger** by uploading a test audio file

### Step 3: Configure Webhook Action

1. **Choose Action App**: Search for "Webhooks"
2. **Choose Action Event**: "POST"
3. **Configure Webhook**:
   - **URL**: `https://your-app-name.onrender.com/webhook/slack`
   - **Method**: POST
   - **Data**: Configure the payload structure

### Step 4: Configure Webhook Payload

Set up the webhook payload to match your middleware expectations:

```json
{
  "file_info": {
    "url_private": "{{file_url_private}}",
    "name": "{{file_name}}",
    "filetype": "{{file_type}}"
  },
  "user_id": "{{user_id}}",
  "channel_id": "{{channel_id}}",
  "timestamp": "{{timestamp}}"
}
```

**Zapier Field Mapping**:
- `file_url_private` → `{{file_url_private}}`
- `file_name` → `{{file_name}}`
- `file_type` → `{{file_type}}`
- `user_id` → `{{user_id}}`
- `channel_id` → `{{channel_id}}`
- `timestamp` → `{{timestamp}}`

### Step 5: Test Your Zap

1. **Test the Webhook**:
   - Upload a test audio file to your Slack channel
   - Check if Zapier triggers the webhook
   - Verify your middleware receives the payload

2. **Check Middleware Logs**:
   - Go to Render dashboard
   - View your service logs
   - Look for webhook processing messages

3. **Verify Zoho Desk**:
   - Check if tickets are created
   - Verify transcriptions are added
   - Confirm Slack feedback is posted

### Step 6: Activate Your Zap

1. **Review Configuration**:
   - Double-check all settings
   - Verify webhook URL is correct
   - Confirm payload structure

2. **Turn On Zap**:
   - Click "Turn on Zap"
   - Your automation is now active!

## 🔧 Advanced Zapier Configuration

### Custom Filtering

Add filters to process only specific files:

1. **Add Filter Step**:
   - Choose "Filter by Zapier"
   - Set conditions:
     - `file_type` equals "mp3" OR "wav" OR "m4a"
     - `file_size` is greater than 0

2. **Channel Filtering**:
   - Only process files from specific channels
   - Exclude certain users or file types

### Error Handling

1. **Add Error Handling**:
   - Choose "Filter by Zapier" for error conditions
   - Set up notifications for failed webhooks

2. **Retry Logic**:
   - Configure retry attempts for failed webhooks
   - Set up alerts for persistent failures

## 📊 Monitoring Your Zap

### Zapier Dashboard

1. **View Zap History**:
   - Go to your Zap dashboard
   - Click on your Zap
   - View execution history

2. **Check Task Usage**:
   - Monitor your Zapier task usage
   - Upgrade plan if needed

### Middleware Logs

1. **Render Dashboard**:
   - Go to your service dashboard
   - View real-time logs
   - Check for processing errors

2. **Health Monitoring**:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

## 🧪 Testing Your Integration

### Test 1: Basic Webhook

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

### Test 2: Duplicate Prevention

```bash
# Send same payload twice
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

**Expected Response**:
```json
{
  "success": true,
  "message": "File already processed - skipping duplicate",
  "duplicate": true
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Zapier Not Triggering**:
   - Check Slack permissions
   - Verify channel selection
   - Test with manual file upload

2. **Webhook Failing**:
   - Verify middleware URL is correct
   - Check middleware logs for errors
   - Test webhook manually

3. **Transcription Failing**:
   - Verify API keys are set
   - Check transcription service status
   - Review error logs

4. **Zoho Desk Integration Failing**:
   - Verify Zoho API credentials
   - Check organization ID and domain
   - Test API access manually

### Debug Steps

1. **Check Zapier Logs**:
   - Go to Zapier dashboard
   - View execution history
   - Check for error messages

2. **Check Middleware Logs**:
   - Go to Render dashboard
   - View service logs
   - Look for processing errors

3. **Test Components Individually**:
   - Test Slack trigger manually
   - Test webhook endpoint directly
   - Test transcription service
   - Test Zoho Desk API

## 📈 Optimization Tips

### Performance

1. **Batch Processing**:
   - Process multiple files efficiently
   - Use async processing for better performance

2. **Error Recovery**:
   - Set up retry logic for failed requests
   - Implement fallback mechanisms

### Cost Management

1. **Zapier Tasks**:
   - Monitor task usage
   - Optimize trigger conditions
   - Use filters to reduce unnecessary triggers

2. **API Costs**:
   - Monitor transcription API usage
   - Optimize file processing
   - Use efficient transcription providers

## 🎯 Best Practices

### Zapier Configuration

1. **Specific Triggers**:
   - Use specific channels when possible
   - Filter by file types
   - Exclude unnecessary files

2. **Error Handling**:
   - Set up error notifications
   - Implement retry logic
   - Monitor for failures

### Middleware Configuration

1. **Environment Variables**:
   - Use secure API key storage
   - Rotate keys regularly
   - Monitor key usage

2. **Monitoring**:
   - Set up health checks
   - Monitor processing times
   - Track success rates

## 🚀 Production Deployment

### Pre-Launch Checklist

- [ ] Zapier Zap configured and tested
- [ ] Middleware deployed and accessible
- [ ] All API keys configured
- [ ] Health endpoints working
- [ ] Test with real audio files
- [ ] Verify Zoho Desk integration
- [ ] Check Slack feedback posting
- [ ] Monitor for errors

### Go-Live Steps

1. **Activate Zap**:
   - Turn on your Zapier automation
   - Monitor first few executions
   - Check for any issues

2. **Monitor Performance**:
   - Watch processing times
   - Check error rates
   - Verify ticket creation

3. **User Training**:
   - Inform team about new workflow
   - Provide usage guidelines
   - Set up support channels

## 📞 Support

### Getting Help

1. **Zapier Support**:
   - Check Zapier documentation
   - Contact Zapier support
   - Use Zapier community forums

2. **Middleware Support**:
   - Check Render logs
   - Review error messages
   - Test components individually

3. **API Support**:
   - Check service status pages
   - Verify API credentials
   - Test API endpoints directly

---

## 🎉 **Your Zapier Integration is Ready!**

Once configured, your system will automatically:
- ✅ **Detect new audio files** in Slack
- ✅ **Process them through Zapier** webhook
- ✅ **Transcribe audio** using AI
- ✅ **Create Zoho Desk tickets** automatically
- ✅ **Post feedback** back to Slack
- ✅ **Prevent duplicates** automatically

**No manual intervention required!** 🚀
