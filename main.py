#!/usr/bin/env python3
"""
Main entry point for the Slack Webhook Middleware
This file serves as the entry point for deployment platforms
"""

import os
import sys
from dotenv import load_dotenv

# Load configuration from config.env
config_file = "config.env"
if os.path.exists(config_file):
    print(f"🔧 Loading configuration from {config_file}")
    load_dotenv(config_file)
    print("✅ Configuration loaded")
else:
    print(f"⚠️  Configuration file {config_file} not found, using environment variables")

from slack_webhook_middleware import app

if __name__ == "__main__":
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 Starting Slack middleware on port {port}")
    # Run the Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
