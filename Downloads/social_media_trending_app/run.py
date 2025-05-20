import os
import platform
import sys

def run_app():
    """
    Run the Flask application with the appropriate WSGI server based on platform
    """
    system = platform.system()
    port = int(os.environ.get("PORT", 8008))
    
    if system == 'Windows':
        # Use waitress on Windows
        try:
            from waitress import serve
            from app import app
            print(f"Starting waitress server on http://localhost:{port}")
            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            print("Waitress is not installed. Please install it with 'pip install waitress'")
            sys.exit(1)
    else:
        # Use gunicorn on Linux/Unix systems (like Render)
        try:
            import gunicorn
            # We don't actually run gunicorn here - we just check it's installed
            # Then we use os.system to run it with the appropriate arguments
            cmd = f"gunicorn app:app --bind 0.0.0.0:{port}"
            print(f"Starting gunicorn server with command: {cmd}")
            os.system(cmd)
        except ImportError:
            print("Gunicorn is not installed. Please install it with 'pip install gunicorn'")
            sys.exit(1)

if __name__ == "__main__":
    run_app()
