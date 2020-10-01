import json
import os

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
    else:
        res = {"status": "Denied", "message": "File creation did not succeed - no such directory."}
        
    return json.dumps(res)

def read_file(message):
    pass
def delete_file(message):
    pass

if __name__ == "__main__":
    message = json.dumps({"command": "touch", "args": {"user": "/Users/admin/Desktop/ds_project/", "path": "test.txt"}})
    print(create_file(json_read(message)))
