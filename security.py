from flask_bcrypt import Bcrypt


class Security:
    def __init__(self,app):
        self.bcrypt = Bcrypt(app)

    #get a hash from a string
    def get_hashed(self,pt_string):
        pw_hash = self.bcrypt.generate_password_hash(pt_string)
        return pw_hash

    #check a hash and a given string to see if they are the same
    def check_hash(self,pt_string,hp):
        return self.bcrypt.check_password_hash(hp,pt_string)


