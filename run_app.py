import sys
import os
import threading
import webbrowser
import time
import socket
from app import app

def get_port():
    try:
        # Tenta usar a porta 5001 primeiro (para manter o link fixo)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 5001))
        s.close()
        return 5001
    except OSError:
        # Se a 5001 já estiver em uso, busca qualquer porta livre
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        return port

def open_browser(port):
    """Waits for the server to start, then opens the default web browser."""
    # A short delay to ensure the Flask server has bound to the port
    time.sleep(2)
    print(f"Opening browser at http://127.0.0.1:{port}...")
    webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == "__main__":
    # Get an available port
    port = get_port()
    
    # Start the browser opening logic in a separate background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Run the Flask application
    # We disable debug mode for the standalone app to prevent double-starts and extra console noise
    print("Starting Anki Helper server...")
    app.run(port=port, debug=False)
