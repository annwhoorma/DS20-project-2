import json
import os
import subprocess
import shutil


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

    return os.path.exists(root + path)

def check_root(root):
    return os.path.exists(root)

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
if __name__ == "__main__":
    message1 = json.dumps({"command": "touch", "args": {"user": "/Users/admin/Desktop/ds/new_folder", "path": "test1"}})
    message2 = json.dumps({"command": "mv",
    "args": {"user": "/Users/admin/Desktop", "src": "/ds_project/test.txt", "dst": "/ds/test.txt"}})
    message3 = json.dumps({"command": "info", "args": {"user": "/Users/admin/Desktop/ds/", "path": "/folder"}})

    print(list_directory(json_read(message3)))
