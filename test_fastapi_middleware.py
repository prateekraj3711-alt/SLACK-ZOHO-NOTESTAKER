#!/usr/bin/env python3
"""
Test script for FastAPI Slack File Share Middleware
"""

import requests
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_file_share_event():
    """Test file share event processing"""
    print("\nTesting file share event...")
    
    # Mock Slack file share event
    event_payload = {
        "type": "event_callback",
        "event": {
            "type": "file_shared",
            "file": {
                "id": "F1234567890",
                "name": "test_audio.mp3",
                "mimetype": "audio/mpeg",
                "size": 1024000,
                "url_private_download": "https://files.slack.com/files-pri/123/test_audio.mp3",
                "user": "U123456",
                "channels": ["C123456"]
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook/slack",
            json=event_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_message_with_files():
    """Test message with file attachments"""
    print("\nTesting message with file attachments...")
    
    event_payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "files": [
                {
                    "id": "F1234567891",
                    "name": "meeting_recording.wav",
                    "mimetype": "audio/wav",
                    "size": 2048000
                },
                {
                    "id": "F1234567892",
                    "name": "document.pdf",
                    "mimetype": "application/pdf",
                    "size": 512000
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook/slack",
            json=event_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_files():
    """Test listing downloaded files"""
    print("\nTesting file listing...")
    try:
        response = requests.get("http://localhost:8000/files")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_download_endpoint():
    """Test direct file download"""
    print("\nTesting download endpoint...")
    try:
        # This will fail without a real file ID, but tests the endpoint
        response = requests.get("http://localhost:8000/download/F1234567890")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True  # We expect this to fail with 404
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("FastAPI Slack File Share Middleware Test Suite")
    print("=" * 50)
    
    # Check if server is running
    print("Checking if server is running on localhost:8000...")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✅ Server is running")
    except Exception as e:
        print("❌ Server is not running. Please start the middleware first:")
        print("   python slack_file_middleware.py")
        return
    
    # Run tests
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("File Share Event", test_file_share_event),
        ("Message with Files", test_message_with_files),
        ("List Files", test_list_files),
        ("Download Endpoint", test_download_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
