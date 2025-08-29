import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

def create_combined_app():

    # Add backend directory to Python path so we can import main.py
    backend_dir = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_dir))

    # Import the existing FastAPI app from main.py
    try:
        from main import app
        print("✅ Successfully imported backend app from main.py")
    except ImportError as e:
        print(f"❌ Error importing backend: {e}")
        sys.exit(1)

    # Get the frontend directory path
    frontend_dir = Path(__file__).parent / "frontend"

    if not frontend_dir.exists():
        print("❌ Error: frontend directory not found!")
        print(f"Expected at: {frontend_dir.absolute()}")
        sys.exit(1)

    # Ensure required directories exist
    print("📁 Ensuring required directories exist...")
    project_root = Path(__file__).parent
    os.makedirs(project_root / 'generated', exist_ok=True)
    os.makedirs(project_root / 'uploads', exist_ok=True)
    print("✅ All directories created successfully")

    # Add frontend static file serving to the existing FastAPI app
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Mount frontend static files (this should be before other mounts)
    try:
        app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")
        print("✅ Frontend static files mounted at /frontend")
        print(f"📁 Frontend directory: {frontend_dir.absolute()}")
    except Exception as e:
        print(f"❌ Error mounting frontend static files: {e}")
        print(f"Expected frontend directory: {frontend_dir.absolute()}")
        
    # Also mount the debug test file
    try:
        debug_file = Path(__file__).parent / "test_audio_debug.html"
        if debug_file.exists():
            print(f"✅ Debug test file available at /debug-audio")
    except Exception as e:
        print(f"Note: Debug test file not available: {e}")

    # Add root route to serve index.html
    @app.get("/")
    async def serve_frontend():
        """Serve the main frontend page"""
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            print(f"📄 Serving frontend index.html from {index_path}")
            return FileResponse(str(index_path), media_type='text/html')
        else:
            print(f"❌ Frontend index.html not found at {index_path}")
            return {"error": "Frontend not found"}

    # Add route to serve index.html at /app for direct access
    @app.get("/app")
    async def serve_app_page():
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path), media_type='text/html')
        else:
            return {"error": "Frontend not found"}

    # Add route to serve debug test file
    @app.get("/debug-audio")
    async def serve_debug_audio():
        debug_path = Path(__file__).parent / "test_audio_debug.html"
        if debug_path.exists():
            return FileResponse(str(debug_path), media_type='text/html')
        else:
            return {"error": "Debug test file not found"}

    print("✅ Frontend routes configured")
    return app

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)  # Wait for server to start
    try:
        webbrowser.open('http://localhost:8000')
        print("🌐 Opened browser at http://localhost:8000")
    except Exception as e:
        print(f"Could not open browser: {e}")

def main():
    import uvicorn

    print("🚀 Starting Combined TikTok Aging App Server...")
    print("=" * 60)

    try:
        # Create the combined app
        combined_app = create_combined_app()

        print("🎯 Combined Server Configuration:")
        print(f"   📍 Server URL: http://localhost:8000")
        print(f"   🌐 Frontend: http://localhost:8000 (or /app)")
        print(f"   📖 API Docs: http://localhost:8000/docs")
        print(f"   🎬 Generated Videos: http://localhost:8000/generated/")
        print(f"   🖼️  Generated Images: http://localhost:8000/images/")
        print(f"   📁 Frontend Files: Served from /frontend directory")
        print(f"   🔧 Auto-reload: Manual reload required")
        print(f"   ⏹️  Press Ctrl+C to stop")
        print("=" * 60)

        # Open browser in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        # Start the server with proper configuration
        print("🌟 Server starting...")
        uvicorn.run(
            combined_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            use_colors=True
        )

    except KeyboardInterrupt:
        print("\n🛑 Combined server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting combined server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

