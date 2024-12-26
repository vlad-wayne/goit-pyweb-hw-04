import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime

os.chdir(r"D:\user\vladi\.vscode\goit-pyweb-hw-04")
print("Current working directory:", os.getcwd())
print("Static files path:", os.path.abspath("static"))


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html_page("index.html")
        elif self.path == "/message.html":
            self.send_html_page("message.html")
        elif self.path == "/error.html":
            self.send_html_page("error.html")
        elif self.path.startswith("/static/"):
            self.send_static_file(self.path[7:])
        else:
            self.send_error(404, "Page not found")

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            form_data = post_data.decode().split('&')
            username = form_data[0].split('=')[1]
            message = form_data[1].split('=')[1]

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_address = ('localhost', 5000)
            message_data = f"{username}|{message}"
            sock.sendto(message_data.encode(), server_address)
            sock.close()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Form submitted successfully!')

    def send_html_page(self, filename):
        try:
            with open(f"templates/{filename}", "r") as f:
                html_content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
        except FileNotFoundError:
            self.send_error(404, "File not found")

    def send_static_file(self, filename):
        try:
            with open(f"static/{filename}", "rb") as f:
                content = f.read()
            
            if filename.endswith(".css"):
                content_type = 'text/css'
            elif filename.endswith(".png"):
                content_type = 'image/png'
            else:
                content_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")


def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 5000))
    print("Socket server started on port 5000")

    while True:
        data, address = sock.recvfrom(4096)
        if data:
            username, message = data.decode().split('|')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            new_message = {timestamp: {"username": username, "message": message}}

            try:
                with open("storage/data.json", "r") as f:
                    messages = json.load(f)
            except FileNotFoundError:
                messages = {}

            messages.update(new_message)
            
            with open("storage/data.json", "w") as f:
                json.dump(messages, f, indent=4)
            
            print(f"Message saved: {new_message}")


def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("HTTP server started on port 3000")
    httpd.serve_forever()


if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    socket_thread = threading.Thread(target=socket_server)
    socket_thread.start()
