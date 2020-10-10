# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path
from errors import throw_error
from DBinterface import DBInterface
from user import User
from Datanode import Datanode
from time import time
import json

MASTER_DOWN_TIMEOUT = 11
MASTER_NODE_TYPE = 'master'
SLAVE_NODE_TYPE = 'slave'


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
            "read_file": self.read_file,
            "write_file": self.write_file,
            "delete_file": self.delete_file,
            "info_file": self.info_file,
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
        if len(self.datanodes) == 0:
            node.promote()
            ret_args = {"master": ip, "node_status": "new"}
        elif self.is_old_node(node):
            # the node just got up
            ret_args = {"master": master.ip, "node_status": "old"}
        else:
            # the node just joined
            ret_args = {"master": master.ip, "node_status": "new"}

        return 0, ret_args

    def change_master(self, args):
        if self.is_master_down():
            node_ip = args["node_ip"]
            master_ip = ""
            master = self.get_master()
            if not master:
                master_ip = node_ip
                self.find_datanode_by_ip(master_ip).promote()
            return 0, {"master": "{ip}".format(ip=master_ip)}
        return 1, {"error": throw_error("INVALID_REQUEST")}

    def update_slaves_list(self, args):
        slaves_ips = args["slaves"]
        for ip in slaves_ips:
            node = self.find_datanode_by_ip(ip)
            node.demote()
        return 2, {}

    def send_slaves_list(self, args):
        ips = []
        for node in self.datanodes:
            if node.type == SLAVE_NODE_TYPE:
                ips.append(node.ip)
        return 0, {"slaves": ips}

    ''' helping methods '''
    def is_master_down(self):
        if time() - self.master_timestamp < MASTER_DOWN_TIMEOUT:
            return True
        return False

    def is_old_node(self, datanode):
        for node in self.datanodes:
            if node.ip == datanode.ip:
                return True
        return False    

    def get_master(self):
        for node in self.datanodes:
            if node.type == MASTER_NODE_TYPE:
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
        filename = args["filename"]
        cur_dir = args["cur_dir"]
        path = ""
        res, arg = self.database.create_file(filename, cur_dir, path=path)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def read_file(self, args):
        cur_dir = args["cur_dir"]
        path = args["filename"] # might include dirs
        fullpath, arg = self.database.get_fullpath_as_list(cur_dir, path=path)
        if fullpath == 1:
            return 1, {"error": arg}
        res, arg = self.database.path_exists(fullpath, required_label="File")
        return (0, {"path": arg}) if res == True else (1, {"error": arg})

    def write_file(self, args):
        cur_dir = args["cur_dir"]
        path = args["filename"]
        fullpath, arg = self.database.get_fullpath_as_list(cur_dir, path)
        if fullpath == 1:
            return 1, {"error": arg}
        res, arg = self.database.path_exists(fullpath, required_label="File")
        return (0, {"path": arg}) if res == True else (1, {"error": arg})
    
    def delete_file(self, args):
        cur_dir = args["cur_dir"]
        path = args["filename"]
        res, arg = self.database.delete_file(cur_dir, path=path)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def info_file(self, args):
        cur_dir = args["cur_dir"]
        path = args["filename"]
        fullpath, arg = self.database.get_fullpath_as_list(cur_dir, path)
        if fullpath == 1:
            return 1, {"error": arg}
        res, arg = self.database.path_exists(fullpath, required_label="File")
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})
    
    def copy_file(self, args):
        cur_dir = args["cur_dir"]
        path_from = args["filename"]
        path_to = args["dest_dir"]
        res, arg = self.database.copy_file(cur_dir, path_from, path_to)
        # arg is [src, dst]
        return (0, {"path": arg[0]}) if res == 0 else (1, {"error": arg})

    def move_file(self, args):
        cur_dir = args["cur_dir"]
        path_from = args["filename"]
        path_to = args["dest_dir"]
        res, arg = self.database.move_file(cur_dir, path_from, path_to)
        # arg is [src, dst]
        return (0, {"src": arg[0], "dst": arg[1]}) if res == 0 else (1, {"error": arg})

    def open_dir(self, args):
        cur_dir = args["cur_dir"]
        path = args["target_dir"]
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        if self.database.path_exists(fullpath, required_label="Dir"):
            return 0, {}
        return 1, {"error": throw_error("NO_SUCH_DIR")}
    
    def read_dir(self, args):
        cur_dir = args["cur_dir"]
        path = args["target_dir"]
        res, arg = self.database.list_files(cur_dir, path)
        return (0, {"dirs": arg}) if res == 0 else (1, {"error": arg})
        
    def make_dir(self, args):
        cur_dir = args["cur_dir"]
        path = args["new_dir"]
        res, arg = self.database.make_dir(cur_dir, path)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def del_dir(self, args):
        cur_dir = args["cur_dir"]
        path = args["del_dir"]
        res, arg = self.database.delete_dir(cur_dir, path)
        return (0, {"path": arg}) if res == 0 else (1, {"error": arg})

    def user_exists(self, username):
        for user in self.users:
            if user == username:
                return True
        return False


def preprocessing(namenode_command, fullpath):
    user, path = fullpath_to_string(fullpath)
    datanode_command = commands_mapping[namenode_command]
    fields = {
        "user": "/{username}".format(username=user),
        "path": path
    }
    return datanode_command, fields

def fullpath_to_string(fullpath):
    user = fullpath.pop(0)
    path = ""
    for entry in fullpath:
        path += "/{entry}".format(entry=entry)
    return user, path