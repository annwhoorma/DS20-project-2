from flask import Flask, request, jsonify
import requests
from namenode import Namenode, preprocessing

RUSLAN_PORT = 1234
MY_PORT = 5000
ALLA_IP = "localhost"
ALLA_PORT = 1400
OK = "<3"
NOTOK = "</3"

client = Flask(__name__)
namenode = Namenode()


def is_heartbeat_protocol(cmd):
    commands = ['init_node', '<3', 'change_master', 'get_slaves', 'share_slaves']
    if cmd in commands:
        return True
    return False

def is_client_protocol(cmd):
    commands = ["auth", "new_user", "create_file", "read_file", "write_file", "delete_file",
                "info_file", "copy_file", "move_file", "open_dir", "read_dir", "make_dir", "del_dir"]
    if cmd and cmd in commands:
        return True
    return False

def requires_datanodes_only(cmd):
    commands = ["read_file", "write_file", "info_file"]
    if cmd and cmd in commands:
        return True
    return False

def requires_namenode_only(cmd):
    commands = ["auth", "open_dir", "read_dir"]
    if cmd and cmd in commands:
        return True
    return False


@client.route('/', methods=['GET'])
def index():
    msg = request.json
    if is_heartbeat_protocol(msg["command"]):
        print("heartbeat protocol detected")
        action = msg["command"] 
        args = msg["args"] if not (msg["command"] == "<3" or msg["command"] == "share_slaves") else {}
        status, args = namenode.perform_action_heartbeat(action, args)
        if status == 1:
            return jsonify(status="Failed", args={})
        elif status == 0:
            return jsonify(status="OK", args=args)
        return jsonify(status="OK", args={})
        
    elif is_client_protocol(msg["command"]):
        print("client protocol detected")
        if msg["command"] == "new_user":
            status, args = namenode.perform_action_database(msg["command"], msg["args"])
            if status == 0:
                username = args["login"]
                json = jsonify(command="init", args={"user": "/{username}".format(username=username)})
                msg2 = requests.request(method='get', url="http://{ip}:{port}".format(ip=ALLA_IP, port=ALLA_PORT), json=json)
                return jsonify(status=OK, args={})

        if requires_namenode_only(msg["command"]):
            status, args = namenode.perform_action_database(msg["command"], msg["args"])
            return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)

        elif requires_datanodes_only(msg["command"]):
            command, args2 = preprocessing(msg["command"], msg["args"])
            json = jsonify(command, args2)
            msg2 = requests.request(method='get', url="http://{ip}:{port}".format(ip=ALLA_IP, port=ALLA_PORT), json=json)
            status2 = msg2["status"]
            args3 = msg2["args"]["error"] if status2 == "Failed" else ""
            return jsonify(status=OK, args=args3) if status == "OK" else jsonify(status=NOTOK, args={"error": args3})
        
        else: # requires both
            command, args2 = preprocessing(msg["command"], msg["args"])
            json = jsonify(command, args2)
            msg2 = requests.request(method='get', url="http://{ip}:{port}".format(ip=ALLA_IP, port=ALLA_PORT), json=json)
            status2 = msg2["status"]
            args3 = msg2["args"]["error"] if "error" in msg2["args"] else ""

            if status == "OK" and msg["command"] == "copy_file":
                # the datanode sent the new name
                new_name = msg2["args"]["filename"]
                msg["args"]["new_name"] = new_name
                status, args = namenode.perform_action_database(msg["command"], msg["args"])
                return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)

            elif status == "OK":
                # update the namenode
                status, args = namenode.perform_action_database(msg["command"], msg["args"])
                return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)
            else:
                return jsonify(status=NOTOK, args={"error": args3})

    else: 
        return jsonify(status=NOTOK, args={"error": "Invalid command"})

client.run(port=MY_PORT)
