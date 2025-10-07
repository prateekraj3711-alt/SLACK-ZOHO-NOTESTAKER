"""
Setup script for Slack Zapier Middleware
Validates configuration and provides deployment instructions
"""

import os
import sys
from pathlib import Path

def check_required_files():
    """Check if all required files are present"""
    required_files = [
        'slack_webhook_middleware.py',
        'requirements.txt',
        'render.yaml',
        'Procfile',
        'runtime.txt',
        'zapier_webhook_payload.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files found")
    return True

def check_environment_template():
    """Check if environment template exists"""
    if Path('env.example').exists():
        print("✅ Environment template found")
        return True
    else:
        print("⚠️  Environment template not found")
        return False

def show_deployment_instructions():
    """Show deployment instructions"""
    print("\n🚀 Deployment Instructions")
    print("=" * 50)
    
    print("\n📋 Step 1: Upload to GitHub")
    print("1. Initialize git repository:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Deploy Slack Zapier middleware'")
    print("   git remote add origin https://github.com/your-username/slack-zapier-middleware.git")
    print("   git push -u origin main")
    
    print("\n📋 Step 2: Deploy to Render")
    print("1. Go to https://render.com")
    print("2. Create new Web Service")
    print("3. Connect your GitHub repository")
    print("4. Set environment variables:")
    print("   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here")
    print("   ZOHO_DESK_API_KEY=your-zoho-desk-api-key-here")
    print("   ZOHO_DESK_ORG_ID=your-zoho-org-id-here")
    print("   ZOHO_DESK_DOMAIN=your-domain.zohodesk.com")
    print("   TRANSCRIPTION_API_KEY=your-transcription-api-key-here")
    print("   TRANSCRIPTION_PROVIDER=deepgram")
    print("   OPENAI_API_KEY=your-openai-api-key-here")
    print("5. Deploy!")
    
    print("\n📋 Step 3: Configure Zapier")
    print("1. Go to https://zapier.com")
    print("2. Create new Zap")
    print("3. Choose Trigger: 'Slack - New File in Channel'")
    print("4. Choose Action: 'Webhooks - POST'")
    print("5. Configure webhook URL: https://your-app-name.onrender.com/webhook/slack")
    print("6. Use payload from zapier_webhook_payload.json")
    print("7. Test and activate!")
    
    print("\n📋 Step 4: Test Your Integration")
    print("1. Upload test audio file to Slack")
    print("2. Check Zapier execution in dashboard")
    print("3. Verify ticket creation in Zoho Desk")
    print("4. Check Slack feedback message")

def show_documentation():
    """Show available documentation"""
    print("\n📚 Documentation")
    print("=" * 30)
    
    docs = [
        ("README.md", "Complete system overview"),
        ("ZAPIER_QUICK_START.md", "5-minute quick start"),
        ("ZAPIER_SETUP_GUIDE.md", "Complete Zapier setup"),
        ("RENDER_DEPLOYMENT_GUIDE.md", "Detailed deployment"),
        ("DUPLICATE_PREVENTION_GUIDE.md", "Duplicate prevention")
    ]
    
    for doc, description in docs:
        if Path(doc).exists():
            print(f"✅ {doc} - {description}")
        else:
            print(f"❌ {doc} - Missing")

def main():
    """Main setup function"""
    print("🔗 Slack Zapier Middleware Setup")
    print("=" * 40)
    
    # Check files
    if not check_required_files():
        print("\n❌ Setup failed - missing required files")
        return False
    
    check_environment_template()
    
    # Show documentation
    show_documentation()
    
    # Show deployment instructions
    show_deployment_instructions()
    
    print("\n🎯 Your Slack Zapier Middleware is ready for deployment!")
    print("\n💡 Tips:")
    print("- Read README.md for complete overview")
    print("- Use ZAPIER_QUICK_START.md for fast setup")
    print("- Check RENDER_DEPLOYMENT_GUIDE.md for detailed deployment")
    print("- Test with test_zapier_integration.py after deployment")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)
