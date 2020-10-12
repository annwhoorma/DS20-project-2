from flask import Flask, request, jsonify
import requests
from namenode import Namenode, preprocessing

MY_PORT = 5000

CLIENT_IP = "localhost"
CLIENT_PORT = 1234

DATANODE_IP = "localhost"
DATANODE_PORT = 1400

OK = "<3"
NOTOK = "</3"

EXPECT_FILE_READ = False
EXPECT_FILE_WRITE = False

client = Flask(__name__)
namenode = Namenode()

'''
@param: cmd - the command that came from the client or the datanode
@return: true if the command is related to the heartbeat protocol, false otherwise
'''
def is_heartbeat_protocol(cmd):
    commands = ['init_node', '<3', 'change_master', 'get_slaves', 'share_slaves']
    if cmd in commands:
        return True
    return False

'''
@param: cmd - the command that came from the client or the datanode
@return: true if the command is related to the client-namenode protocol, false otherwise
'''
def is_client_protocol(cmd):
    commands = ["auth", "new_user", "create_file", "read_file", "write_file", "delete_file",
                "info_file", "copy_file", "move_file", "open_dir", "read_dir", "make_dir", "del_dir"]
    if cmd and cmd in commands:
        return True
    return False

'''
@param: cmd - the command that came from the client
@return: true if the command requires some file reading or writing, false otherwise
'''
def requires_file_operation(cmd):
    commands = ["read_file", "write_file"]
    if cmd and cmd in commands:
        return True
    return False

'''
@param: cmd - the command that came from the client
@return: true if the command requires some file reading or writing, false otherwise
'''
def requires_datanodes_only(cmd):
    commands = ["info_file"]
    if cmd and cmd in commands:
        return True
    return False

'''
@param: cmd - the command that came from the client
@return: true if the command can be satisfied from the namenode, false otherwise
'''
def requires_namenode_only(cmd):
    commands = ["auth", "open_dir", "read_dir"]
    if cmd and cmd in commands:
        return True
    return False

'''
expects "GET" HTTP-requests because of bad architecture decisions
the author of this code would rather implement POST requests
'''
@client.route('/', methods=['GET'])
def index():
    # check if any files arrived
    data = request.files
    # if files arrived and the client issued a read operation, the the file came from 
    # the datanode and needs to be forwarded to the client
    if data and EXPECT_FILE_READ:
        EXPECT_FILE_READ = False
        requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=CLIENT_IP, port=CLIENT_PORT), files=data)
        return jsonify({"status": OK})
    # if files arrived and the client issued a write operation, the the file came from 
    # the client and needs to be forwarded to the datanode
    elif data and EXPECT_FILE_WRITE:
        # send it to the client
        EXPECT_FILE_WRITE = False
        requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=DATANODE_IP, port=DATANODE_PORT), files=data)
        return jsonify({"status": OK})

    # check if some json message arrived from the client or the datanode
    msg = request.json
    # check if the message is related to the heartbeat protocol
    if is_heartbeat_protocol(msg["command"]):
        print("heartbeat protocol detected")
        action = msg["command"]
        # process the message
        args = msg["args"] if not (msg["command"] == "<3" or msg["command"] == "share_slaves") else {}
        status, args = namenode.perform_action_heartbeat(action, args)
        # success or failure - notify the datanode
        if status == 1:
            return jsonify(status="Failed", args={})
        elif status == 0:
            return jsonify(status="OK", args=args)
        return jsonify(status="OK", args={})
    
    # check if the message is related to the client-namenode protocol
    elif is_client_protocol(msg["command"]):
        print("client protocol detected")
        # process the message
        # if it is a new user then we need to make sure that the name is available
        if msg["command"] == "new_user":
            status, args = namenode.perform_action_database(msg["command"], msg["args"])
            # if the name is available, send a request to the datanode, if satisfied - send OK to the client
            if status == 0:
                username = msg["args"]["login"]
                json = {"command": "init", "args": {"user": "/{{username}}".format(username=username)}}
                msg2 = requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=DATANODE_IP, port=DATANODE_PORT), json=json)
                return jsonify(status=OK, args={})

        # check if the message can be satisfied without going to the datanode
        if requires_namenode_only(msg["command"]):
            status, args = namenode.perform_action_database(msg["command"], msg["args"])
            return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)

        # check if the message doesn't require any operations from the namenode
        # and return the result to the client
        elif requires_datanodes_only(msg["command"]):
            command, args2 = preprocessing(msg["command"], msg["args"])
            json = {"command": command, "args": args2}
            msg2 = requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=DATANODE_IP, port=DATANODE_PORT), json=json)
            status2 = msg2["status"]
            args3 = msg2["args"]["error"] if status2 == "Failed" else ""
            return jsonify(status=OK, args=args3) if status == "OK" else jsonify(status=NOTOK, args={"error": args3})
        
        # check if the client issued write or read operation and set the corresponding global flag to True
        elif requires_file_operation(msg["command"]):
            if msg["command"] == "read_file":
                EXPECT_FILE_READ = True
            else:
                EXPECT_FILE_WRITE = True
                msg2 = requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=DATANODE_IP, port=DATANODE_PORT), json=json)
            status, args = namenode.perform_action_database(msg["command"], msg["args"])
            # check with the datanode as well - there is no such command yet
            return jsonify(status=OK, args={}) if status == 0 else jsonify(status=NOTOK, args=args)
        
        # requires both namenode and datanode
        else: 
            command, args2 = preprocessing(msg["command"], msg["args"])
            json = {"command": command, "args": args2}
            msg2 = requests.request(method='get', url="http://{{ip}}:{{port}}".format(ip=DATANODE_IP, port=DATANODE_PORT), json=json)
            status2 = msg2["status"]
            args3 = msg2["args"]["error"] if "error" in msg2["args"] else ""

            if status == "OK" and msg["command"] == "copy_file":
                # the datanode sent the new name in case the file was copied successfully 
                new_name = msg2["args"]["filename"]
                msg["args"]["new_name"] = new_name
                status, args = namenode.perform_action_database(msg["command"], msg["args"])
                return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)

            elif status == "OK":
                # update the namenode if the request was satisfied
                status, args = namenode.perform_action_database(msg["command"], msg["args"])
                return jsonify(status=OK, args=args) if status == 0 else jsonify(status=NOTOK, args=args)
            else:
                return jsonify(status=NOTOK, args={"error": args3})

    else: 
        return jsonify(status=NOTOK, args={"error": "Invalid command"})

client.run(port=MY_PORT)
