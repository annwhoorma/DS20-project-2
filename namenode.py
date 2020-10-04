# path is a string like "/anya/folder/file" or "folder/hey" which can contain relative or full path
# fullpath is a list like ["anya", "folder", "file"] and it's always a full path

from neo4j import GraphDatabase
import http.server
import socketserver
import json

CLIENT_PORT = 8080
DATANODE_PORT = 0000 # 1?

# for neo4j
uri = "bolt://localhost:7687"
username = "neo4j"
password = "ohmyg0d"

def print_error(message):
    print("ERROR: {m}".format(m=message)) if message else print('ERROR')
    # return None


class ClientInterface(http.server.BaseHTTPRequestHandler):
    # namenode <-> client interface
    def __init__(self):
        pass

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()

    def do_GET(self):
        content_length = int(self.headers['content-length'])
        content = self.rfile.read(content_length)
        
        msg = json.loads(json.loads(content.decode()))
        print(type(msg), msg)
        
        if msg["action"] == "auth":
            if msg["args"]["login"] == "Dmmc":
                response = json.dumps({"status":"ok"})
            else:
                response = json.dumps({"status":"invalid user"})
        else:
            response = json.dumps({"status":"unknown command"})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.encode())


class DatanodeInterface(http.server.BaseHTTPRequestHandler):
    # namenode <-> datanode interface
    def __init__(self):
        pass


class Namenode:
    # namenode <-> datanode interface
    def __init__(self, filesystem, server, client):
        self.client_interface = ClientInterface()
        with socketserver.TCPServer(("", CLIENT_PORT), self.client_interface) as httpd_client:
            print("Just another not suspicious fake namenode at the port: ", CLIENT_PORT)
            httpd_client.serve_forever()

        self.dataNode_interface = DatanodeInterface()
        with socketserver.TCPServer(("", DATANODE_PORT), self.dataNode_interface) as httpd_datanode:
            print("Just another not suspicious fake namenode at the port: ", DATANODE_PORT)
            httpd_datanode.serve_forever()

        self.db_interface = DBInterface(self)
        self.users = []

    def initialize(self, username):
            # check username uniquness
        for user in self.users:
            if user.name == username:
                print_error('user with this name already exists')
                return
        self.add_user(username)
        self.db_interface.add_root(username)

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


class User:
    def __init__(self, username, fileSystem):
        self.username = username
        self.root_dir = '/{u}/'.format(u=username.lower())

    def rename_user(self, new_name):
        self.username = new_name
        self.root_dir = '/{u}/'.format(u=new_name.lower())

class DBInterface:
    def __init__(self, namenode):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.namenode = namenode
        self.cur_dir = "/"
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

    def get_fullpath_as_list(self, path):
        fullpath = []
        if self.is_fullpath(path):
            # it's a full path => starts with a root
            fullpath = path.split('/')
            fullpath.remove('')
        else:
            # it's a relative path
            fullpath = path.split('/')
            fullpath.remove('')
            cur_dir_path = self.cur_dir.split('/')
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

    def path_exists(self, fullpath):
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

        if continue_flag:
            return uuid, label
        return False

    def is_name_unique(self, dir_uuid, new_name):
        files = self.list_all(uuid=dir_uuid)
        for [name, label] in files:
            if name == new_name:
                print_error('{type} with such name already exists'.format(type='file' if label == 'File' else 'directory')) 
                return False
        return True

    def create_file(self, name, path="", uuid=""):
        # uuid is uuid of the directory 
        if not uuid and path:
            fullpath = self.get_fullpath_as_list(path)
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
        
    def read_file(self, path):
        fullpath = self.get_fullpath_as_list(path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        # datanodes

    def write_file(self, path):
        fullpath = self.get_fullpath_as_list(path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        uuid, label = result[0], result[1]
        if not label == 'File':
            print_error("")
            return
        # datanodes

    def delete_file(self, path="", uuid=""):
        if not path and not uuid:
            print_error("")
            return

        if not uuid and path:
            fullpath = self.get_fullpath_as_list(path)
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

    def get_file_info(self, path):
        fullpath = self.get_fullpath_as_list(path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        
        uuid, label = result[0], result[1]
        if not label == "File":
            print_error("file does not exist")
            return
        
        # datanodes

    def copy_file(self, path, copy_to_path, delete_original=False):
        fullpath1 = self.get_fullpath_as_list(path)
        fullpath2 = self.get_fullpath_as_list(copy_to_path)
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

        self.create_file(filename, uuid=uuid2)
        if delete_original:
            self.delete_file(uuid=uuid1)

    def move_file(self, path, move_to_path):
        self.copy_file(path, move_to_path, delete_original=True)

    def change_directory(self, path):
        fullpath = self.get_fullpath_as_list(path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        
        uuid, label = result[0], result[1]
        if not label == "Dir":
            print_error("path does not exist")
            return
        
        self.cur_dir = ""
        for entry in fullpath:
            self.cur_dir += '/{e}'.format(e=entry)        

    def list_files(self, path):
        fullpath = self.get_fullpath_as_list(path)
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

    def make_dir(self, path, name):
        fullpath = self.get_fullpath_as_list(path)
        result = self.path_exists(fullpath)
        if not result:
            print_error('path does not exist')
            return
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            print_error("")
            return

        if not self.is_name_unique(uuid, name):
            print_error("")
            return
        
        query = """
                match (dir: Dir) where dir.uuid = "{uuid}"
                create (new_dir: Dir {name: "{name}"})
                create (dir)-[:HAS]->(new_dir)
                """.format(uuid=uuid, name=name)

        self.driver.session().write_transaction(self.submit_query, query)

    def delete_dir(self, path):
        fullpath = self.get_fullpath_as_list(path)
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


    
