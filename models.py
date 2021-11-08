import uuid
from app import db
from passlib.apps import custom_app_context as pwd_context
from datetime import datetime

def verify_password(password, password_hash):
    return pwd_context.verify(password, password_hash)


class Users(db.Model):
    __tablename__ = 'users'
    #_id = db.Column("id", db.Integer)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(128))
    token = db.Column(db.String(100))
    fb_token = db.Column(db.String(200), nullable = True, default = None)
    uuid = db.Column(db.String(10), nullable = False, primary_key = True)

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
    _id_friend1 = db.Column(db.String(10), db.ForeignKey('users.uuid'))
    _id_friend2 = db.Column(db.String(10), db.ForeignKey('users.uuid'))
    accepted = db.Column(db.Boolean, nullable= True, default = None)

    def __init__(self, id_friend1, id_friend2):
        self._id_friend1 = id_friend1
        self._id_friend2 = id_friend2
        #self.accepted = False
    
class Rooms(db.Model):
    __tablename__ = "rooms"
   # _id = db.Column("id", db.Integer)
    roomname = db.Column(db.String(100),primary_key = True)
    password_hash = db.Column(db.String(128))
    maxplayers = db.Column(db.Integer)
    minbet = db.Column(db.Integer)
    rounds = db.Column(db.Integer)
    curr_round = db.Column(db.Integer, nullable= True)
    lastresult = db.Column(db.Integer, nullable= True)
    voting = db.Column(db.Boolean)

    def __init__(self, roomname, maxplayers, minbet, rounds):
        self.roomname = roomname
        self.maxplayers = maxplayers
        self.minbet = minbet
        self.rounds = rounds
        self.curr_round = 1
        self.lastresult = None
        self.voting = True

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class UserRooms(db.Model):
    __tablename__ = "userrooms"
    _id = db.Column("id", db.Integer, primary_key = True)
    roomname = db.Column(db.String(100), db.ForeignKey("rooms.roomname"))
    uuid = db.Column(db.String(10), db.ForeignKey("users.uuid"))
    accepted = db.Column(db.Boolean, nullable= True)
    gatchas = db.Column(db.Integer)
    deleted = db.Column(db.Boolean)

    def __init__(self, roomname, uuid, accepted):
        self.roomname = roomname
        self.uuid = uuid
        self.accepted = accepted
        self.gatchas = 2000
        self.deleted = False

class UserVote(db.Model):
    __tablename__ = "uservote"
    _id = db.Column("id", db.Integer, primary_key = True)
    roomname = db.Column(db.String(100), db.ForeignKey("rooms.roomname"))
    uuid = db.Column(db.String(10), db.ForeignKey("users.uuid"))
    vote = db.Column(db.Integer)
    bet = db.Column(db.Integer)
    round = db.Column(db.Integer)

    def __init__(self, roomname, uuid, vote, bet, round):
        self.roomname = roomname
        self.uuid = uuid
        self.vote = vote
        self.bet = bet
        self.round = round

class UserStats(db.Model):
    __tablename__ = "userstats"
    _id = db.Column("id", db.Integer, primary_key = True)
    uuid = db.Column(db.String(10), db.ForeignKey("users.uuid"))
    vtry_pts = db.Column(db.Integer)
    total_games = db.Column(db.Integer)
    won_games = db.Column(db.Integer)
    bet_wins = db.Column(db.Integer)
    total_frnds =  db.Column(db.Integer)
    maxgatcha = db.Column(db.Integer)
    createdate = db.Column(db.String(20))

    def __init__(self, uuid):
        self.uuid = uuid
        self.vtry_pts = 0
        self.total_games = 0
        self.won_games = 0
        self.bet_wins = 0
        self.total_frnds = 0
        self.maxgatcha = 0
        self.createdate = datetime.now().strftime("%d-%b-%Y")


if __name__ == "__main__":
    db.create_all()