"""
Keep Alive Script - Simple HTTP Server
يحافظ على نشاط البوت على Replit
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import sys
import time

class PingHandler(BaseHTTPRequestHandler):
    """معالج HTTP requests بسيط"""
    
    def do_GET(self):
        """معالج GET requests"""
        if self.path in ['/', '/ping']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(b'pong')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """إخفاء logs الافتراضية"""
        pass

def run_server():
    """تشغيل HTTP server بسيط"""
    try:
        print("[keep_alive] Starting HTTP server on 0.0.0.0:5000...", flush=True)
        sys.stdout.flush()
        
        server = HTTPServer(('0.0.0.0', 5000), PingHandler)
        server.allow_reuse_address = True
        
        print("[keep_alive] ✅ HTTP server started successfully on port 5000!", flush=True)
        sys.stdout.flush()
        
        # Serve forever
        server.serve_forever()
    except OSError as e:
        print(f"[keep_alive] ❌ Error on port 5000: {e}", flush=True)
        try:
            print(f"[keep_alive] Trying port 3000...", flush=True)
            server = HTTPServer(('0.0.0.0', 3000), PingHandler)
            server.allow_reuse_address = True
            print("[keep_alive] ✅ HTTP server started on port 3000!", flush=True)
            server.serve_forever()
        except Exception as e2:
            print(f"[keep_alive] ❌ Failed on port 3000: {e2}", flush=True)
    except Exception as e:
        print(f"[keep_alive] ❌ Server error: {e}", flush=True)
        sys.stdout.flush()

def keep_alive():
    """
    يشغل HTTP server في thread منفصل للحفاظ على البوت حياً
    Runs HTTP server in a separate thread to keep bot alive
    """
    try:
        print("[keep_alive] Initializing keep-alive server...", flush=True)
        sys.stdout.flush()
        
        # Start server in daemon thread
        t = Thread(target=run_server, daemon=False)  # Not daemon - important!
        t.daemon = False
        t.start()
        
        print("✅ Keep-alive server initialized!", flush=True)
        sys.stdout.flush()
        
        # Small delay to ensure server starts
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ Failed to start keep-alive server: {e}", flush=True)
        sys.stdout.flush()
