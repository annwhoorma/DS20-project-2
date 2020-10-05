import http.server
import socketserver
import json

ok = "<3"
notok = "</3"

PORT = 8080

def for_main():
    return json.dumps({"status" : ok,
                       "args" : {"free_space" : 1337,
                                 "cur_dir" : "/root/jonata",
                                 "error" : ""}})
def no():
    return json.dumps({"status" : notok,
                       "error" : ""})

def read_dir():
    return json.dumps({"status" : ok,
                       "args" : {"dirs" : [{ "name" : "maman", "type" : "dir"},
                                           { "name" : "another_dir", "type" : "dir"},
                                           { "name" : "meme.png", "type" : "file"},
                                           { "name" : "video.mp4", "type" : "file"}],
                                 "error" : ""}})

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
                response = for_main()
            # if cridentials are not valid - send notok
            else:
                response = no()
                
        elif msg["action"] == "new_user":
            # if cridentials are valid then create new user
            if msg["args"]["login"] != "Dmmc":
                # here you initialize the FS for new user and return size
                response = for_main()
            # if cridentials are not valid - send notok >:)
            else:
                response = no()
                
        elif msg["action"] == "read_dir":
            # changing directiry here
            response = read_dir()
            
        else:
            response = no()
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())
        
        
        
with socketserver.TCPServer(("", PORT), fake_namenode) as httpd:
    print("Just another not suspicious fake namenode at the port: ", PORT)
    httpd.serve_forever()