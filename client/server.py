import http.server
import socketserver
import json

ok = "ok"
notok = "notok"

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
        print(msg)
        
        if msg["action"] == "auth":
            # if cridentials are valid then let user in
            if msg["args"]["login"] == "Dmmc":
                response = json.dumps({"status" : ok, "args" : {"free_space" : 1337}})
            # if cridentials are not valid - send notok
            else:
                response = json.dumps({"status" : notok})
                
        elif msg["action"] == "new_user":
            # if cridentials are valid then create new user
            if msg["args"]["login"] != "Dmmc":
                # here you initialize the FS for new user and return size
                response = json.dumps({"status" : ok, "args" : {"free_space" : 1338}})
            # if cridentials are not valid - send notok >:)
            else:
                response = json.dumps({"status" : notok})
                
        else:
            response = json.dumps({"status" : notok})
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())
        
        
        
with socketserver.TCPServer(("", PORT), fake_namenode) as httpd:
    print("Just another not suspicious fake namenode at the port: ", PORT)
    httpd.serve_forever()