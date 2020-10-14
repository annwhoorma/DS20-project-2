from neo4j import GraphDatabase
from neo4j import unit_of_work
from errors import throw_error
import time

# default settings for neo4j access
uri = "bolt://neo4j-database:7687"
username_db = "neo4j"
password_db = "ohmyg0d"

class DBInterface:
    def __init__(self, namenode):
        time.sleep(10)
        self.driver = GraphDatabase.driver(uri, auth=(username_db, password_db))
        self.create_constraints()

    '''
    create necessary constraints - create uuid for nodes with labels Dir and File
    '''
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

    '''
    @param: path - path in string representation
    @return: 0 - no error
    @return: fullpath - list of strings

    takes "anya/DS/ds.md" and returns (0, ["anya", "DS", "ds.md"])
    '''
    def get_fullpath_as_list(self, path):
        fullpath = []
        fullpath = path.split('/')
        while '' in fullpath:
            fullpath.remove('')
        
        return 0, fullpath

    '''
    @param: fullpath - path in list representation
    @return: pairs - list of pairs of fullpath

    takes ["anya", "DS", "ds.md"] and returns [["anya", "DS"], ["DS", "ds.md"]]
    '''
    def get_fullpath_pairs(self, fullpath):
        pairs = []
        if len(fullpath) == 1:
            return fullpath

        for index in range(0, len(fullpath)-1):
            pairs.append([fullpath[index], fullpath[index+1]])
        return pairs

    '''
    @param: tx - a callback to read or write a transaction
    @param: query - the text of the query
    @param: list_all - optional, will represent result in a way that self.list_all() needs
    @param: path_ex - optional, will represent result in a way that self.path_exists() needs
    @return: None or one of the optional representations
    '''
    def submit_query(self, tx, query, list_all=False, path_ex=False):
        res = tx.run(query)
        if list_all:
            return [{"name": record[0], "type": record[1]} for record in res]
        if path_ex:
            tmp = [[rec[0], rec[1], rec[2], rec[3]] for rec in res]
            return tmp
        return res.single()

    '''
    @param: uuid - optional, uuid of the directory if such is known ot the caller
    @param: fullpath - fullpath in list representation
    @return: 0 if no error occured and 1 otherwise
    @return: directory entries if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def list_all(self, uuid=None, fullpath=None):
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

        result = self.driver.session().read_transaction(self.submit_query, query, list_all=True)
        return 0, result

    '''
    @param: fullpath - fullpath in list representation
    @param: required_label - can be 'File' or 'Dir'
    @return: uuid of the requested entry if no error occured and 1 otherwise
    @return: label of the requested entry if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def path_exists(self, fullpath, required_label=""):
        while " " in fullpath: 
            fullpath.remove(" ")
        if len(fullpath) == 1:
            query = """
                    match (dir:Dir)
                    where dir.name = "{name}"
                    return dir.uuid, labels(dir)[0]
                    """.format(name=fullpath[0])
            with self.driver.session() as session:
                sing = session.read_transaction(self.submit_query, query)
            return sing[0], sing[1]

        folders_pairs = self.get_fullpath_pairs(fullpath)
        print(folders_pairs)
        continue_flag = True
        uuid = ""
        label = "" # will be set to "Dir" or "File"
        for pair in folders_pairs:
            print("PAIR", pair)
            if not continue_flag:
                return 1, throw_error("NO_SUCH_DIR")

            query = """
                    match (folder1:Dir)-[:HAS]->(child)
                    where folder1.name = "{name1}" and child.name = "{name2}"
                    return folder1.name, child.name, child.uuid, labels(child)[0]
                    """.format(name1=pair[0], name2=pair[1])

            result = self.driver.session().read_transaction(self.submit_query, query, path_ex=True)
            if len(result) == 0:
                print("HEERER ER")
                return 1, throw_error("NO_SUCH_DIR")
            if result[0][0] == pair[0] and result[0][1] == pair[1]:
                continue_flag = True
                uuid = result[0][2] # should be uuid of the second dir/file
                label = result[0][3]
            else:
                return 1, throw_error("NO_SUCH_DIR")

        if continue_flag and required_label and label == required_label:
            return uuid, label
        if continue_flag and not required_label:
            return uuid, label
        return 1, throw_error("NO_SUCH_DIR")

    '''
    @param: name - username to be added as yet another root
    @return: 0 if no error occured, 1 otherwise
    @return: "" if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def add_root(self, name):
        query = """
                create (root: Dir {name: "{{name}}", username: "{{name}}"})
                """.format(name=name)

        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, "") if result == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    '''
    @param: cur_dir - string path to the file including its name
    @return: 0 if no error occured, 1 otherwise
    @return: "" if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def create_file(self, cur_dir):
        # uuid is uuid of the directory
        filename = ""
        fullpath = []
        res, fullpath = self.get_fullpath_as_list(cur_dir)
        if not res == 0:
            # fullpath will contain an error in this case
            return 1, fullpath
        filename = fullpath.pop(len(fullpath)-1)
        result = self.path_exists(fullpath)
        if not result:
            return 1, throw_error("NO_SUCH_DIR")

        uuid, label = result[0], result[1]
        print("UUID: ", uuid, "LABEL: ", label)
        if not label == 'Dir':
            return 1, throw_error("NO_SUCH_DIR")
        
        query = """
                match(n: Dir) where n.uuid = "{uuid}"
                create (child: File {{name: "{filename}"}})
                create (n)-[:HAS]->(child)
                """.format(uuid=uuid, filename=filename)
        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    '''
    @param: cur_dir - string path to the file including its name
    @return: 0 if no error occured, 1 otherwise
    @return: fullpath to the file in list representation if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def delete_file(self, cur_dir):
        fullpath = []
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
        return (0, fullpath) if result == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    '''
    @param: cur_dir - string path to the file including its name
    
    makes a call to another function that returns the results
    '''
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

    '''
    @param: cur_dir - string path to the file including its name
    @return: 0 if no error occured, 1 otherwise
    @return: fullpath to the file in list representation if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
    def make_dir(self, cur_dir):
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
        
        query = """
                match (dir: Dir) where dir.uuid = "{uuid}"
                create (new_dir: Dir {{name: "{name}"}})
                create (dir)-[:HAS]->(new_dir)
                """.format(uuid=uuid, name=new_dir_name)

        result = self.driver.session().write_transaction(self.submit_query, query)
        return (0, fullpath) if result == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    '''
    @param: cur_dir - string path to the file including its name
    @return: 0 if no error occured, 1 otherwise
    @return: fullpath to the file in list representation if no error occured, error message otherwise

    in case of no error it will return {[{"name": "file1.txt", "type": "File"}, ...]} 
    '''
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
        return (0, fullpath) if result == None else (1, throw_error("QUERY_DID_NOT_SUCCEED"))

    '''
    close the connection to the neo4j database
    '''
    def close_connection(self):
        self.driver.close()
