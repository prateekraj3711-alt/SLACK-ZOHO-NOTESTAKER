#!/usr/bin/env python3
"""
Main entry point for the FastAPI Slack Middleware
This file serves as the entry point for deployment platforms
"""

import os
import uvicorn
from slack_file_middleware import app

if __name__ == "__main__":
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=port)
