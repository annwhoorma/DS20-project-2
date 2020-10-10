from neo4j import GraphDatabase
from errors import throw_error

# for neo4j
uri = "bolt://localhost:7687"
username_db = "neo4j"
password_db = "ohmyg0d"

class DBInterface:
    def __init__(self, namenode):
        self.driver = GraphDatabase.driver(uri, auth=(username_db, password_db))
        self.namenode = namenode
        self.create_constraints()

    def create_constraints(self):
        query1 = """
                create constraint if not exists on (dir: Dir)
                assert dir.uuid is unique
                """
        query2 = """
                create constraint if not exists on (file: File)
                assert file.uuid is unique
                """
        self.driver.session().write_transaction(self.submit_query, query1)
        self.driver.session().write_transaction(self.submit_query, query2)

        query3 = """
                call apoc.uuid.install('Dir')
                """
        query4 = """
                call apoc.uuid.install('File')
                """
        self.driver.session().write_transaction(self.submit_query, query3)
        self.driver.session().write_transaction(self.submit_query, query4)

    def get_fullpath_as_list(self, cur_dir):
        fullpath = []
        fullpath = cur_dir.split('/')
        while '' in fullpath:
            fullpath.remove('')
        
        return 0, fullpath

    def get_fullpath_pairs(self, fullpath):
        pairs = []
        if len(fullpath) == 1:
            return fullpath

        for index in range(0, len(fullpath)-1):
            pairs.append([fullpath[index], fullpath[index+1]])
        return pairs

    def submit_query(self, tx, query):
        return tx.run(query)

    def list_all(self, uuid="", fullpath=""):
        # specify either uuid or fullpath, not both, otherwise fullpath will have a priority
        if fullpath and not uuid:
            # if full path was specified
            result = self.path_exists(fullpath)
            if not result:
                return 1, throw_error("NO_SUCH_DIR")
            
            uuid, label = result[0], result[1]
            if not label == 'Dir':
                return 1, throw_error("NO_SUCH_DIR")

        query = """
                match(n: Dir)-[:HAS]->(smt) 
                where n.uuid = "{uuid}"
                return smt.name, labels(smt)[0]
                """.format(uuid=uuid)

        # result will contains entries of type: [file/dir-name, label: Dir or File]
        result = self.driver.session().write_transaction(self.submit_query, query)
        arg = [{"name": record[0], "type": record[1]} for record in result] if not result == None else []
        return 0, arg

    def path_exists(self, fullpath, required_label=""):
        while " " in fullpath: 
            fullpath.remove(" ")
        if len(fullpath) == 1:
            query = """
                    match (dir:Dir)
                    where dir.name = "{name}"
                    return dir.uuid, labels(dir)[0]
                    """.format(name=fullpath[0])
            result = self.driver.session().write_transaction(self.submit_query, query)
            return result.single()[0], result.single()[1]

        folders_pairs = self.get_fullpath_pairs(fullpath)
        print(folders_pairs)
        continue_flag = False
        uuid = ""
        label = "" # will be set to "Dir" or "File"
        for pair in folders_pairs:
            if not continue_flag:
                return 1, throw_error("NO_SUCH_DIR")

            query = """
                    match (folder1:Dir)-[:HAS]->(child)
                    where folder1.name = "{name1}" and child.name = "{name2}"
                    return folder1.name, child.name, child.uuid, labels(child)[0]
                    """.format(name1=pair[0], name2=pair[1])

            result = self.driver.session().write_transaction(self.submit_query, query)
            result = [[rec[0], rec[1], rec[2], rec[3]] for rec in result]
            if result[0][0] == pair[0] and result[0][1] == pair[1]:
                continue_flag = True
                uuid = result[0][2] # should be uuid of the second dir/file
                label = result[0][3]

        if continue_flag and required_label and label == required_label:
            return uuid, label
        if continue_flag and not required_label:
            return uuid, label
        return 1, throw_error("NO_SUCH_DIR")

    def is_name_unique(self, dir_uuid, new_name):
        res, files = self.list_all(uuid=dir_uuid)
        for [name, label] in files:
            if name == new_name:
                return False
        return True

    def are_two_fullpaths_same(self, fullpath1, fullpath2):
        if not len(fullpath1) == len(fullpath2) or not fullpath1[len(fullpath1)] == fullpath2[len(fullpath2)]:
            return False
        for depth in len(fullpath1):
            if not fullpath1[depth] == fullpath2[depth]:
                return False
        return True


    def add_root(self, name):
        query = """
                create (root: Dir {{name: "{name}", username: "{name}"}})
                """.format(name=name)

        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, "") if result.single() == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    def create_file(self, name, cur_dir, uuid=""):
        # uuid is uuid of the directory
        fullpath = []
        if not uuid:
            res, fullpath = self.get_fullpath_as_list(cur_dir)
            print("FULLPATH", fullpath)
            if not res == 0:
                # fullpath will contain an error in this case
                return 1, fullpath
            result = self.path_exists(fullpath)
            if not result:
                return 1, throw_error("NO_SUCH_DIR")
            
            uuid, label = result[0], result[1]
            print("UUID: ", uuid, "LABEL: ", label)
            if not label == 'Dir':
                return 1, throw_error("NO_SUCH_DIR")
        
        if not uuid:
            return 1, throw_error("DIR_NOT_SPECIFIED")
        query = """
                match(n: Dir) where n.uuid = "{uuid}"
                create (child: File {{name: "{filename}"}})
                create (n)-[:HAS]->(child)
                """.format(uuid=uuid, filename=name)
        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result.single() == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    def delete_file(self, cur_dir, uuid=""):
        fullpath = []

        if not uuid:
            res, fullpath = self.get_fullpath_as_list(cur_dir)
            if not res == 0:
                # fullpath will contain an error in this case
                return 1, fullpath
            result = self.path_exists(fullpath)
            if not result:
                return 1, throw_error("NO_SUCH_DIR")
            
            uuid, label = result[0], result[1]
            if not label == "File":
                return 1, throw_error("NO_SUCH_FILE")
        
        query = """
                match (file: File)
                where file.uuid = "{uuid}"
                detach delete (file)
                """.format(uuid=uuid)
        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result.single() == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    def copy_file(self, cur_dir, copy_to_path, delete_original=False):
        res1, fullpath1 = self.get_fullpath_as_list(cur_dir)
        res2, fullpath2 = self.get_fullpath_as_list(copy_to_path)
        # not sufficient check
        if not self.are_two_fullpaths_same(fullpath1, fullpath2):
            return 1, throw_error("NO_COPY_TO_ANOTHER_DIR")
        if not res1 == 0 or not res2 == 0:
            # fullpath1 will contain an error in this case
            return 1, throw_error("NO_SUCH_DIR")
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
        ''' commented because datanodes-side will handle the naming'''
        # if not self.is_name_unique(uuid2, filename):
        #     return 1, throw_error("NAME_EXISTS")

        res, fp = self.create_file(fullpath1[len(fullpath1)], cur_dir, uuid=uuid2)
        if res == 0:
            if delete_original:
                res1, fp1 = self.delete_file(cur_dir, uuid=uuid1)
                if res1 == 0:
                    return 0, [fullpath1, fullpath2]
            else:
                return 0, [fullpath1, fullpath2]
        return 1, throw_error("INVALID_REQUEST")

    def move_file(self, cur_dir, move_to_path):
        return self.copy_file(cur_dir, move_to_path, delete_original=True)

    def list_files(self, cur_dir):
        res, fullpath = self.get_fullpath_as_list(cur_dir)
        if not res == 0:
            # fullpath will contain an error in this case
            return 1, fullpath
        result = self.path_exists(fullpath)
        if not result:
            return 1, throw_error("NO_SUCH_DIR")
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            return 1, throw_error("NO_SUCH_DIR")

        return self.list_all(uuid=uuid)

    def make_dir(self, cur_dir):
        # do you handle existence of chaining dirs?
        res, fullpath = self.get_fullpath_as_list(cur_dir)
        if not res == 0:
            # fullpath will contain an error in this case
            return 1, fullpath
        new_dir_name = fullpath.pop(len(fullpath)-1)
        result = self.path_exists(fullpath)
        if not result:
            return 1, throw_error("NO_SUCH_DIR")
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            return 1, throw_error("INVALID_REQUEST")

        if not self.is_name_unique(uuid, new_dir_name):
            return 1, throw_error("DIR_EXISTS")
        
        query = """
                match (dir: Dir) where dir.uuid = "{uuid}"
                create (new_dir: Dir {{name: "{name}"}})
                create (dir)-[:HAS]->(new_dir)
                """.format(uuid=uuid, name=new_dir_name)

        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result.single() == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    def delete_dir(self, cur_dir):
        res, fullpath = self.get_fullpath_as_list(cur_dir)
        if not res == 0:
            # fullpath will contain an error in this case
            return 1, fullpath
        result = self.path_exists(fullpath)
        if not result:
            return 1, throw_error("NO_SUCH_DIR")
        uuid, label = result[0], result[1]
        if not label == 'Dir':
            return 1, throw_error("INVALID_REQUEST")
        query = """
                match (dir: Dir)-[:HAS*0..]->(child) where dir.uuid = "{uuid}"
                detach delete (child)
                """.format(uuid=uuid)

        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result.single() == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    def close_connection(self):
        self.driver.close()
