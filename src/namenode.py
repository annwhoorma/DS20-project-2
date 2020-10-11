# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path
from errors import throw_error
from DBinterface import DBInterface
from Datanode import Datanode
from time import time
import json

MASTER_DOWN_TIMEOUT = 11


commands_mapping = {
    "new_user": "init",
    "create_file": "file_create",
    "read_file": "read_file",
    "write_file": "write_file",
    "delete_file": "file_delete",
    "info_file": "file_info",
    "copy_file": "file_copy",
    "move_file": "file_move",
    "make_dir": "create_dir",
    "del_dir": "delete_dir"
}

class Namenode:
    def __init__(self):
        self.users = []
        self.database = DBInterface(self)
        self.datanodes = []
        self.master_timestamp = 0
        self.funcs_client = {
            "auth": self.auth,
            "new_user": self.add_user,
            "create_file": self.create_file,
            "delete_file": self.delete_file,
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "open_dir": self.open_dir,
            "read_dir": self.read_dir,
            "make_dir": self.make_dir,
            "del_dir": self.del_dir,
        }
        self.funcs_datanode = {
            "<3": self.update_master_timestamp,
            "init_node": self.init_node,
            "change_master": self.change_master,
            "get_slaves": self.update_slaves_list,
            "share_slaves": self.send_slaves_list
        }
    
    def perform_action_database(self, action, args):
        print("perform action", args)
        res, arg = self.funcs_client[action](args)
        print(res, arg)
        if not res == 0:
            return 1, arg
        return res, arg

    def perform_action_heartbeat(self, action, args):
        if not args and not action == "<3" and not action == "share_slaves":
            return 1, {"error": throw_error("INVALID_REQUEST")}

        if not args and (action == "<3" or action == "share_slaves"):
            res, arg = self.funcs_datanode[action]()
            return res, arg

        res, arg = self.funcs_datanode[action](args)
        if not res == 0:
            return 1, {"error": throw_error("INVALID_REQUEST")}
        return res, arg
        
    '''
    METHODS RELATED TO THE HEARTBEATS PROTOCOL
    '''
    
    def update_master_timestamp(self):
        self.master_timestamp = time()
        return 2, ""
    
    def init_node(self, args):
        ret_args = {}
        if not args["node"]:
            return 1, {"error": throw_error("INVALID_REQUEST")}
        ip = args["node"]
        node = Datanode(ip)
        master = self.get_master()
        if len(self.datanodes) == 0 or master == None:
            node.promote()
            self.master_timestamp = time()
            ret_args = {"master": ip, "node_status": "new"}
        elif self.is_old_node(node):
            # the node just got up
            ret_args = {"master": master.ip, "node_status": "old"}
        else:
            # the node just joined
            ret_args = {"master": master.ip, "node_status": "new"}
        self.datanodes.append(node)

        return 0, ret_args

    def change_master(self, args):
        if len(self.datanodes) == 0:
            return 1, {"error": "Invalid request"}
        master = self.get_master()
        master_ip = master.ip if master else ""
        if self.is_master_down():
            node_ip = args["node"] # should i check that it exists?
            if not self.find_datanode_by_ip(node_ip):
                return 1, {"master": "{ip}".format(ip=master_ip)}
            self.get_master().demote()
            self.find_datanode_by_ip(node_ip).promote()
            master_ip = self.get_master().ip
            return 0, {"master": "{ip}".format(ip=master_ip)}

        return 1, {"master": "{ip}".format(ip=master_ip)}

    def update_slaves_list(self, args):
        if len(self.datanodes) == 0:
            return 1, {"error": "Invalid request"}
        slaves_ips = args["slaves"]
        print(slaves_ips)
        for ip in slaves_ips:
            node = self.find_datanode_by_ip(ip)
            if not node:
                node.demote()
            else:
                return 1, {"error": "Invalid request"}
                
        return 0, {}

    def send_slaves_list(self):
        ips = []
        for node in self.datanodes:
            if node.type == 'slave':
                ips.append(node.ip)
        return 0, {"slaves": ips}

    ''' helping methods '''
    def is_master_down(self):
        if time() - self.master_timestamp > MASTER_DOWN_TIMEOUT:
            return True
        return False

    def is_old_node(self, datanode):
        for node in self.datanodes:
            if node.ip == datanode.ip:
                return True
        return False    

    def get_master(self):
        for node in self.datanodes:
            if node.type == 'master':
                return node
        return

    def find_datanode_by_ip(self, ip):
        for node in self.datanodes:
            if node.ip == ip:
                return node
        return

    '''
    METHODS RELATED TO THE CLIENT PROTOCOL
    '''

    def auth(self, args):
        username = args['login']
        if not self.user_exists(username):
            return 1, {"error": throw_error("NO_SUCH_USER")}
        return 0, {}

    def add_user(self, args):
        username = args["login"]
        if self.user_exists(username):
            return 1, {"error": throw_error("USER_ALREADY_EXISTS")}

        self.users.append(username)
        res, arg = self.database.add_root(username)
        return (0, ["/"]) if res == 0 else (1, {"error": arg})

    def create_file(self, args):
        cur_dir = args["cur_dir"]
        res, arg = self.database.create_file(cur_dir)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})
    
    def delete_file(self, args):
        cur_dir = args["cur_dir"]
        res, arg = self.database.delete_file(cur_dir)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})
    
    def copy_file(self, args):
        cur_dir = args["cur_dir"] # will include the old name
        new_name = args["new_name"]
        new_path = substitute_file_name(cur_dir, new_name)
        res, arg = self.database.create_file(new_path)
        return (0, {}) if res == 0 else (1, {"error": arg})

    def move_file(self, args):
        cur_dir = args["cur_dir"]
        filename = retrieve_filename(cur_dir)
        dst_dir = append_filename_to_path(args["dest_dir"], filename)
        res1, arg1 = self.database.delete_file(cur_dir)
        res2, arg2 = self.database.create_file(dst_dir)
        # arg is [src, dst]
        return (0, {}) if res1 == 0 and res2 == 0 else (1, {"error": arg1 + " & " + arg2})

    def open_dir(self, args):
        cur_dir = args["cur_dir"]
        res, fullpath = self.database.get_fullpath_as_list(cur_dir)
        print(fullpath)
        res, arg  = self.database.path_exists(fullpath, required_label="Dir")
        if res != 1:
            return 0, {}
        return 1, {"error": throw_error("NO_SUCH_DIR")}
    
    def read_dir(self, args):
        path = args["target_dir"]
        res, arg = self.database.list_files(path)
        return (0, {"dirs": arg}) if res == 0 else (1, {"error": arg})
        
    def make_dir(self, args):
        cur_dir = args["cur_dir"]
        res, arg = self.database.make_dir(cur_dir)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def del_dir(self, args):
        cur_dir = args["cur_dir"]
        res, arg = self.database.delete_dir(cur_dir)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def user_exists(self, username):
        for user in self.users:
            if user == username:
                return True
        return False


def preprocessing(namenode_command, args):
    datanode_command = commands_mapping[namenode_command]
    if datanode_command == "file_move":
        src = args["cur_dir"]
        dst = args["dest_dir"]
        user, src = client_path_to_string(src)
        user, dst = client_path_to_string(dst)
        fields = {
            "user": "/{username}".format(username=user),
            "src": "src".format(src=src),
            "dst": "dst".format(dst=dst)
        }
        return datanode_command, fields

    client_path = args["cur_dir"]
    user, path = client_path_to_string(client_path)
    fields = {
        "user": "/{username}".format(username=user),
        "path": path
    }
    return datanode_command, fields

def client_path_to_string(client_path):
    fullpath = []
    fullpath = client_path.split('/')
    while '' in fullpath:
        fullpath.remove('')
    user = fullpath.pop(0)
    new_path = ""
    while len(fullpath) > 0:
        new_path += "/" + fullpath.pop(0)
    return user, new_path

def substitute_file_name(path, new_name):
    fullpath = []
    fullpath = path.split('/')
    while '' in fullpath:
        fullpath.remove('')
    fullpath.remove(len(fullpath)-1)
    fullpath.append(new_name)
    new_path = ""
    while len(fullpath) > 0:
        new_path += "/" + fullpath.pop(0)
    return new_path

def append_filename_to_path(path, filename):
    fullpath = []
    fullpath = path.split('/')
    while '' in fullpath:
        fullpath.remove('')
    fullpath.append(filename)
    new_path = ""
    while len(fullpath) > 0:
        new_path += "/" + fullpath.pop(0)
    return new_path

def retrieve_filename(path):
    fullpath = []
    fullpath = path.split('/')
    while '' in fullpath:
        fullpath.remove('')
    filename = fullpath.pop(len(fullpath)-1)
    return filename