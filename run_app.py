import sys
import os
import threading
import webbrowser
import time
from app import app

def open_browser():
    """Waits for the server to start, then opens the default web browser."""
    # A short delay to ensure the Flask server has bound to the port
    time.sleep(2)
    print("Opening browser at http://127.0.0.1:5000...")
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Start the browser opening logic in a separate background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the Flask application
    # We disable debug mode for the standalone app to prevent double-starts and extra console noise
    print("Starting Anki Helper server...")
    app.run(port=5000, debug=False)
