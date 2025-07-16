#!/usr/bin/env python3
"""
Raspberry Pi Hub Backend Startup Script
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def main():
    """Start the FastAPI hub backend"""
    
    # Configuration
    host = os.getenv('HUB_HOST', '0.0.0.0')
    port = int(os.getenv('HUB_PORT', 3001))
    reload = os.getenv('HUB_RELOAD', 'true').lower() == 'true'
    log_level = os.getenv('HUB_LOG_LEVEL', 'debug')
    
    print(f"Starting Security Hub Backend on {host}:{port}")
    print(f"Reload: {reload}, Log Level: {log_level}")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()