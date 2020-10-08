class User:
    def __init__(self, username, namenode):
        self.username = username
        self.namenode = namenode
        self.root_dir = '/{u}/'.format(u=username.lower())

