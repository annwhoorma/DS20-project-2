import json
import os
import subprocess
import shutil
import socket
from multiprocessing import Process
from http.server import HTTPServer, BaseHTTPRequestHandler

# tudu - tokenizer for paths, test info in linux OS, agreement on naming in JSONs commands

# testing - curl -X GET -d
# '{"command": "file_delete", "args": {"user": "/Users/admin/Desktop/ds/", "path": "test.txt"}}'
# localhost:1337

HTTP_PORT = 1337
FTP_PORT = 7331

########### inner functions ###########
def check_path(message):
    root = message["args"]["user"]
    path = message["args"]["path"]

    return os.path.exists(root + path)

def check_root(root):
    return os.path.exists(root)

def json_read(message):
    json_object = json.loads(message.decode("utf-8"))
    return json_object

########### functions for external commands ###########
def init_user(message):
    root = message["args"]["user"]
    try:
        os.mkdir('{}'.format(root))
        res = {"status": "OK", "message": "Root directory successfully initialized"}
    except FileExistsError:
        shutil.rmtree('{}'.format(root), ignore_errors=True)
        os.mkdir('{}'.format(root))
        res = {"status": "OK", "message": "Root directory was reinitialized and cleaned"}
    return json.dumps(res)

def create_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path
    directory_to_put = local_path[:local_path.rfind("/")]

    if not(check_path(message)) and os.path.exists(directory_to_put):
        os.system('touch ' + local_path)
        res = {"status": "OK", "message": "File creation succeed"}
    elif check_path(message):
        res = {"status": "Failed", "message": "File creation did not succeed - file with this name already exists."}
    else:
        res = {"status": "Failed", "message": "File creation did not succeed - no such directory to put a file."}

    return json.dumps(res)

def delete_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    if check_path(message):
        os.remove(local_path)
        res = {"status": "OK", "message": "File deletion succeed"}
    else:
        res = {"status": "Failed", "message": "File deletion did not succeed - no such file."}
    return json.dumps(res)

def move_file(message):
    root = message["args"]["user"]
    src = message["args"]["src"]
    dst = message["args"]["dst"]

    if os.path.exists(root+src) and not (os.path.exists(root+dst)):
        os.system('mv ' + root + src + ' ' + root + dst)
        res = {"status": "OK", "message": "File moving succeed"}
    elif os.path.exists(root+dst):
        res = {"status": "Failed", "message": "File moving did not succeed - destination path already exists."}
    else:
        res = {"status": "Failed", "message": "File moving did not succeed - no such source path."}
    return json.dumps(res)

def info_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    if check_path(message):
        size = subprocess.check_output('stat -c %s ' + local_path, shell=True).decode("utf-8").strip()
        status = subprocess.check_output('stat -c %z ' + local_path, shell=True).decode("utf-8").strip()
        i_node_name = subprocess.check_output('stat -c %i ' + local_path, shell=True).decode("utf-8").strip()

        res = {"status": "OK", "message": "File info retrieved successfully:",
                "args": {"size": "{}".format(size), "file_status": "{}".format(status),
                "i-node": "i_node_name", "path": "{}".format(local_path)}}
    else:
        res = {"status": "Failed", "message": "File info retrieval did not succeed - no such file."}
    return json.dumps(res)

def copy_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    ind = path.rfind(".")
    new_path = path[:ind]
    print(new_path)
    ex = path.split("/")[-1].split(".")[-1]
    copy_num = int(subprocess.check_output('ls ' + root + new_path + '* | wc -l', shell=True).decode(
        "utf-8").strip())

    if ind == -1:
        new_name = path + '_copy{}'.format(
            str(copy_num))
    else:
        new_name = path[:ind] + '_copy{}.'.format(
            str(copy_num)) + str(ex)

    if check_path(message):
        os.system(
            'cp ' + str(root) + path + ' ' + root + new_name)
        res = {"status": "OK", "message": "File was copied successfully",
                "args": {"filename": new_name.split("s/")[-1]}}
    else:
        res = {"status": "Failed", "message": "File copying did not succeed - no such file."}

    return json.dumps(res)

def create_directory(message):
    root = message["args"]["user"]
    path = message["args"]["path"]

    if not(check_root(root)):
        res = {"status": "Failed",
        "message": "Directory creating did not succeed - root directory is not initialized"}
    else:
        if not(check_path(message)):
            local_path = root + path
            try:
                os.mkdir(local_path)
                res = {"status": "OK", "message": "New directory was successfelly created"}
            except FileNotFoundError:
                res = {"status": "Failed", "message": "Directory creating did not succeed - invalid input format"}
        else:
            res = {"status": "Failed",
            "message": "Directory creating did not succeed - required path already exists."}

    return json.dumps(res)

def delete_directory(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    if not(check_root(root)):
        res = {"status": "Failed",
        "message": "Directory deleting did not succeed - root directory is not initialized"}
    else:
        if path == "":
            res = {"status": "Failed", "message":
            "Directory creating did not succeed - cannot delete root directory"}
        elif check_path(message):
            shutil.rmtree('{}'.format(local_path), ignore_errors=True)
            res = {"status": "OK", "message": "Required directory was successfelly deleted"}
        else:
            res = {"status": "Failed", "message":
            "Directory creating did not succeed - no such directory"}
    return json.dumps(res)

def list_directory(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    if not(check_root(root)):
        res = {"status": "Failed",
        "message": "Directory listing did not succeed - root directory is not initialized"}
    else:
        if not(check_path(message)):
            res = {"status": "Failed", "message":
            "Directory listing did not succeed - no such directory"}
        else:
            listing = subprocess.check_output('ls ' + local_path, shell=True).decode("utf-8").strip().split("\n")
            res = {"status": "OK",
            "message": "Required directory was successfelly listed", "args": {"data": "{}".format(listing)}}
    return json.dumps(res)

def send_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host = ""
    s.bind((host, FTP_PORT))
    s.listen(5)

    conn, addr = s.accept()
    if os.path.exists(root + path):
        f = open(root + path, 'rb')
        l = f.read(1024)
        while (l):
            conn.send(l)
            l = f.read(1024)
        f.close()
        res = {"status": "OK", "message": "Filed was successfuly sent"}
    else:
        res = {"status": "Failed", "message": "No such file"}
    conn.close()
    s.close()
    return json.dumps(res)

def read_file(message):
    process = Process(target=send_file(message))
    process.start()
    return json.dumbs({"status": "OK", "message": "Uploading..."})

def receive_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    filename = root + path

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ""
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, FTP_PORT))
    s.listen(5)
    conn, addr = s.accept()

    with open('{}'.format(filename), 'wb') as f:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)
    f.close()
    conn.close()
    s.close()

def write_file(message):
    process = Process(target=receive_file(message))
    process.start()
    res = {"status": "OK", "message": "Uploading..."}
    return json.dumps(res)

########### Class for HTTP handler ###########
class Http_handler(BaseHTTPRequestHandler):
    def do_GET(self):

        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        message = json_read(data)
        command = message['command']

        if command == "init":
            res = init_user(message)
        elif command == "create_dir":
            res = create_directory(message)
        elif command == "list_dir":
            res = list_directory(message)
        elif command == "delete_dir":
            res = delete_directory(message)
        elif command == "file_info":
            res = info_file(message)
        elif command == "file_delete":
            res = delete_file(message)
        elif command == "file_copy":
            res = copy_file(message)
        elif command == "file_create":
            res = create_file(message)
        elif command == "file_move":
            res = move_file(message)
        elif command == "read_file":
            res = read_file(message)
        elif command == "write_file":
            res = write_file(message)
        else:
            res = json.dumps({"status": "Failed", "message": "Invalid command"})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(res, "utf-8"))

if __name__ == "__main__":
    server_address = ('', HTTP_PORT)
    httpd = HTTPServer(server_address, Http_handler)
    httpd.serve_forever()
