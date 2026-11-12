# Local receiver for Tripo Studio exports: accepts POST /<name> (a .glb/.fbx/.zip body) from the
# studio.tripo3d.ai page and saves it under OUT. Run: python3 receiver.py OUT  (port 8765)
import http.server, os, pathlib, re, sys
OUT = pathlib.Path(sys.argv[1]); ORIGIN = "https://studio.tripo3d.ai"
class H(http.server.BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()
    def do_GET(self):   # serves setup scripts from $RECEIVER_SCRIPTS (only to the Studio page)
        name = self.path.strip("/")
        src = pathlib.Path(os.environ.get("RECEIVER_SCRIPTS", "/nonexistent")) / name
        if self.headers.get("Origin") != ORIGIN or not re.fullmatch(r"[a-z0-9-]+\.js", name) or not src.exists():
            self.send_response(404); self.cors(); self.end_headers(); return
        body = src.read_bytes()
        self.send_response(200); self.cors(); self.send_header("Content-Type", "text/javascript"); self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        name = self.path.strip("/")
        if self.headers.get("Origin") != ORIGIN or not re.fullmatch(r"[a-z0-9-]+\.(glb|fbx|zip)", name):
            self.send_response(403); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        (OUT / name).write_bytes(self.rfile.read(n))
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(f"saved {name} {n}".encode())
        print("saved", name, n, flush=True)
http.server.HTTPServer(("127.0.0.1", 8765), H).serve_forever()
