import http.server
import socketserver
import json
import os
import socket
import threading

ok = "<3"
notok = "</3"

PORT = 5000
FTP_PORT = 1338
BUFF_SIZE = 1024

SERVER_FOLDER = "server_storage"

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
   
# socket implementation
def send_file_to_client():
    file = "file.txt"
    path = "{}/{}".format(SERVER_FOLDER, file)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    host = ""
    
    s.bind((host, FTP_PORT))
    s.listen()
    conn, addr = s.accept()
    
    f = open(path, 'rb')
    l = f.read(BUFF_SIZE)
    while (l):
        conn.send(l)
        l = f.read(BUFF_SIZE)
    f.close()
    conn.close()
    s.close()

def read_file():
    file = "file.txt"
    path = "{}/{}".format(SERVER_FOLDER, file)
    
    if os.path.exists(path):
        res = {"status": ok,
               "args" : {"error" : ""}}
    else:
        res = {"status": notok,
               "args" : {"error" : "No such file!"}}
        
    return json.dumps(res)

def write_file():
    return json.dumps({"status" : ok,
                       "args": {"error" : ""}}) 
            
# socket implementation
def read_file_from_client():
    file = "uploaded.txt"
    path = "{}/{}".format(SERVER_FOLDER, file)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    host = ""
    
    s.bind((host, FTP_PORT))
    s.listen()
    conn, addr = s.accept()
    
    f = open(path, 'wb')
    l = conn.recv(BUFF_SIZE)
    while (l):
        f.write(l)
        l = conn.recv(BUFF_SIZE)
    f.close()
    conn.close()
    s.close()   
        
    
    

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
        
        msg = json.loads(content.decode())
        print(msg)
        
        if msg["command"] == "auth":
            # if cridentials are valid then let user in
            if msg["args"]["login"] == "Dmmc":
                response = for_main()
            # if cridentials are not valid - send notok
            else:
                response = no()
                
        elif msg["command"] == "new_user":
            # if cridentials are valid then create new user
            if msg["args"]["login"] != "Dmmc":
                # here you initialize the FS for new user and return size
                response = for_main()
            # if cridentials are not valid - send notok >:)
            else:
                response = no()
                
        elif msg["command"] == "read_dir":
            # listing directory content here
            response = read_dir()
            
        elif msg["command"] == "open_dir":
            # checkign if such directory exist so user can go into it
            response = open_dir()
            
        elif msg["command"] == "make_dir":
            # Checking if we can create the directory
            response = make_dir()
            
        elif msg["command"] == "del_dir":
            # Checking if target folder exists
            response = del_dir()

        elif msg["command"] == "create_file":
            # Checking if we can create s@app.route("/login", methods = ["POST", "GET"])uch a file
            response = create_file()
            
        elif msg["command"] == "delete_file":
            # Checking if we can delete such a file
            response = delete_file()
            
        elif msg["command"] == "info_file":
            # Checking if we can get info about a file
            response = info_file()
            
        elif msg["command"] == "copy_file":
            # Checking if we can successfully copy the file into destination directory
            response = copy_file()
            
        elif msg["command"] == "move_file":
            # Checking if we can successfully move the file into destination directory
            response = move_file()
            
        elif msg["command"] == "read_file":
            # Checking if such file exists
            response = read_file()
            
            #send_file_thread = threading.Thread(target=send_file_to_client, daemon=True)
            #send_file_thread.start()
            
        elif msg["command"] == "write_file":
            # Checking if client can upload such file
            response = write_file()
            
            #read_file_thread = threading.Thread(target=read_file_from_client, daemon=True)
            #read_file_thread.start()
        
        elif msg["command"] == "receive_file":
            
            
        else:
            response = no()
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())
        
with socketserver.TCPServer(("", PORT), fake_namenode) as httpd:
    print("Just another not suspicious fake namenode at the port: ", PORT)
    httpd.serve_forever()