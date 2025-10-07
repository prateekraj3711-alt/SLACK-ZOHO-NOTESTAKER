@echo off
echo 🚀 Slack Zapier Middleware Deployment Script
echo ==========================================

echo.
echo 📁 Current directory: %CD%
echo.

echo 🔍 Checking for required files...
if not exist "slack_webhook_middleware.py" (
    echo ❌ slack_webhook_middleware.py not found
    exit /b 1
)
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found
    exit /b 1
)
if not exist "render.yaml" (
    echo ❌ render.yaml not found
    exit /b 1
)

echo ✅ All required files found
echo.

echo 🚀 Ready for deployment!
echo.
echo 📋 Next steps:
echo 1. Upload this folder to GitHub
echo 2. Go to https://render.com
echo 3. Create new Web Service
echo 4. Connect your GitHub repository
echo 5. Set environment variables
echo 6. Deploy!
echo.
echo 📖 For detailed instructions, see:
echo    - README.md
echo    - RENDER_DEPLOYMENT_GUIDE.md
echo    - ZAPIER_QUICK_START.md
echo.
echo 🎯 Your Slack Zapier Middleware is ready!
pause
