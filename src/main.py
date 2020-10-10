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

@client.route('/', methods=['GET'])
def index():
    namenode = Namenode()
    msg = request.json # from Ruslan or Alla
    if is_heartbeat_protocol(msg.command):
        action = msg.action 
        args = msg.args if msg.args else ""
        status, args = namenode.perform_action_heartbeat(action, args)
        if status == 1:
            return jsonify(status="Failed", args={})
        elif status == 0:
            return jsonify(status="OK", args=args)
        return
        
    elif is_client_protocol(msg.command):
        status, args = namenode.perform_action_database(msg.action, msg.args)
        if status == 0:
            command, args2 = preprocessing(msg.action, args)
            json = jsonify(command, args2)
            msg = requests.request(method='get', url="http://{ip}:{port}".format(ip=ALLA_IP, port=ALLA_PORT), json=json)
            status2 = msg.status
            args3 = msg.args.error or "some error"
            if status2 == "OK":
                return jsonify(status=OK, args={}) ### fix args
            if status2 == "Failed":
                return jsonify(status=NOTOK, args={"error": args3})
        else:
            return jsonify(status=NOTOK, args=args)

    else: 
        return

client.run(port=MY_PORT)

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