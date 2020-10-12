'''
the class to describe a datanode
'''
class Datanode:
    '''
    @param: ip - node ip
    @param: node_type - "slave" or "master"
    '''
    def __init__(self, ip, node_type="slave"):
        self.ip = ip
        self.type = node_type
        # status: active, inactive
        self.status = "active"
    '''
    make the node the master
    '''
    def promote(self):
        self.type = "master"
    '''
    make the node a slave
    '''
    def demote(self):
        self.type = "slave"