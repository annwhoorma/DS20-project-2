# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path
from errors import return_error
from DBinterface import DBInterface
from user import User

class Namenode:
    # namenode <-> datanode interface
    def __init__(self):
        self.users = []
        self.database = DBInterface(self)
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
    
    def perform_action(self, action, args):
        if args.cur_dir and not args.cur_dir[0] == '/':
            return return_error("NO_SUCH_DIR")
        self.funcs[action](args)
        return "ok", {}

    def auth(self, args):
        username = args.login
        if self.user_exists(username):
            return return_error("USER_ALREADY_EXISTS")
        self.add_user(username)
        self.database.add_root(username)

    def add_user(self, username):
        user = User(username, self)
        self.users.append(user)
    
    def delete_user(self, username):
        # should be called if root dir was requested to be deleted
        for user in self.users:
            if user.username == username:
                self.users.pop(user)
                return
        return return_error("NO_SUCH_USER")

    def user_exists(self, username):
        for user in self.users:
            if user.username == username:
                return True
        return False

    def create_file(self, args):
        filename = args.filename
        cur_dir = args.cur_dir
        path = ""
        res = self.database.create_file(filename, cur_dir, path=path)
        if res == 0:
            # go to datanodes
            pass
            return
        return res 

    def read_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename # might include dirs
        fullpath = self.database.get_fullpath_as_list(cur_dir, path=path)
        self.database.path_exists(fullpath, required_label="File")

    def write_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="File")
    
    def delete_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        self.database.delete_file(cur_dir, path=path)

    def info_file(self, args):
        cur_dir = args.cur_dir
        path = args.filename
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="File")
    
    def copy_file(self, args):
        cur_dir = args.cur_dir
        path_from = args.filename
        path_to = args.dest_dir
        self.database.copy_file(cur_dir, path_from, path_to)

    def move_file(self, args):
        cur_dir = args.cur_dir
        path_from = args.filename
        path_to = args.dest_dir
        self.database.copy_file(cur_dir, path_from, path_to, delete_original=True)

    def open_dir(self, args):
        cur_dir = args.cur_dir
        path = args.target_dir
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="Dir")
    
    def read_dir(self, args):
        cur_dir = args.cur_dir
        path = args.target_dir
        self.database.list_files(cur_dir, path)
        
    def make_dir(self, args):
        cur_dir = args.cur_dir
        path = args.new_dir
        self.database.make_dir(cur_dir, path)

    def del_dir(self, args):
        cur_dir = args.cur_dir
        path = args.del_dir
        self.database.delete_dir(cur_dir, path)