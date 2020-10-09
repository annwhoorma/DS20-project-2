from flask import Flask, request, jsonify
import requests
from namenode import Namenode, preprocessing

RUSLAN_PORT = 1235
MY_PORT = 5000
ALLA_IP = "some_host_idk_yet"
ALLA_PORT = 1234
OK = "<3"
NOTOK = "</3"
# requests.post(url="http://ip:port", json=json)

client = Flask(__name__)

@client.route('/', methods=['GET'])
def index():
    namenode = Namenode()
    msg = request.json # from Ruslan
    status, args = namenode.perform_action_database(msg.action, msg.args)
    if status == 0:
        command, args = preprocessing(msg.action, args)
        json = jsonify(command, args)
        msg = requests.request(method='get', url="http://{ip}:{port}".format(ip=ALLA_IP, port=ALLA_PORT), json=json)
        status2 = msg.status
        args2 = msg.args
        if status2 == 0:
            return jsonify(status=OK, args={}) ### fix args
        if status2 == 1:
            return jsonify(status=NOTOK, args={"error": args2})
        else:
            return jsonify(status=NOTOK, args={"error": "some_error_later"})
    elif status == 1:
        return jsonify(status="</3", args={"error": args})

client.run(port=MY_PORT)


