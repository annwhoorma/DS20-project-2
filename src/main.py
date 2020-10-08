from flask import Flask, request, jsonify
import requests
from namenode import Namenode

PORT = 5000

# requests.post(url="http://ip:port", json=json)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    namenode = Namenode()
    msg = request.json
    status, args = namenode.perform_action(msg.action, msg.args)
    return jsonify(status=status, args=args)

app.run(port=PORT)