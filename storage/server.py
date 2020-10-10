import json
import os
import subprocess
import shutil
import socket
from multiprocessing import Process
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import random
# tudu - tokenizer for paths, test info in linux OS, agreement on naming in JSONs commands

# testing - curl -X GET -d
# '{"command": "file_delete", "args": {"user": "/Users/admin/Desktop/ds/", "path": "test.txt"}}'
# localhost:1337

MASTER_IP = ''
#node_ip = requests.get('https://api.ipify.org').text
#NODE_IP = os.environ.get('MY_IP')
NAMESERVER_IP = "192.168.1.52"
NODE_IP = "192.168.1.52"
#NAMESERVER_IP = os.environ.get('NAMENODE')
NAMESERVER_PORT = 5000
NAME_SERVER_ADDRESS = 'http://' + NAMESERVER_IP + ':' + str(NAMESERVER_PORT)
SLAVES = []
HTTP_PORT = 1400
FTP_PORT = 1421

TIME_STAMP = 0

########### functions for nodes' communication ###########
def init_node():
    global MASTER_IP
    global NODE_IP
    message = {"command": "init_node",
    "args": {"node": NODE_IP} }

    response = json.loads(requests.get(NAME_SERVER_ADDRESS, json=message).text)
    # format to response:
        # status: OK, Failed
        # args:
            # master: "MASTER_IP"
            # node_status: new, old
    if response['status'] == "OK":
        MASTER_IP = response["args"]["master"]
        print("MASTER_IP: ", MASTER_IP)
        init_fs(response['args']['node_status'])
    else:
        print("-----------Retrying to initialize node-----------")
        init_node()
        # ? should I do it like this?

def init_fs(node_status):
    if node_status == 'new':
        request_fs()
        print("------------Successfully initialized------------")
    else:
        ## вернуть -> os.system("rm -r */")
        print("------------Successfully initialized------------")

def share_slaves():
    global SLAVES

    res = ""
    slaves_tmp = ""
    for item in SLAVES:
        slaves_tmp += " "
        slaves_tmp += item

    if slaves_tmp != "":
        slaves_tmp = slaves_tmp[1:]
        print(slaves_tmp)
    else:
        slaves_tmp = "none"
    res = {"command": "get_slaves", "args": {"slaves": slaves_tmp}}

    try:
        requests.get(NAME_SERVER_ADDRESS, json=res, timeout=1)
    except requests.exceptions.ReadTimeout:
        pass
    except requests.exceptions.ConnectionError:
        pass

def get_slaves():
    global SLAVES
    global NAME_SERVER_ADDRESS
    message = {"command": "share_slaves"}
    response = json.loads(requests.get(NAME_SERVER_ADDRESS, json=message).text)

    if response["args"]["slaves"] != "none":
        SLAVES = response["args"]["slaves"].split(" ")

def update_time_stamp():
    global TIME_STAMP
    TIME_STAMP = time.time()

def slave_command_distribution(message):
    print(SLAVES)
    for slave in SLAVES:
        try:
            slave_address = 'http://' + slave + ':' + str(HTTP_PORT)
            response = json.loads(
                requests.get(slave_address, json=message, timeout=1).text)
        except requests.exceptions.ReadTimeout:
            SLAVES.remove(slave)
        except requests.exceptions.ConnectionError:
            SLAVES.remove(slave)

def change_master(message):
    global MASTER_IP
    MASTER_IP = message["args"]["node_ip"]

def request_fs():
    message = {"command": "send_fs", "args": {"ip": NODE_IP}}
    message = json.dumps(message)
    master_address = 'http://' + MASTER_IP + ':' + str(PORT_http)
    response = json.loads(requests.get(master_address, json=message, timeout=0.000001).text)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ""
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, FTP_PORT))
    s.listen(5)
    conn, addr = s.accept()
    with open('fs.zip', 'wb') as f:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            f.write(data)

        f.close()
        conn.close()
        s.close()

        os.system("unzip bckp.zip")
        os.system("rm bckp.zip")



def send_fs(message):
    node = message["args"]["ip"]
    os.system(
        "zip -r fs.zip $(ls) -x \"storageserver.py\" \"README.md\" \".zip\" \"requirements.txt\" \"Dockerfile\" \"docker-compose.yml\" ")
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((node, PORT_ftp_send))

    filepath = 'fs.zip'
    f = open(filepath, 'rb')
    l = f.read(1024)
    while (l):
        s.send(l)
        l = f.read(1024)
    f.close()
    s.close()
    os.system("rm fs.zip")
    return json.dumps({"status": "OK"})

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
    available_size = subprocess.check_output("df -Ph . | tail -1 | awk '{print $4}'", shell=True)
    try:
        os.mkdir('{}'.format(root))
        res = {"status": "OK", "message": "Root directory successfully initialized",
        "size": "{}".format(available_size.decode("utf-8").strip())}
    except FileExistsError:
        shutil.rmtree('{}'.format(root), ignore_errors=True)
        os.mkdir('{}'.format(root))
        res = {"status": "OK",
        "message": "Root directory was reinitialized and cleaned",
        "size": "{}".format(available_size.decode("utf-8").strip())}
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
                "i-node": "{}".format(i_node_name), "path": "{}".format(local_path)}}
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
            "Directory deleting did not succeed - cannot delete root directory"}
        elif check_path(message):
            shutil.rmtree('{}'.format(local_path), ignore_errors=True)
            res = {"status": "OK", "message": "Required directory was successfelly deleted"}
        else:
            res = {"status": "Failed", "message":
            "Directory deleting did not succeed - no such directory"}
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

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((node, PORT_ftp_send))

    f = open(filename, 'rb')
    l = f.read(1024)
    while (l):
        s.send(l)
        l = f.read(1024)
    f.close()
    s.close()


def write_file(message):
    process = Process(target=receive_file(message))
    process.start()
    res = {"status": "OK", "message": "Uploading..."}
    return json.dumps(res)

########### Class for HTTP handler ###########
class Http_handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global MASTER_IP
        global NODE_IP
        res = ''
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        message = json_read(data)
        command = message['command']

        if command == "init":
            res = init_user(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "create_dir":
            res = create_directory(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "file_copy":
            res = copy_file(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "file_create":
            res = create_file(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "list_dir":
            res = list_directory(message)
        elif command == "delete_dir":
            res = delete_directory(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "file_move":
            res = move_file(message)
            if leader_ip == node_ip:
                slave_command_distribution(message)
        elif command == "read_file":
            res = read_file(message)
        elif command == "file_info":
            res = info_file(message)
        elif command == "file_delete":
            res = delete_file(message)
            if MASTER_IP == NODE_IP:
                slave_command_distribution(message)
        elif command == "write_file":
            res = write_file(message)
        elif command == "<3":
            update_time_stamp()
            res = json.dumps({"status": "OK", "message": "Master is alive"})
        elif command == "change_master":
            change_master(message)
        elif command == "send_fs":
            res = send_fs(message)
        else:
            res = json.dumps({"status": "Failed", "message": "Invalid command"})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(res, "utf-8"))

########### Classes for HeartBeat protocol ###########
class Master():
    def __init__(self):
        thread = threading.Thread(target=self.start, args=())
        thread.daemon = True
        thread.start()

    def start(self):
        global MASTER_IP
        while NODE_IP == MASTER_IP:
            get_slaves()
            message = {"command": "<3"}
            print(SLAVES)
            try:
                requests.get(NAME_SERVER_ADDRESS, json=message, timeout=1)
            except Exception:
                pass

            for slave in SLAVES:
                try:
                    response = json.loads(requests.get('http://' + slave + ':' + str(HTTP_PORT), json=message, timeout=1).text)
                except requests.exceptions.ReadTimeout:
                    if SLAVES != []:

                        SLAVES.remove(slave)
                        print("-----------Node {} is dead-----------".format(slave))
                except requests.exceptions.ConnectionError:
                    if SLAVES != []:

                        SLAVES.remove(slave)
                        print("-----------Node {} is dead-----------".format(slave))

            share_slaves()

        # in case node changed the status, it should be reload as a slave
        new_slave = Slave()



class Slave():
    def __init__(self):
        thread = threading.Thread(target=self.start, args=())
        thread.daemon = True
        thread.start()

    def start(self):
        global MASTER_IP
        while True:
            if time.time() - TIME_STAMP > 3:
                time.sleep(random.randint(1, 4))
                message  = {"command": "change_master", "args": {"node_ip": NODE_IP}}
                response = json.loads(requests.get(NAME_SERVER_ADDRESS, json=message, timeout=1).text)
                if response['args']['master'] == NODE_IP:
                    MASTER_IP = NODE_IP

                    get_slaves()
                    new_master = Master()
                    for slave in SLAVES:
                        if SLAVES != []:
                            if slaves != NODE_IP:
                                response = json.loads(requests.get('http://' + slave + ':' + str(HTTP_PORT), json=message, timeout=1).text)


                    break


if __name__ == "__main__":
    print(NODE_IP)
    NODE_ADDRESS = ('', HTTP_PORT)
    httpd = HTTPServer(NODE_ADDRESS, Http_handler)
    init_node()
    if NODE_IP == MASTER_IP:
        master = Master()
    else:
        slave = Slave()
    httpd.serve_forever()
