import os
import json
import socket
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer


HTTP_PORT = 3000
SOCKET_PORT = 5000
DATA_FILE = os.path.join("storage", "data.json")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        elif self.path == "/message.html":
            self.path = "/message.html"
        elif self.path.startswith("/static"):
            self.path = self.path[1:]
        else:
            self.path = "/error.html"
        
        super().do_GET()

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            fields = self.parse_form_data(post_data)

            
            if not self.validate_form(fields):
                self.send_error(400, "Bad Request: Missing required fields or invalid data")
                return

            self.send_to_socket(fields)
            self.send_response(302)  
            self.send_header("Location", "/")
            self.end_headers()

    def parse_form_data(self, data):
        decoded = data.decode("utf-8")
        return dict(item.split("=") for item in decoded.split("&"))

    def validate_form(self, fields):
        required_fields = ["username", "message"]
        if not all(field in fields for field in required_fields):
            return False
        if any(char in fields.get("username", "") for char in ['<', '>', '{', '}', '"']):
            return False
        return True

    def send_to_socket(self, fields):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(fields).encode("utf-8"), ("127.0.0.1", SOCKET_PORT))

def socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(("127.0.0.1", SOCKET_PORT))
        print(f"Socket server running on port {SOCKET_PORT}")

        while True:
            data, _ = server.recvfrom(1024)
            message = json.loads(data.decode("utf-8"))

            timestamp = datetime.now().isoformat()
            entry = {timestamp: message}

            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
            else:
                existing_data = {}

            existing_data.update(entry)

            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, indent=4, ensure_ascii=False)


def http_server():
    os.chdir(STATIC_DIR)
    handler = CustomHTTPRequestHandler
    httpd = HTTPServer(("127.0.0.1", HTTP_PORT), handler)
    print(f"HTTP server running on port {HTTP_PORT}")
    httpd.serve_forever()


def main():
    threading.Thread(target=http_server, daemon=True).start()
    threading.Thread(target=socket_server, daemon=True).start()

    try:
        while True:
            pass  
    except KeyboardInterrupt:
        print("\nShutting down servers...")

if __name__ == "__main__":
    main()
