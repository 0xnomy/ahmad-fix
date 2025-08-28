#!/usr/bin/env python3
"""
Production-ready server launcher for TikTok aging video generation.
Configures proper timeouts and settings for long-running video operations.
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Start the FastAPI server with production-ready configurations."""
    
    # Ensure we're in the backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Server configuration optimized for long-running video operations
    config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "reload_dirs": [str(backend_dir)],
        "timeout_keep_alive": 600,  # 10 minutes keep-alive
        "timeout_graceful_shutdown": 120,  # 2 minutes graceful shutdown
        "backlog": 2048,  # Connection backlog
        "limit_max_requests": 1000,  # Max requests before worker restart
        "limit_concurrency": 100,  # Max concurrent connections
        "log_level": "info",
        "access_log": True,
        "use_colors": True,
        # Worker timeout settings
        "workers": 1,  # Single worker for video processing consistency
    }
    
    print("🚀 Starting TikTok Aging Video Server...")
    print(f"📍 Server URL: http://localhost:8000")
    print(f"📖 API Docs: http://localhost:8000/docs")
    print(f"⚙️  Configuration:")
    print(f"   - Keep-alive timeout: {config['timeout_keep_alive']}s")
    print(f"   - Graceful shutdown: {config['timeout_graceful_shutdown']}s")
    print(f"   - Max concurrent requests: {config['limit_concurrency']}")
    print(f"   - Auto-reload: {config['reload']}")
    print("="*60)
    
    # Start the server
    uvicorn.run(**config)

if __name__ == "__main__":
    main()
