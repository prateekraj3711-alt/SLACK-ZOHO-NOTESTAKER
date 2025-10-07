#!/usr/bin/env python3
"""
Load configuration from config.env file
"""

import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from config.env file"""
    config_file = "config.env"
    
    if os.path.exists(config_file):
        print(f"🔧 Loading configuration from {config_file}")
        load_dotenv(config_file)
        print("✅ Configuration loaded")
    else:
        print(f"❌ Configuration file {config_file} not found")
        return False
    
    # Verify key environment variables
    required_vars = [
        "SLACK_BOT_TOKEN",
        "TRANSCRIPTION_API_KEY",
        "ZOHO_DESK_CLIENT_ID",
        "ZOHO_DESK_CLIENT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your-") or value.startswith("xoxb-your-"):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or invalid variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    success = load_config()
    if success:
        print("\n🎉 Configuration loaded successfully!")
        print("You can now start the middleware: python main.py")
    else:
        print("\n❌ Configuration loading failed")
        print("Please check your config.env file")
