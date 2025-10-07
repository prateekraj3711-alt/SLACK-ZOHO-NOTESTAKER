#!/usr/bin/env python3
"""
Test Deepgram API connection
"""

import os
import requests
import json

def test_deepgram_api():
    """Test Deepgram API with the current API key"""
    api_key = os.getenv("TRANSCRIPTION_API_KEY")
    
    print(f"🔍 Testing Deepgram API...")
    print(f"API Key: {api_key[:10]}..." if api_key else "❌ No API key found")
    
    if not api_key:
        print("❌ TRANSCRIPTION_API_KEY not set")
        return False
    
    try:
        # Test Deepgram projects endpoint
        headers = {"Authorization": f"Token {api_key}"}
        response = requests.get("https://api.deepgram.com/v1/projects", headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Deepgram API connection successful")
            return True
        elif response.status_code == 401:
            print("❌ Deepgram API authentication failed")
            print("   Check your API key at: https://console.deepgram.com/")
            return False
        else:
            print(f"❌ Deepgram API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Deepgram API connection failed: {e}")
        return False

def test_deepgram_listen():
    """Test Deepgram listen endpoint with a simple audio file"""
    api_key = os.getenv("TRANSCRIPTION_API_KEY")
    
    if not api_key:
        print("❌ TRANSCRIPTION_API_KEY not set")
        return False
    
    print("\n🔍 Testing Deepgram listen endpoint...")
    
    try:
        # Create a simple test audio file (silence)
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Create 1 second of silence using FFmpeg
            result = subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=duration=1', 
                '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                temp_file.name, '-y'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Test audio file created")
                
                # Test Deepgram listen endpoint
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "audio/wav"
                }
                
                with open(temp_file.name, 'rb') as audio_file:
                    response = requests.post(
                        "https://api.deepgram.com/v1/listen",
                        headers=headers,
                        data=audio_file,
                        timeout=10
                    )
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print("✅ Deepgram listen endpoint working")
                    return True
                else:
                    print(f"❌ Deepgram listen error: {response.status_code}")
                    return False
            else:
                print("❌ Failed to create test audio file")
                return False
                
    except Exception as e:
        print(f"❌ Deepgram listen test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Deepgram API Test")
    print("=" * 50)
    
    # Test API connection
    api_ok = test_deepgram_api()
    
    # Test listen endpoint
    if api_ok:
        listen_ok = test_deepgram_listen()
    else:
        listen_ok = False
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if api_ok and listen_ok:
        print("✅ Deepgram API is working correctly")
    elif api_ok:
        print("⚠️  Deepgram API connection works, but listen endpoint has issues")
    else:
        print("❌ Deepgram API is not working")
        print("   Check your API key at: https://console.deepgram.com/")
        print("   Make sure the key has the correct permissions")

if __name__ == "__main__":
    main()
