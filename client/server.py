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
                       "args": {"error" : ""}})

def read_dir():
    return json.dumps({"status" : ok,
                       "args" : {"dirs" : [{ "name" : "maman", "type" : "dir"},
                                           { "name" : "another_dir", "type" : "dir"},
                                           { "name" : "meme.png", "type" : "file"},
                                           { "name" : "video.mp4", "type" : "file"}],
                                 "error" : ""}})

def open_dir():
    return json.dumps({"status" : ok,
                       "args": {"error" : ""}})
    
def make_dir():
    return json.dumps({"status" : notok,
                       "args": {"error" : "Such folder doesnot exist"}})
    
def del_dir():
    return json.dumps({"status" : notok,
                       "args": {"error" : "Suck folder doesnot exist"}})
    
def create_file():
    return json.dumps({"status" : notok,
                       "args": {"error" : "Not enough space for the file!"}})
    
def delete_file():
    return json.dumps({"status" : ok,
                       "args": {"error" : ""}})
    
def info_file():
    return json.dumps({"status" : ok,
                       "args" : {"size" : 1337,
                                 "node_id" : 2,
                                 "modified" : "12.12.12",
                                 "accessed" : "11.11.11",
                                 "error" : ""}})
    
def copy_file():
    return json.dumps({"status" : notok,
                       "args": {"error" : "No such file!"}})
    
def move_file():
    return json.dumps({"status" : ok,
                       "args": {"error" : ""}})

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
            # listing directory content here
            response = read_dir()
            
        elif msg["action"] == "open_dir":
            # checkign if such directory exist so user can go into it
            response = open_dir()
            
        elif msg["action"] == "make_dir":
            # Checking if we can create the directory
            response = make_dir()
            
        elif msg["action"] == "del_dir":
            # Checking if target folder exists
            response = del_dir()

        elif msg["action"] == "create_file":
            # Checking if we can create such a file
            response = create_file()
            
        elif msg["action"] == "delete_file":
            # Checking if we can create such a file
            response = delete_file()
            
        elif msg["action"] == "info_file":
            # Checking if we can get info about a file
            response = info_file()
            
        elif msg["action"] == "copy_file":
            # Checking if we can successfully copy the file into destination directory
            response = copy_file()
            
        elif msg["action"] == "move_file":
            # Checking if we can successfully copy the file into destination directory
            response = move_file()
            
        else:
            response = no()
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())
        
with socketserver.TCPServer(("", PORT), fake_namenode) as httpd:
    print("Just another not suspicious fake namenode at the port: ", PORT)
    httpd.serve_forever()