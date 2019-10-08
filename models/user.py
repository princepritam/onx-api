class User():
    
    def __init__(self, name,token,role):
        self.name = name
        self.token = token
        self.role = role

    def asdict(self):
        return {
            'name':self.name,
            'token':self.token,
            'role':self.role
        }


