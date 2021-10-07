import uuid
from app import db
from passlib.apps import custom_app_context as pwd_context

class User(db.Model):
    __tablename__ = 'user'
    _id = db.Column("id", db.Integer, primary_key = True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))
    token = db.Column(db.String(100))
    uuid = db.Column(db.String(10))

    def __init__(self, username):
        self.username = username
        self.token = str(uuid.uuid1())
        self.uuid = str(uuid.uuid4())[:8]

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class Friends(db.Model):
    __tablename__ = 'friends'
    _id = db.Column("id", db.Integer, primary_key = True)
    _id_friend1 = db.Column(db.String(10), db.ForeignKey('user.uuid'))
    _id_friend2 = db.Column(db.String(10), db.ForeignKey('user.uuid'))
    accepted = db.Column(db.Boolean)

    def __init__(self, id_friend1, id_friend2):
        self._id_friend1 = id_friend1
        self._id_friend2 = id_friend2
        self.accepted = False
    

if __name__ == "__main__":
    db.create_all()