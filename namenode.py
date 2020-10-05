# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path
from flask import Flask, request, jsonify
from neo4j import GraphDatabase
import http.server
import socketserver
import json

PORT = 5000

# for neo4j
uri = "bolt://localhost:7687"
username_db = "neo4j"
password_db = "ohmyg0d"

def print_error(message):
    print("ERROR: {m}".format(m=message)) if message else print('ERROR')
    # return None


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
        self.funcs[action](args)
        return "ok", {}

    def initialize(self, username):
            # check username uniquness
        for user in self.users:
            if user.name == username:
                print_error('user with this name already exists')
                return
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
        print_error('user with this username does not exist')

    def user_exists(self, username):
        for user in self.users:
            if user.username == username:
                return True
        return False

    def create_file(self, filename, cur_dir, path):
        self.database.create_file(filename, cur_dir, path=path)
        # go to datanodes

    def read_file(self, cur_dir, path):
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="File")

    def write_file(self, cur_dir, path):
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="File")
    
    def delete_file(self, cur_dir, path):
        self.database.delete_file(cur_dir, path=path)

    def info_file(self, cur_dir, path):
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="File")
    
    def copy_file(self, cur_dir, path_from, path_to):
        self.database.copy_file(cur_dir, path_from, path_to)

    def move_file(self, cur_dir, path_from, path_to):
        self.database.copy_file(cur_dir, path_from, path_to, delete_original=True)

    def open_dir(self, cur_dir, path):
        fullpath = self.database.get_fullpath_as_list(cur_dir, path)
        self.database.path_exists(fullpath, required_label="Dir")
    
    def read_dir(self, cur_dir, path):
        self.database.list_files(cur_dir, path)
        
    def make_dir(self, cur_dir, path):
        self.database.make_dir(cur_dir, path)

    def del_dir(self, cur_dir, path):
        self.database.delete_dir(cur_dir, path)


class User:
    def __init__(self, username, fileSystem):
        self.username = username
        self.root_dir = '/{u}/'.format(u=username.lower())

    def rename_user(self, new_name):
        self.username = new_name
        self.root_dir = '/{u}/'.format(u=new_name.lower())


class DBInterface:
    def __init__(self, namenode):
        self.driver = GraphDatabase.driver(uri, auth=(username_db, password_db))
        self.namenode = namenode
        self.create_constraints()

    def create_constraints(self):
        query1 = """
                create constraint on (dir: Dir)
                assert dir.uuid is unique

                create constraint on (file: File)
                assert file.uuid is unique
                """
        self.driver.session().write_transaction(self.submit_query, query1)

        query2 = """
                call apoc.uuid.install('Dir')
                call.apoc.uuid.install('File')
                """
        self.driver.session().write_transaction(self.submit_query, query2)

    def add_root(self, name):
        query = """
                create (root: Dir {name: "{name}"})
                """.format(name=name)

        self.driver.session().write_transaction(self.submit_query, query)

    def is_fullpath(self, path):
        return True if path[0] == '/' else False

    def get_fullpath_as_list(self, cur_dir, path):
        fullpath = []
        if self.is_fullpath(path):
            # it's a full path => starts with a root
            fullpath = path.split('/')
            fullpath.remove('')
        else:
            # it's a relative path
            fullpath = path.split('/')
            fullpath.remove('')
            cur_dir_path = cur_dir.split('/')
            cur_dir_path.remove('')
            fullpath = cur_dir_path + fullpath

        return fullpath if self.namenode.user_exists(fullpath[0]) else print_error('root directory for this user does not exist')

    def get_fullpath_pairs(self, path):
        pairs = []
        for index in range(0, len(path)-1):
            pairs.append([path[index], path[index+1]])
        return pairs

    def submit_query(self, tx, query):
        result = tx.run(query)
        return result.single()

    def list_all(self, uuid="", fullpath=""):
        # specify either uuid or fullpath, not both, otherwise fullpath will have a priority
        if fullpath and not uuid:
            # if full path was specified
            result = self.path_exists(fullpath)
            if not result:
                print_error('path does not exist')
                return
            
            uuid, label = result[0], result[1]
            if not label == 'Dir':
                print_error('it is not a folder')
                return

        query = """
                match(n: Dir)-[:HAS]->(smt) 
                where n.uuid = "{uuid}"
                return smt.name, labels(smt)[0]
                """.format(uuid=uuid)

        # result will contains entries of type: [file/dir-name, label: Dir or File]
        result = self.driver.session().write_transaction(self.submit_query, query)
        return result

    def path_exists(self, fullpath, required_label=""):
        folders_pairs = self.get_fullpath_pairs(fullpath)
        continue_flag = False
        uuid = ""
        label = "" # will be set to "Dir" or "File"
        for pair in folders_pairs:
            if not continue_flag:
                return False

            query = """
                    match (folder1:Folder)-[:HAS]->(child)
                    where folder1.name = "{name1}" and child.name = "{name2}"
                    return folder1.name, child.name, child.uuid, labels(child)[0]
                    """.format(name1=pair[0], name2=pair[1])

            result = self.driver.session().write_transaction(self.submit_query, query)
            if result[0] == pair[0] and result[1] == pair[1]:
                continue_flag = True
                uuid = result[2] # should be uuid of the second dir/file
                label = result[3]

        if continue_flag and required_label and label == required_label:
            return uuid, label
        if continue_flag and not required_label:
            return uuid, label
        return False

    def is_name_unique(self, dir_uuid, new_name):
        files = self.list_all(uuid=dir_uuid)
        for [name, label] in files:
            if name == new_name:
                print_error('{type} with such name already exists'.format(type='file' if label == 'File' else 'directory')) 
                return False
        return True

    def create_file(self, name, cur_dir, path="", uuid=""):
        # uuid is uuid of the directory 
        if not uuid and path:
            fullpath = self.get_fullpath_as_list(cur_dir, path)
            result = self.path_exists(fullpath)
            if not result:
                print_error('path does not exist')
                return
            
            uuid, label = result[0], result[1]
            if not label == 'Dir':
                print_error('it is not a folder')
                return
        
        if not uuid and not path:
            print_error('path is not specified')
            return

        query = """
                match(n: Dir) where n.uuid = "{uuid}"
                create (child: File {name: "{filename}"})
                create (n)-[:HAS]->(child)
                """.format(uuid=uuid, filename=name)
        
        self.driver.session().write_transaction(self.submit_query, query)
        # datanodes

    def delete_file(self, cur_dir, path="", uuid=""):
        if not path and not uuid:
            print_error("")
            return

        if not uuid and path:
            fullpath = self.get_fullpath_as_list(cur_dir, path)
            result = self.path_exists(fullpath)
            if not result:
                print_error('path does not exist')
                return
            
            uuid, label = result[0], result[1]
            if not label == "File":
                print_error("file does not exist")
                return
        
        query = """
                match (file: File)
                where file.uuid = {uuid}
                detach delete (file)
                """.format(uuid=uuid)
        self.driver.session().write_transaction(self.submit_query, query)
        # datanodes

    def copy_file(self, cur_dir, path, copy_to_path, delete_original=False):
        fullpath1 = self.get_fullpath_as_list(cur_dir, path)
        fullpath2 = self.get_fullpath_as_list(cur_dir, copy_to_path)
        result1 = self.path_exists(fullpath1)
        result2 = self.path_exists(fullpath2)
        if not result1 or not result2:
            print_error('some fancy error cant copy')
            return
        
        uuid1, label1, uuid2, label2 = result1[0], result1[1], result2[0], result2[1]

        if not label2 == 'Dir':
            print_error('second path is not a directory')
            return

        if not label1 == 'File':
            print_error("it's not a file")
            return
        
        filename = fullpath1[len(fullpath1)-1]
        if not self.is_name_unique(uuid2, filename):
            print_error('file with this name already exists')
            return

        self.create_file(filename, cur_dir, uuid=uuid2)
        if delete_original:
            self.delete_file(cur_dir, uuid=uuid1)

    def move_file(self, cur_dir, path, move_to_path):
        self.copy_file(cur_dir, path, move_to_path, delete_original=True)   

    def list_files(self, cur_dir, path):
        fullpath = self.get_fullpath_as_list(cur_dir, path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            print_error("")
            return

        files = self.list_all(uuid=uuid)
        ##### return files as json

    def make_dir(self, cur_dir, path):
        # do you handle existence of chaining dirs?
        fullpath = self.get_fullpath_as_list(cur_dir, path)
        new_dir_name = fullpath.pop(len(fullpath)-1)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            print_error("")
            return

        if not self.is_name_unique(uuid, new_dir_name):
            print_error("")
            return
        
        query = """
                match (dir: Dir) where dir.uuid = "{uuid}"
                create (new_dir: Dir {name: "{name}"})
                create (dir)-[:HAS]->(new_dir)
                """.format(uuid=uuid, name=new_dir_name)

        self.driver.session().write_transaction(self.submit_query, query)

    def delete_dir(self, cur_dir, path):
        fullpath = self.get_fullpath_as_list(cur_dir, path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            print_error("")
            return

        files = self.list_all(uuid=uuid)
        permission = False
        if len(files) > 0:
            # ask for permission
            pass

        if not permission:
            return

        query = """
                match (dir: Dir)-[:HAS*0..]->(child) where dir.uuid = "{uuid}"
                detach delete (child)
                """.format(uuid=uuid)

        self.driver.session().write_transaction(self.submit_query, query)

    def close_connection(self):
        self.driver.close()


app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    namenode = Namenode()
    msg = request.json
    status, args = namenode.perform_action(msg.action, msg.args)
    return jsonify(status=status, args=args)

app.run(port=PORT)