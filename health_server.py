import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server(port=8000):
    def _run():
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print("Health server listening on", port)
        server.serve_forever()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
