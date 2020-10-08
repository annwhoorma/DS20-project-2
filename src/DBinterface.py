from neo4j import GraphDatabase
from errors import throw_error

# for neo4j
uri = "bolt://localhost:7687"
username_db = "neo4j"
password_db = "ohmyg0d"

def print_error(message):
    print("ERROR: {m}".format(m=message)) if message else print('ERROR')
    # return None

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
                create (root: Dir {name: "/", username: "{name}"})
                """.format(username=name)

        self.driver.session().write_transaction(self.submit_query, query)

    def is_fullpath(self, path):
        return True if path[0] == '/' else False

    def get_fullpath_as_list(self, cur_dir, path):
        fullpath = []
        fullpath = path.split('/')
        while '' in fullpath:
            fullpath.remove('')

        if not self.is_fullpath(path):
            # it's a relative path
            cur_dir_path = cur_dir.split('/')
            while '' in cur_dir_path:
                cur_dir_path.remove('')
            fullpath = cur_dir_path + fullpath

        if not self.namenode.user_exists(fullpath[0]):
            return 1, throw_error("NO_SUCH_USER")

        return fullpath

    def get_fullpath_pairs(self, fullpath):
        pairs = []
        if len(fullpath) == 1:
            pairs.append(["/", fullpath[0]])
            return pairs

        for index in range(0, len(fullpath)-1):
            pairs.append([fullpath[index], fullpath[index+1]])
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
                    match (folder1:Dir)-[:HAS]->(child)
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
                return False
        return True


    def create_file(self, name, cur_dir, path="", uuid=""):
        # uuid is uuid of the directory 
        if not uuid and path:
            fullpath = self.get_fullpath_as_list(cur_dir, path)
            result = self.path_exists(fullpath)
            if not result:
                return 1, throw_error("NO_SUCH_DIR")
            
            uuid, label = result[0], result[1]
            if not label == 'Dir':
                return 1, throw_error("NO_SUCH_DIR")
        
        if not uuid and not path:
            return 1, throw_error("DIR_NOT_SPECIFIED")

        query = """
                match(n: Dir) where n.uuid = "{uuid}"
                create (child: File {name: "{filename}"})
                create (n)-[:HAS]->(child)
                """.format(uuid=uuid, filename=name)
        self.driver.session().write_transaction(self.submit_query, query)
        return 0, fullpath

    def delete_file(self, cur_dir, path="", uuid=""):
        if not path and not uuid:
            return 1, throw_error("DIR_NOT_SPECIFIED")

        if not uuid and path:
            fullpath = self.get_fullpath_as_list(cur_dir, path)
            result = self.path_exists(fullpath)
            if not result:
                return 1, throw_error("NO_SUCH_DIR")
            
            uuid, label = result[0], result[1]
            if not label == "File":
                return 1, throw_error("NO_SUCH_FILE")
        
        query = """
                match (file: File)
                where file.uuid = {uuid}
                detach delete (file)
                """.format(uuid=uuid)
        self.driver.session().write_transaction(self.submit_query, query)
        return 0, fullpath

    def copy_file(self, cur_dir, path, copy_to_path, delete_original=False):
        fullpath1 = self.get_fullpath_as_list(cur_dir, path)
        fullpath2 = self.get_fullpath_as_list(cur_dir, copy_to_path)
        result1 = self.path_exists(fullpath1)
        result2 = self.path_exists(fullpath2)
        if not result1 or not result2:
            return 1, throw_error("NO_SUCH_DIR")
        
        uuid1, label1, uuid2, label2 = result1[0], result1[1], result2[0], result2[1]

        if not label2 == 'Dir':
            return 1, throw_error("NO_SUCH_DIR")

        if not label1 == 'File':
            return 1, throw_error("NO_SUCH_FILE")
        
        filename = fullpath1[len(fullpath1)-1]
        if not self.is_name_unique(uuid2, filename):
            return 1, throw_error("NAME_EXISTS")

        self.create_file(filename, cur_dir, uuid=uuid2)
        if delete_original:
            self.delete_file(cur_dir, uuid=uuid1)
        return 0, [fullpath1, fullpath2]

    def move_file(self, cur_dir, path, move_to_path):
        return self.copy_file(cur_dir, path, move_to_path, delete_original=True)

    def list_files(self, cur_dir, path):
        fullpath = self.get_fullpath_as_list(cur_dir, path)
        result = self.path_exists(fullpath)
        if not result:
            return 1, throw_error("NO_SUCH_DIR")
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            return 1, throw_error("NO_SUCH_DIR")

        files = self.list_all(uuid=uuid)
        return 0, files

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
        return 0, fullpath

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
        return 0, fullpath

    def close_connection(self):
        self.driver.close()
