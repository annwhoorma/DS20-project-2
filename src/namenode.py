# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path
from errors import throw_error
from DBinterface import DBInterface
from user import User
from DatanodeInterface import DatanodeInterface

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
    # namenode <-> datanode interface
    def __init__(self):
        self.users = []
        self.database = DBInterface(self)
        self.datanode = DatanodeInterface(self)
        self.active_datanodes = []
        self.leader_datanode = None
        self.funcs = {
            "auth": self.user_exists,
            "new_user": self.add_user,
            "create_file": self.create_file,
            "read_file": self.read_file, # check that file exists and read from datanodes
            "write_file": self.write_file, # check that file exists and write to file
            "delete_file": self.delete_file,
            "info_file": self.info_file, # check that file exists and write to file
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "open_dir": self.open_dir,
            "read_dir": self.read_dir,
            "make_dir": self.make_dir,
            "del_dir": self.del_dir
        }
    
    def perform_action_database(self, action, args):
        if args.cur_dir and not args.cur_dir[0] == '/':
            return 1, throw_error("NO_SUCH_DIR")
        res, arg = self.funcs[action](args)
        return res, arg

    def perform_action_datanode(self, action, args):
        command, fields = preprocessing(action, args)
        

    def add_user(self, args):
        username = args.login
        if self.user_exists(username):
            return 1, throw_error("USER_ALREADY_EXISTS")
        self.add_user(username)
        self.database.add_root(username)
        # datanodes
        command = commands_mapping["add_user"]
        fields = {
            "user": "/{username}".format(username=username)
        }
        self.datanode.compose_request(command, fields)
        #### return smt

    def auth(self, args):
        username = args['username']
        if not self.user_exists(username):
            return 1, throw_error("NO_SUCH_USER")
        user = User(username, self)
        self.users.append(user)
        return 0, 0
    
    # deprecated 
    def delete_user(self, username):
        # should be called if root dir was requested to be deleted? 
        for user in self.users:
            if user.username == username:
                self.users.pop(user)
                # call to datanodes
                return 
        return 1, throw_error("NO_SUCH_USER")

    def user_exists(self, username):
        for user in self.users:
            if user.username == username:
                return True
        return False

    def create_file(self, args):
        filename = args.filename
        cur_dir = args.cur_dir
        path = ""
        res, arg = self.database.create_file(filename, cur_dir, path=path)

        if res == 0:
            command, fields = preprocessing('create_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # res is an error
            return 1, arg 

    def read_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename # might include dirs
        fullpath = self.database.get_fullpath_as_list(cur_dir, path=path)
        res, arg = self.database.path_exists(fullpath, required_label="File")

        if res == 0:
            command, fields = preprocessing('read_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # res is an error
            return 1, arg 

    def write_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        res, arg = self.database.path_exists(fullpath, required_label="File")

        if res == 0:
            command, fields = preprocessing('write_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 
    
    def delete_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        res, arg = self.database.delete_file(cur_dir, path=path)

        if res == 0:
            command, fields = preprocessing('delete_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 

    def info_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        res, arg = self.database.path_exists(fullpath, required_label="File")
        if res == 0:
            command, fields = preprocessing('info_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 
    
    def copy_file(self, args):
        cur_dir = args.cur_dir
        path_from = args.filename
        path_to = args.dest_dir
        res, arg = self.database.copy_file(cur_dir, path_from, path_to)
        if res == 0:
            command, fields = preprocessing('copy_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 

    def move_file(self, args):
        cur_dir = args.cur_dir
        path_from = args.filename
        path_to = args.dest_dir
        res, arg = self.database.copy_file(cur_dir, path_from, path_to, delete_original=True)
        if res == 0:
            command, fields = preprocessing('move_file', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 

    def open_dir(self, args):
        cur_dir = args.cur_dir
        path = args.target_dir
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        if self.database.path_exists(fullpath, required_label="Dir"):
            return 0, 0
    
    def read_dir(self, args):
        cur_dir = args.cur_dir
        path = args.target_dir
        res, arg = self.database.list_files(cur_dir, path)
        return res, arg # (0, files) or (1, error)
        
    def make_dir(self, args):
        cur_dir = args.cur_dir
        path = args.new_dir
        res, arg = self.database.make_dir(cur_dir, path)
        if res == 0:
            command, fields = preprocessing('make_dir', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 

    def del_dir(self, args):
        cur_dir = args.cur_dir
        path = args.del_dir
        res, arg = self.database.delete_dir(cur_dir, path)
        if res == 0:
            command, fields = preprocessing('del_dir', arg)
            self.datanode.compose_request(command, fields)
            # ?????
            return 0, 0
        elif res == 1:
            # arg is an error
            return 1, arg 


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