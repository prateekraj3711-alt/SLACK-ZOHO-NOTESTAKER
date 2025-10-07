#!/usr/bin/env python3
"""
Startup script for FastAPI Slack File Share Middleware
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    required_vars = ['SLACK_BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSet them in your .env file or environment")
        return False
    
    return True

def create_download_directory():
    """Create download directory if it doesn't exist"""
    download_dir = os.getenv('SLACK_DOWNLOAD_DIR', 'downloads')
    Path(download_dir).mkdir(exist_ok=True)
    print(f"📁 Download directory: {download_dir}")

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI Slack File Share Middleware...")
    
    # Get configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    reload = os.getenv('RELOAD', 'false').lower() == 'true'
    
    print(f"🌐 Server will be available at: http://{host}:{port}")
    print(f"📋 Health check: http://{host}:{port}/health")
    print(f"🔗 Webhook endpoint: http://{host}:{port}/webhook/slack")
    
    if reload:
        print("🔄 Auto-reload enabled")
    
    # Start server
    try:
        import uvicorn
        uvicorn.run(
            "slack_file_middleware:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("FastAPI Slack File Share Middleware")
    print("=" * 40)
    
    # Check requirements
    print("🔍 Checking requirements...")
    if not check_requirements():
        sys.exit(1)
    print("✅ All required packages are installed")
    
    # Check environment
    print("\n🔍 Checking environment...")
    if not check_environment():
        sys.exit(1)
    print("✅ Environment variables are set")
    
    # Create download directory
    print("\n📁 Setting up download directory...")
    create_download_directory()
    
    # Start server
    print("\n🚀 Starting server...")
    start_server()

if __name__ == "__main__":
    main()
