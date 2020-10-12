from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
HTTP_PORT = 5000
MASTER_IP = ''
SLAVES = []
NEW_SLAVES = []
def json_read(message):
    json_object = json.loads(message.decode("utf-8"))
    return json_object
TIME_STAMP = time.time()

def update_time_stamp():
    global TIME_STAMP
    TIME_STAMP = time.time()

class Http_handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global MASTER_IP
        global SLAVES
        global NEW_SLAVES
        global TIME_STAMP
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        res = ""
        message = json_read(data)

        command = message["command"]
        print(command)

        if command == "init_node":
            node_ip = message["args"]["node"]
            if MASTER_IP == '' or time.time() - TIME_STAMP > 7:
                print("NEW MASTER", node_ip)
                res = {"status": "OK", "args": {"master": node_ip, "node_status": "old"}}
                MASTER_IP = node_ip
            else:
                res = {"status": "OK", "args": {"master": MASTER_IP, "node_status": "old"}}
                if node_ip not in SLAVES:
                    NEW_SLAVES.append(node_ip)

        elif command == "<3":
            update_time_stamp()
        elif command == "share_slaves":
            SLAVES += NEW_SLAVES
            NEW_SLAVES = []

            res = {"status": "OK", "args": {}}
            res["args"]["slaves"] = SLAVES
        elif command == "change_master":
            node_ip = message["args"]["node_ip"]

            if time.time() - TIME_STAMP > 4:
                res = {"status": "Failed", "args": {"master": node_ip, "node_status": "old"}}
                MASTER_IP = node_ip
                print("NEW MASTER", MASTER_IP)
                print("!", SLAVES)
                SLAVES.remove(MASTER_IP)
                print("!", SLAVES)
            else:
                res = {"status": "Failed", "args": {"master": MASTER_IP, "node_status": "old"}}
        elif command == "get_slaves":
            print(message["args"]["slaves"], "\n")
            if message["args"]["slaves"] != "none":
                SLAVES = message["args"]["slaves"]
                SLAVES += NEW_SLAVES
                NEW_SLAVES = []
        res = json.dumps(res)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(res, "utf-8"))

if __name__ == "__main__":
    MASTER_IP = ''
    NODE_ADDRESS = ('', HTTP_PORT)
    httpd = HTTPServer(NODE_ADDRESS, Http_handler)
    httpd.serve_forever()
