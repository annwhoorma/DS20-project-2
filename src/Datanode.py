class Datanode:
    def __init__(self, ip, node_type="slave"):
        self.ip = ip
        self.type = node_type
        self.status = "active"

    def promote(self):
        self.type = "master"
    
    def demote(self):
        self.type = "slave"