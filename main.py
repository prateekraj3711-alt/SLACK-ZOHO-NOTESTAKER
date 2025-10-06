#!/usr/bin/env python3
"""
Main entry point for Slack Webhook Middleware
This file imports and runs the main middleware application
"""

import os
from slack_webhook_middleware import app

if __name__ == '__main__':
    # Run the Flask application
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
