class DatanodeInterface:
    def __init__(self, namenode):
        self.namenode = namenode

    def compose_request(self, command, fields):
        args = {}
        if not command or not fields or not fields['user']:
            return 1

        user = fields['user']
            
        if fields['path']:
            args['path'] = fields['path']

        elif fields['src'] and fields['dst']:
            args['src'] = fields['src']
            args['dst'] = fields['dst']
        
        elif fields['message']:
            args['message'] = fields['message']

        return command, user, args
        # send request