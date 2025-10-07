#!/usr/bin/env python3
"""
Quick Fix Script for Slack Middleware Issues
This script helps diagnose and fix common issues
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "SLACK_BOT_TOKEN",
        "TRANSCRIPTION_API_KEY",
        "ZOHO_DESK_ACCESS_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your-") or value.startswith("xoxb-your-"):
            missing_vars.append(var)
            print(f"❌ {var}: Not set or using default value")
        else:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed and working"""
    print("\n🔍 Checking FFmpeg installation...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is installed and working")
            return True
        else:
            print("❌ FFmpeg is not working properly")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg is not installed")
        print("Run: .\\setup_ffmpeg_windows.ps1")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking FFmpeg: {e}")
        return False

def test_slack_api():
    """Test Slack API connection"""
    print("\n🔍 Testing Slack API connection...")
    
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token or token.startswith("xoxb-your-"):
        print("❌ SLACK_BOT_TOKEN not set or using default value")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://slack.com/api/auth.test", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Slack API connection successful")
                print(f"   Bot: {data.get('user')}")
                print(f"   Team: {data.get('team')}")
                return True
            else:
                print(f"❌ Slack API error: {data.get('error')}")
                return False
        else:
            print(f"❌ Slack API HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Slack API connection failed: {e}")
        return False

def test_deepgram_api():
    """Test Deepgram API connection"""
    print("\n🔍 Testing Deepgram API connection...")
    
    api_key = os.getenv("TRANSCRIPTION_API_KEY")
    if not api_key or api_key.startswith("your-"):
        print("❌ TRANSCRIPTION_API_KEY not set or using default value")
        return False
    
    try:
        headers = {"Authorization": f"Token {api_key}"}
        response = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Deepgram API connection successful")
            return True
        elif response.status_code == 401:
            print("❌ Deepgram API authentication failed - check your API key")
            return False
        else:
            print(f"❌ Deepgram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Deepgram API connection failed: {e}")
        return False

def test_canvas_api():
    """Test Canvas API access"""
    print("\n🔍 Testing Canvas API access...")
    
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token or token.startswith("xoxb-your-"):
        print("❌ SLACK_BOT_TOKEN not set or using default value")
        return False
    
    # Test with a sample canvas ID (you can replace this with a real one)
    canvas_id = "F09HRKKGYEB"  # Replace with your actual canvas ID
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"https://slack.com/api/canvas.info?canvas_id={canvas_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Canvas API access successful")
                canvas_data = data.get("canvas", {})
                print(f"   Canvas ID: {canvas_data.get('id')}")
                print(f"   Blocks: {len(canvas_data.get('blocks', []))}")
                return True
            else:
                print(f"❌ Canvas API error: {data.get('error')}")
                return False
        else:
            print(f"❌ Canvas API HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Canvas API connection failed: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\n🔧 Creating .env file...")
    
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists("env.example"):
        try:
            with open("env.example", "r") as f:
                content = f.read()
            
            with open(".env", "w") as f:
                f.write(content)
            
            print("✅ .env file created from env.example")
            print("⚠️  Please edit .env file with your actual values")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ env.example file not found")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Slack Middleware Quick Fix Script")
    print("=" * 50)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Test API connections
    slack_ok = test_slack_api()
    deepgram_ok = test_deepgram_api()
    canvas_ok = test_canvas_api()
    
    # Create .env file if needed
    if not env_ok:
        create_env_file()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"FFmpeg Installation: {'✅' if ffmpeg_ok else '❌'}")
    print(f"Slack API Connection: {'✅' if slack_ok else '❌'}")
    print(f"Deepgram API Connection: {'✅' if deepgram_ok else '❌'}")
    print(f"Canvas API Access: {'✅' if canvas_ok else '❌'}")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS")
    print("=" * 50)
    
    if not env_ok:
        print("1. Set your environment variables in .env file")
        print("2. Get your API keys from the respective services")
    
    if not ffmpeg_ok:
        print("3. Install FFmpeg: .\\setup_ffmpeg_windows.ps1")
    
    if not slack_ok:
        print("4. Check your Slack bot token and permissions")
    
    if not deepgram_ok:
        print("5. Get a valid Deepgram API key from console.deepgram.com")
    
    if not canvas_ok:
        print("6. Ensure your bot has files:read scope")
    
    # Overall status
    all_ok = env_ok and ffmpeg_ok and slack_ok and deepgram_ok and canvas_ok
    
    if all_ok:
        print("\n🎉 All checks passed! Your middleware should work correctly.")
    else:
        print("\n⚠️  Some issues found. Please fix them before running the middleware.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
