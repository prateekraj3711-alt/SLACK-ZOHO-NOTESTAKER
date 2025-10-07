#!/usr/bin/env python3
"""
Test Canvas API access and permissions
"""

import os
import requests
import json

def test_slack_api_methods():
    """Test various Slack API methods to see what's available"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test different API methods
    methods_to_test = [
        "auth.test",
        "files.info", 
        "files.list",
        "canvas.info",
        "conversations.history",
        "users.info"
    ]
    
    print("🔍 Testing Slack API methods...")
    
    for method in methods_to_test:
        try:
            if method == "auth.test":
                url = f"https://slack.com/api/{method}"
            elif method == "files.info":
                url = f"https://slack.com/api/{method}?file=F09HRKKGYEB"
            elif method == "files.list":
                url = f"https://slack.com/api/{method}?limit=1"
            elif method == "canvas.info":
                url = f"https://slack.com/api/{method}?canvas_id=F09HRKKGYEB"
            elif method == "conversations.history":
                url = f"https://slack.com/api/{method}?channel=C09HRKL86R5&limit=1"
            elif method == "users.info":
                url = f"https://slack.com/api/{method}?user=U09HRKLA3KR"
            else:
                url = f"https://slack.com/api/{method}"
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("ok"):
                print(f"✅ {method}: Success")
            else:
                error = data.get("error", "unknown")
                print(f"❌ {method}: {error}")
                
        except Exception as e:
            print(f"❌ {method}: Error - {e}")

def test_canvas_alternative():
    """Test alternative approaches to Canvas data"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing Canvas alternatives...")
    
    # Test files.info for the Canvas file
    try:
        response = requests.get(
            "https://slack.com/api/files.info?file=F09HRKKGYEB", 
            headers=headers, 
            timeout=10
        )
        data = response.json()
        
        if data.get("ok"):
            file_info = data.get("file", {})
            print("✅ files.info: Success")
            print(f"   File ID: {file_info.get('id')}")
            print(f"   File Name: {file_info.get('name')}")
            print(f"   File Type: {file_info.get('filetype')}")
            print(f"   MIME Type: {file_info.get('mimetype')}")
            print(f"   Download URL: {file_info.get('url_private_download')}")
            
            # Check if it's a Canvas file
            if file_info.get('filetype') == 'quip':
                print("✅ This is a Canvas file (quip type)")
                print("   Note: Canvas files may not support direct audio extraction")
                print("   Consider using files.list to find audio files in the channel")
            else:
                print("❌ This is not a Canvas file")
        else:
            print(f"❌ files.info: {data.get('error')}")
            
    except Exception as e:
        print(f"❌ files.info: Error - {e}")

def test_files_list():
    """Test files.list to see what files are available"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing files.list...")
    
    try:
        response = requests.get(
            "https://slack.com/api/files.list?limit=10", 
            headers=headers, 
            timeout=10
        )
        data = response.json()
        
        if data.get("ok"):
            files = data.get("files", [])
            print(f"✅ files.list: Success - Found {len(files)} files")
            
            for file in files[:5]:  # Show first 5 files
                print(f"   - {file.get('name')} ({file.get('filetype')}) - {file.get('id')}")
        else:
            print(f"❌ files.list: {data.get('error')}")
            
    except Exception as e:
        print(f"❌ files.list: Error - {e}")

def main():
    """Main test function"""
    print("🚀 Canvas API Test Script")
    print("=" * 50)
    
    # Test Slack API methods
    test_slack_api_methods()
    
    # Test Canvas alternatives
    test_canvas_alternative()
    
    # Test files list
    test_files_list()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    print("If canvas.info is not available, the system will use files.info instead")
    print("Canvas files (quip type) may not support direct audio extraction")
    print("Consider using files.list to find audio files in the channel")

if __name__ == "__main__":
    main()
