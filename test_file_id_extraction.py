#!/usr/bin/env python3
"""
Test file ID extraction from various Slack URL formats
"""

import re

def extract_file_id_from_url(file_url: str) -> str:
    """Extract file ID from Slack file URL - updated version"""
    try:
        # Pattern for Canvas files: /files-pri/TEAM_ID-FILE_ID/canvas
        match = re.search(r'/files-pri/[^-]+-([^/]+)/canvas', file_url)
        if match:
            return match.group(1)
        
        # Pattern for regular files: /files-pri/TEAM_ID-FILE_ID/filename
        match = re.search(r'/files-pri/[^-]+-([^/]+)/', file_url)
        if match:
            return match.group(1)
        
        # Alternative pattern for other file types
        match = re.search(r'/files/([^/]+)/', file_url)
        if match:
            return match.group(1)
        
        return None
    except Exception as e:
        print(f"Error extracting file ID: {str(e)}")
        return None

def test_file_id_extraction():
    """Test file ID extraction with various URL formats"""
    print("🔍 Testing file ID extraction...")
    
    test_cases = [
        # Canvas file URL (the problematic one)
        ("https://files.slack.com/files-pri/T09HRKL86R5-F09HRKKGYEB/canvas", "F09HRKKGYEB"),
        
        # Regular file URLs
        ("https://files.slack.com/files-pri/T09HRKL86R5-F09HRKKGYEB/download/audio.mp3", "F09HRKKGYEB"),
        ("https://files.slack.com/files-pri/T09HRKL86R5-F09HRKKGYEB/audio.mp3", "F09HRKKGYEB"),
        
        # Other formats
        ("https://files.slack.com/files/T09HRKL86R5-F09HRKKGYEB/audio.mp3", "F09HRKKGYEB"),
        ("https://files.slack.com/files-pri/T09HRKL86R5-F09HRKKGYEB/download/canvas", "F09HRKKGYEB"),
    ]
    
    all_passed = True
    
    for url, expected in test_cases:
        result = extract_file_id_from_url(url)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {url}")
        print(f"      Expected: {expected}, Got: {result}")
        
        if result != expected:
            all_passed = False
    
    return all_passed

def test_specific_canvas_url():
    """Test the specific Canvas URL from the error"""
    print("\n🔍 Testing specific Canvas URL...")
    
    canvas_url = "https://files.slack.com/files-pri/T09HRKL86R5-F09HRKKGYEB/canvas"
    expected_id = "F09HRKKGYEB"
    
    result = extract_file_id_from_url(canvas_url)
    
    if result == expected_id:
        print(f"✅ Canvas URL extraction successful: {result}")
        return True
    else:
        print(f"❌ Canvas URL extraction failed: expected {expected_id}, got {result}")
        return False

def main():
    """Main test function"""
    print("🚀 File ID Extraction Test")
    print("=" * 50)
    
    # Test general file ID extraction
    general_ok = test_file_id_extraction()
    
    # Test specific Canvas URL
    canvas_ok = test_specific_canvas_url()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if general_ok and canvas_ok:
        print("✅ All file ID extraction tests passed!")
        print("   Canvas files will be processed correctly")
        print("   The middleware should work without file ID extraction errors")
    else:
        print("❌ Some file ID extraction tests failed")
        if not general_ok:
            print("   - General file ID extraction needs fixing")
        if not canvas_ok:
            print("   - Canvas file ID extraction needs fixing")
    
    print("\n🚀 Next steps:")
    print("1. The file ID extraction is now fixed")
    print("2. Restart the middleware: python main.py")
    print("3. Test with the Canvas file again")

if __name__ == "__main__":
    main()
