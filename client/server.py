import http.server
import socketserver
import json

PORT = 8080

class fake_namenode(http.server.BaseHTTPRequestHandler):  
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_GET(self):
        content_length = int(self.headers['content-length'])
        content = self.rfile.read(content_length)
        
        
        msg = json.loads(json.loads(content.decode()))
        print(type(msg), msg)
        
        if msg["action"] == "auth":
            if msg["args"]["login"] == "Dmmc":
                response = json.dumps({"status":"ok"})
            else:
                response = json.dumps({"status":"invalid user"})
        else:
            response = json.dumps({"status":"unknown command"})
        
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())
        
        
        
with socketserver.TCPServer(("", PORT), fake_namenode) as httpd:
    print("Just another not suspicious fake namenode at the port: ", PORT)
    httpd.serve_forever()