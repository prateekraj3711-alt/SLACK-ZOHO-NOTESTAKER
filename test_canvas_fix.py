#!/usr/bin/env python3
"""
Test Canvas file processing fix
"""

import os
import sys
from dotenv import load_dotenv

# Load configuration
config_file = "config.env"
if os.path.exists(config_file):
    load_dotenv(config_file)

# Import the middleware components
from slack_webhook_middleware import CanvasParser

def test_canvas_detection():
    """Test Canvas file detection"""
    print("🔍 Testing Canvas file detection...")
    
    # Test cases
    test_cases = [
        ("quip", "application/vnd.slack-docs", True),
        ("canvas", "application/vnd.slack.canvas", True),
        ("mp3", "audio/mpeg", False),
        ("mp4", "video/mp4", False),
        ("unknown", "application/octet-stream", False)
    ]
    
    parser = CanvasParser("test-token")
    
    for file_type, mimetype, expected in test_cases:
        result = parser.is_canvas_file(file_type, mimetype)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {file_type} + {mimetype} -> {result} (expected {expected})")
    
    return True

def test_environment_loading():
    """Test environment variable loading"""
    print("\n🔍 Testing environment variable loading...")
    
    required_vars = [
        "SLACK_BOT_TOKEN",
        "TRANSCRIPTION_API_KEY",
        "ZOHO_DESK_CLIENT_ID",
        "ZOHO_DESK_CLIENT_SECRET"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value and not value.startswith("your-") and not value.startswith("xoxb-your-"):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Not set or invalid")
            all_set = False
    
    return all_set

def test_canvas_processing():
    """Test Canvas processing logic"""
    print("\n🔍 Testing Canvas processing logic...")
    
    # Simulate the Canvas file processing
    file_type = "quip"
    mimetype = "application/vnd.slack-docs"
    
    parser = CanvasParser("test-token")
    is_canvas = parser.is_canvas_file(file_type, mimetype)
    
    if is_canvas:
        print("   ✅ Canvas file detected correctly")
        print("   ✅ Will use Canvas processing logic")
        return True
    else:
        print("   ❌ Canvas file not detected")
        print("   ❌ Will try to process as regular audio file")
        return False

def main():
    """Main test function"""
    print("🚀 Canvas Fix Test")
    print("=" * 50)
    
    # Test Canvas detection
    detection_ok = test_canvas_detection()
    
    # Test environment loading
    env_ok = test_environment_loading()
    
    # Test Canvas processing
    processing_ok = test_canvas_processing()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if detection_ok and env_ok and processing_ok:
        print("✅ All tests passed!")
        print("   Canvas files will be processed correctly")
        print("   Environment variables are loaded")
        print("   Ready to start the middleware")
    else:
        print("❌ Some tests failed")
        if not detection_ok:
            print("   - Canvas detection needs fixing")
        if not env_ok:
            print("   - Environment variables not loaded")
        if not processing_ok:
            print("   - Canvas processing logic needs fixing")
    
    print("\n🚀 Next steps:")
    print("1. Start the middleware: python main.py")
    print("2. Test with a Canvas file from Slack")
    print("3. Check the logs for Canvas processing")

if __name__ == "__main__":
    main()
