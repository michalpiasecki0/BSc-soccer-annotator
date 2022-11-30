class User:

    def __init__(self,login,email,password):
        self.login = login
        self.email = email
        #password to be hashed
        self.password = password
        self.authenticated = False

    def __repr__(self):
        return "User(Login '{}',Email '{}',Authenticated '{}')".format(self.login,self.email,
                self.authenticated)