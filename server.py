import json
import os
import subprocess


""" JSON format for received message:
        {
            "command": "string (mkdir, for example)",
            "args": [
                "user": "string",
                "path": "string"
                ]
        }
    JSON format for sended message:
    {
        "status": "string (OK, for example)",
        "message": "string (There is no such directory, for example)"
    }
"""
def check_path(message):
    root = message["args"]["user"]
    path = message["args"]["path"]

    if os.path.exists(root + path):
        return True
    else:
        return False


def json_read(message):
    obj = json.loads(message)
    return obj

def create_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path
    directory_to_put = local_path[:local_path.rfind("/")]

    if not(check_path(message)) and os.path.exists(directory_to_put):
        os.system('touch ' + local_path)
        res = {"status": "OK", "message": "File creation succeed"}
    elif check_path(message):
        res = {"status": "Denied", "message": "File creation did not succeed - file with this name already exists."}
    else:
        res = {"status": "Denied", "message": "File creation did not succeed - no such directory to put a file."}

    return json.dumps(res)

def read_file(message):
    pass

def delete_file(message):
    root = message["args"]["user"]
    path = message["args"]["path"]
    local_path = root + path

    if check_path(message):
        os.remove(local_path)
        res = {"status": "OK", "message": "File deletion succeed"}
    else:
        res = {"status": "Denied", "message": "File deletion did not succeed - no such file."}
    return json.dumps(res)

def move_file(message):
    root = message["args"]["user"]
    src = message["args"]["src"]
    dst = message["args"]["dst"]

    if os.path.exists(root+src) and not (os.path.exists(root+dst)):
        os.system('mv ' + root + src + ' ' + root + dst)
        res = {"status": "OK", "message": "File moving succeed"}
    elif os.path.exists(root+dst):
        res = {"status": "Denied", "message": "File moving did not succeed - destination path already exists."}
    else:
        res = {"status": "Denied", "message": "File moving did not succeed - no such source path."}
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
        res = {"status": "Denied", "message": "File info retrieval did not succeed - no such file."}
    return json.dumps(res)

if __name__ == "__main__":
    message1 = json.dumps({"command": "touch", "args": {"user": "/Users/admin/Desktop/ds/", "path": "test.txt"}})
    message2 = json.dumps({"command": "mv",
    "args": {"user": "/Users/admin/Desktop", "src": "/ds_project/test.txt", "dst": "/ds/test.txt"}})
    message3 = json.dumps({"command": "info", "args": {"user": "/Users/admin/Desktop/ds/", "path": "test.txt"}})

    print(create_file(json_read(message1)))
    print(info_file(json_read(message3)))
