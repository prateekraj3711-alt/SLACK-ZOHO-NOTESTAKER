#!/usr/bin/env python3
"""
Main entry point for the Slack Webhook Middleware
This file serves as the entry point for deployment platforms
"""

import os
import sys
from slack_webhook_middleware import app

if __name__ == "__main__":
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
