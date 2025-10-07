#!/usr/bin/env python3
"""
Test current setup with available files
"""

import os
import requests
import json

def test_available_files():
    """Test with files that are actually accessible"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing available files...")
    
    try:
        # Get list of available files
        response = requests.get(
            "https://slack.com/api/files.list?limit=10", 
            headers=headers, 
            timeout=10
        )
        data = response.json()
        
        if data.get("ok"):
            files = data.get("files", [])
            print(f"✅ Found {len(files)} files")
            
            if files:
                # Test with the first available file
                test_file = files[0]
                file_id = test_file.get('id')
                file_type = test_file.get('filetype')
                file_name = test_file.get('name')
                
                print(f"   Testing with: {file_name} ({file_type}) - {file_id}")
                
                # Test files.info for this file
                try:
                    info_response = requests.get(
                        f"https://slack.com/api/files.info?file={file_id}",
                        headers=headers,
                        timeout=10
                    )
                    info_data = info_response.json()
                    
                    if info_data.get("ok"):
                        print("✅ files.info: Success")
                        file_info = info_data.get("file", {})
                        print(f"   File Name: {file_info.get('name')}")
                        print(f"   File Type: {file_info.get('filetype')}")
                        print(f"   MIME Type: {file_info.get('mimetype')}")
                        print(f"   Size: {file_info.get('size')} bytes")
                        
                        # Check if it's an audio file
                        if file_info.get('filetype') in ['mp3', 'mp4', 'wav', 'm4a', 'ogg']:
                            print("✅ This is an audio file - ready for processing")
                        elif file_info.get('filetype') == 'quip':
                            print("✅ This is a Canvas file - may need special handling")
                        else:
                            print(f"ℹ️  This is a {file_info.get('filetype')} file")
                            
                    else:
                        print(f"❌ files.info: {info_data.get('error')}")
                        
                except Exception as e:
                    print(f"❌ files.info: Error - {e}")
            else:
                print("ℹ️  No files found in workspace")
                print("   Try uploading a test file to Slack first")
                
        else:
            print(f"❌ files.list: {data.get('error')}")
            
    except Exception as e:
        print(f"❌ files.list: Error - {e}")

def test_webhook_endpoint():
    """Test the webhook endpoint"""
    print("\n🔍 Testing webhook endpoint...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: Working")
        else:
            print(f"❌ Health endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint: Error - {e}")
        print("   Make sure the middleware is running: python main.py")

def test_audio_processing():
    """Test audio processing capabilities"""
    print("\n🔍 Testing audio processing...")
    
    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg: Working")
        else:
            print("❌ FFmpeg: Not working")
    except Exception as e:
        print(f"❌ FFmpeg: Error - {e}")
    
    # Check Deepgram API
    api_key = os.getenv("TRANSCRIPTION_API_KEY")
    if api_key and not api_key.startswith("your-"):
        print("✅ Deepgram API Key: Set")
    else:
        print("❌ Deepgram API Key: Not set")

def main():
    """Main test function"""
    print("🚀 Current Setup Test")
    print("=" * 50)
    
    # Test available files
    test_available_files()
    
    # Test webhook endpoint
    test_webhook_endpoint()
    
    # Test audio processing
    test_audio_processing()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print("If files are accessible, the middleware should work")
    print("If no files are found, upload a test file to Slack first")
    print("Make sure the middleware is running: python main.py")

if __name__ == "__main__":
    main()
