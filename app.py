from logging import FATAL
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import random

if __name__ == "__main__":
    from models import *


app = Flask(__name__)
app.secret_key = "donRecabarren"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.app = app


@app.route('/test', methods=['GET'])
def get_test():
    return jsonify({'msg': "This is a test message", "value":"#81F8D2"}), 200


#https://reqbin.com/


@app.route('/login', methods=['POST'])
def get_login():
    try:
        name = request.json['Username']
        pswd = request.json['Password']
        fb_token = request.json['fb_token']
    except:
        return jsonify({'status': False, 'token': '', 'user_id':''}), 400 #BAD REQUEST null values or werent passed

    print(fb_token)
    if not name or not pswd or not fb_token:
        return jsonify({'status': False, 'token': '', 'user_id':''}), 200 #BAD REQUEST null values or werent passed

    usr = User.query.filter_by(username = name).first()
    if not usr or not usr.verify_password(pswd):
        return jsonify({'status': False, 'token': '', 'user_id':''}), 404 #USER DOESNT EXIST or BAD PASSWORD
    else:
        usr.fb_token = fb_token
        db.session.merge(usr)
        db.session.commit()
        return jsonify({'status': True, 'token': usr.token, 'user_id': usr.uuid}), 200 #OK


@app.route('/signup', methods=['POST'])
def setSignUp():

    try:
        name = request.json['Username']
        pswd = request.json['Password']
    except:
        return jsonify({'status': False}), 400 #BAD REQUEST null values or werent passed

    if not name or not pswd:
        return jsonify({'status': False}), 400 #BAD REQUEST empty parameters

    found_user = User.query.filter_by(username = name).first()
    if found_user:
        return jsonify({'status': False}), 409 # Duplicate exists
    else:
        usr = User(name)
        usr.hash_password(pswd)
        db.session.add(usr)
        db.session.commit()
        usrStats = UserStats(usr.uuid)
        db.session.add(usrStats)
        db.session.commit()
        return jsonify({'status': True}) ,201 # User created

@app.route('/addFriend', methods=['POST'])
def addFriend():
    try:
        friend_id = request.json['friend_id']
    except:
        return jsonify({'status': False, 'msg': 'No ID received', 'fb_token':''}), 200 #BAD REQUEST null values or werent passed
    print(friend_id)    
	
    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'status': False, 'msg':'Token isnt valid', 'fb_token':''}), 200 #BAD REQUEST null values or werent passed

    user_id = found_user.uuid
	
    friend = User.query.filter(User.uuid == friend_id).first()
    if not friend:
        return jsonify({"status":False, "msg":"Friend doesn't exist", 'fb_token':''}), 200
        
    #friendQuery = Friends.query.filter(((Friends._id_friend1 == user_id )|(Friends._id_friend2 == friend_id)) | ((Friends._id_friend1 == friend_id )|(Friends._id_friend2 == user_id)) ).first()
    friendQ1 = Friends.query.filter(Friends._id_friend1 == user_id, Friends._id_friend2 == friend_id).first()
    friendQ2 = Friends.query.filter(Friends._id_friend1 == friend_id, Friends._id_friend2 == user_id).first()
    #print(friendQ1)
    #print(friendQ2._id_friend1, friendQ2._id_friend2)    

    if not friendQ1 and not friendQ2:
        friend = Friends(user_id, friend_id)
        db.session.add(friend)
        db.session.commit()
        queryUser = User.query.filter_by(uuid = friend_id).first()
        return jsonify({'status': True, 'msg':'Success', 'fb_token':queryUser.fb_token}), 200 #OK
    else:
        return jsonify({'status': False , 'msg': 'Already added', 'fb_token':''}) , 200 # Duplicate

@app.route('/getRequests', methods=['GET'])
def getRequests():
    '''
    try:
        user_id = request.view_args['user_id']
    except:
        return jsonify({'friends': {}}), 400 #BAD REQUEST null values or werent passed
    '''
    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'friends': {}}), 400 #BAD REQUEST null values or werent passed
    user_id = found_user.uuid


    friends = Friends.query.filter(Friends._id_friend2 == user_id, Friends.accepted == None).all()
    requests = []
    for friend in friends:
        if friend._id_friend2 == user_id:
            friend_id = friend._id_friend1
            usr = User.query.filter_by(uuid = friend_id).first()
            requests.append({"friend_id":friend_id, "Username":usr.username})


    return jsonify({"friends":requests}), 200 #OK

@app.route('/friendResponse', methods=['POST'])
def friendResponse():
    try:
        friend_id = request.json['friend_id']
        response = request.json['response'] #Boolean
    except:
        return jsonify({'status': False, "msg": "Bad parameters"}), 200 #BAD REQUEST null values or werent passed

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'status': False, "msg":"Token isn't valid"}), 200 #BAD REQUEST null values or werent passed
    user_id = found_user.uuid
    

    friend = Friends.query.filter_by(_id_friend1 = friend_id, _id_friend2 = user_id).first()
    if not friend:
        return jsonify({"status":False, "msg":"Request is not valid anymore"}), 200 

    if response: #ACCEPTED
        friend.accepted = True
        db.session.merge(friend)
        db.session.commit()
        f1 = UserStats(user_id)
        f2 = UserStats(friend_id)
        f1.total_frnds = f1.total_frnds + 1
        db.session.merge(f1)
        db.session.commit()
        f2.total_frnds = f2.total_frnds + 1
        db.session.merge(f2)
        db.session.commit()
    else: #DENIED
        friend.accepted = False
        db.session.merge(friend)
        db.session.commit()

    return jsonify({"status":friend.accepted, "msg":"Success"}), 200  #OK

@app.route('/friendList', methods=['GET'])
def friendList():
    token = request.headers.get('token')
    found_user = User.query.filter(User.token == token).first()
    if not found_user:
        return jsonify({'friends': [], "msg":"Token isnt valid"}), 200 #BAD REQUEST null values or werent passed

    user_id = (User.query.filter_by(token = token).first()).uuid

    friends = Friends.query.filter(((Friends._id_friend1 == user_id )|(Friends._id_friend2 == user_id)) & (Friends.accepted == True)).all()	

    friendList = []
    for friend in friends:
        if friend._id_friend1 != user_id:
            friend_id = friend._id_friend1
        else:
            friend_id = friend._id_friend2

        usr = User.query.filter_by(uuid = friend_id).first()
        friendList.append({"friend_id":friend_id, "Username":usr.username})

    return jsonify({"friends":friendList, "msg":"Success"}), 200 #OK

@app.route('/getRooms', methods=['GET'])
def getRooms():
    #RETURNS LIST OF ROOMS OF A USER
    print("GET ROOMS")
    token = request.headers.get('token')
    print(token)
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 200 #BAD REQUEST null values or werent passed
    user_uuid = found_user.uuid
    rooms = UserRooms.query.filter(UserRooms.uuid == user_uuid, UserRooms.accepted == True).all()
    roomList = []
    for room in rooms:
        amountPlayers = UserRooms.query.filter(UserRooms.roomName == room.roomName, UserRooms.accepted == True).count()
        maxSize = Rooms.query.filter(Rooms.roomName == room.roomName).first()
        roomList.append({"roomName":room.roomName, "currSize":amountPlayers, "maxPlayers":maxSize.maxPlayers})

    print(rooms)
    return jsonify({"rooms":roomList, "msg":"Success"}), 200 #OK

@app.route('/getRoom/<roomName>', methods=['GET'])
def getRoom(roomName):
    #RETURNS LIST OF USERS IN A ROOM
    try:
        roomName = request.view_args['roomName']
    except:
        return jsonify({'room': [], "msg":"Bad parameters"}), 400 #BAD REQUEST null values or werent passed

    if roomName == "" or roomName == None:
        return jsonify({'room':[], "msg":"Empty parameters"}), 400

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'room': [], "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_id = found_user.uuid

    mems = []
    members = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.accepted == True).all()
    for member in members:
        usrName = User.query.filter(User.uuid == member.uuid).first()
        mems.append({"Username": usrName.username, "user_id": member.uuid, "gatchas": member.gatchas})

    room = Rooms.query.filter(Rooms.roomName == roomName).first()

    print({"room":mems, "msg":"Success", "lastResult": room.lastResult, "curr_round": room.curr_round, "voting":room.voting})
    return jsonify({"room":mems, "msg":"Success", "lastResult": room.lastResult, "curr_round": room.curr_round, "voting":room.voting}), 200 #OK



@app.route('/roomInvite', methods=['POST'])
def roomInvite():
    try:
        friend_id = request.json['friend_id']
        roomName = request.json['roomName']
    except:
        return jsonify({'status': False, "msg":"Bad parameters", 'fb_token':''}), 200 #BAD REQUEST null values or werent passed

    if friend_id == "" or friend_id == None or roomName == "" or roomName == "None":
        return jsonify({"status":False, "msg":"Empty parameters", 'fb_token':''}), 200

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'status': False, "msg":"Token isn't valid", 'fb_token':''}), 200 #BAD REQUEST null values or werent passed

    usrRoomQuery = UserRooms.query.filter(UserRooms.roomName == roomName , UserRooms.uuid == found_user.uuid).first() #if inviter is in room
    usrRoomQuery2 = UserRooms.query.filter(UserRooms.roomName == roomName , UserRooms.uuid == friend_id, UserRooms.accepted == None).first() # if friend is in room
    if not usrRoomQuery: #User inviter isnt in this room
        return jsonify({'status': False, "msg": "User is not in room", 'fb_token':''}), 200 # BAD REQUEST
    elif usrRoomQuery2:
        return jsonify({'status': False, "msg": "Friend is already invited", 'fb_token':''}), 200 # BAD REQUEST, may trigger if already invited or is in room,check later
    else:
        #CHECK SIZE OF PLAYERS IN ROOM FIRST
        room = Rooms.query.filter(Rooms.roomName == roomName).first()
        roomQuery = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.accepted == True).count()
        if room.maxPlayers < roomQuery:
            return jsonify({'status': False, "msg": "Room full", 'fb_token':''}), 200 # ROOM FULL

        usrRooms = UserRooms(roomName, friend_id, None) # accepted false
        db.session.add(usrRooms)
        db.session.commit()
        queryUser = User.query.filter_by(uuid = friend_id).first()
        return jsonify({'status': True, "msg":"Invite successful", 'fb_token': queryUser.fb_token}) , 200 # OK

@app.route('/roomResponse', methods=['POST'])
def roomResponse():
    try:
        roomName = request.json["roomName"]
        response = request.json['response'] #Boolean
    except:
        return jsonify({'status': False, "msg":"Bad parameters"}), 200 #BAD REQUEST null values or werent passed

    if roomName == "" or roomName == None or response == "" or response == None:
        return jsonify({'status':False,"msg":"Empty parameters"}), 200

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'status': False, "msg":"Token isn't valid"}), 200 #BAD REQUEST null values or werent passed
    user_id = found_user.uuid

    room = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.uuid == user_id).first()
    
    print(room)
    if response: #Join
        count = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.accepted == True).count()
        maxSize = (Rooms.query.filter(Rooms.roomName == roomName).first()).maxPlayers
        if maxSize <= count:
            print(maxSize, count, "FULL")
            return jsonify({'status': False, "msg":"Room full"}), 200 #ROOM FULL
        else:
            print("ACCEPT")
            room.accepted = True
            db.session.merge(room)
            db.session.commit()
            return jsonify({'status':True, 'msg':"Joined room"}), 200 #OK
    else: #DENY
        print("DENY")
        room.accepted = False
        db.session.merge(room)
        db.session.commit()
        return jsonify({'status':True, 'msg':"Denied room"}), 200 #OK


@app.route('/roomRequests', methods=['GET'])
def roomInvs():

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token).first()
    if not found_user:
        return jsonify({'status': False, "msg":"Bad parameters"}), 200 #BAD REQUEST null values or werent passed
    user_id = found_user.uuid

    rooms = UserRooms.query.filter(UserRooms.uuid == user_id, UserRooms.accepted == None).all()

    requests = []

    for room in rooms:
        requests.append({"roomName":room.roomName})


    return jsonify({"rooms":requests, "msg":"Success"}),200

@app.route('/createRoom', methods=['POST'])
def createRoom():
    try:
        roomName = request.json['roomName']
        pswd = request.json['Password']
        maxPlayers = request.json['maxPlayers']
        minBet = request.json['minBet']
        rounds = request.json['rounds']
    except:
        return jsonify({'status': False, "msg":"Bad parameters"}), 200 #BAD REQUEST null values or werent passed

    if not roomName or not pswd or not maxPlayers or not minBet or not rounds:
        return jsonify({'status': False, "msg":"Empty parameters"}), 200 #BAD REQUEST empty parameters
    
    token = request.headers.get('token')
    found_user = User.query.filter(User.token == token).first()
    if not found_user:
        return jsonify({"status":False, "msg":"Token isn't valid"}), 200 #TOKEN DOESNT EXIST

    query = Rooms.query.filter_by(roomName = roomName).first()
    if query:
        return jsonify({"status":False, "msg":"Room already exists"}), 200 #ROOM ALREADY EXISTS

    room = Rooms(roomName, maxPlayers, minBet, rounds)
    room.hash_password(pswd)
    db.session.add(room)
    db.session.commit() #ROOM ADDED

    userRoom = UserRooms(roomName, found_user.uuid, True)
    db.session.add(userRoom)
    db.session.commit() #USERROOM ADDED
    
    

    return jsonify({"status":True, "msg":"Room created"}), 200 #OK

def voteResult(rng, vote):
    '''
        01
        234
        56789
    '''
    nums = [[0,1], [2,3,4], [5,6,7,8,9]]

    if 10 <= vote <= 12:
        if vote == 10:
            if rng in nums[0]:
                return 3
            return -1
        elif vote == 11:
            if rng in nums[1]:
                return 2
            return -1
        elif vote == 12:
            if rng in nums[2]:
                return 1
            return -1
    else:
        if vote == rng:
            return 5
        return -1


@app.route('/vote', methods = ['POST'])
def vote():
    try:
        roomName = request.json['roomName']
        bet = request.json['bet']
        vote = request.json['vote']
        round = request.json['round']
    except:
        return jsonify({'status': False, "msg":"Bad parameters"}), 400 #BAD REQUEST null values or werent passed

    if not roomName or not vote or not bet or not round:
        return jsonify({'status': False, "msg":"Empty parameters"}), 400 #BAD REQUEST empty parameters
    
    token = request.headers.get('token')
    found_user = User.query.filter(User.token == token).first()
    if not found_user:
        return jsonify({"status":False, "msg":"Token isn't valid"}), 404 #TOKEN DOESNT EXIST

    user_id = found_user.uuid
    voteCheck = UserVote.query.filter(UserVote.uuid == user_id, UserVote.round == round, UserVote.roomName == roomName).first()
    print(f"Vote query: {voteCheck} - uuid:{user_id} - round: {round} - roomName: {roomName}")  
    if not voteCheck:
        room = Rooms.query.filter(Rooms.roomName == roomName).first() #puedo conseguir, maxPlayers, rounds, curr round, voting y lastResult
        if not room.voting: # no se puede votar mas
            return jsonify({"status":False, "msg":"Room's closed!"}), 400 #Room's closed!

        usrVote = UserVote(roomName, user_id, vote, bet, round) #roomName, uuid, vote, bet, round
        db.session.add(usrVote)
        db.session.commit() #USERVOTE ADDED
        
        votes = UserVote.query.filter(UserVote.roomName == roomName, UserVote.round == room.curr_round).all() #obtener todos los votos de la ronda actual
        count = UserVote.query.filter(UserVote.roomName == roomName, UserVote.round == room.curr_round).count() #cantidad de votos en ronda actual
        if room.maxPlayers == count: #cantidad votos = cantidad de jugadores
            rng = random.randint(0,9)
            deadPlayers = 0
            for vote in votes:
                usrRoom = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.uuid == vote.uuid, UserRooms.accepted ==True).first() #conseguir gatchas
                if usrRoom:
                    print(f"Vote {vote.vote}")
                    result = voteResult(rng, vote.vote)
                    if result > 0:
                        usrStat = UserStats.query.filter(UserStats.uuid == vote.uuid).first()
                        usrStat.bet_wins = usrStat.bet_wins + 1 # add bet wins
                        db.session.merge(usrStat)
                        db.session.commit()

                    usrRoom.gatchas = usrRoom.gatchas + vote.bet * result # gatchas - 1x bet 
                    if usrRoom.gatchas < 0:
                        usrRoom.accepted = False #desuscribirlo
                        temp =  UserStats.query.filter(UserStats.uuid == usrRoom.uuid).first()
                        temp.total_games = temp.total_games + 1
                        db.session.merge(temp)
                        db.session.commit()
                        deadPlayers += 1

                    db.session.merge(usrRoom)
                    db.session.commit()
            #se calcularon los gactchas de cada jugador de esta ronda
            room.maxPlayers = room.maxPlayers - deadPlayers # se resta los jugadores muertos
            room.last_result = rng

            if room.rounds == room.curr_round: #se llego al ultimo round
                usrRooms = UserRooms.query.filter(UserRooms.roomName == roomName, UserRooms.accepted ==True).all()
                for usr in usrRooms:
                    usrStat = UserStats.query.filter(UserStats.uuid == usr.uuid).first()
                    usrStat.total_games = usrStat.total_games + 1 # INC total games
                    usrStat.vtry_pts = usrStat.vtry_pts + usr.gatchas # INC victory points
                    usrStat.won_games = usrStat.won_games + 1 # INC victory points
                    if usrStat.maxGatcha < usr.gatchas:
                        usrStat.maxGatcha = usr.gatchas #INC MAX GATCHA
                    db.session.merge(usrStat)
                    db.session.commit()
            
                #sumar victory points = cantidad gatchas y total games, max gatcha
                
                
                room.voting = False #cerrar votaciones
                
            else:
                room.curr_round = room.curr_round + 1 #aumentar current round por 1
                
            db.session.merge(room)
            db.session.commit()

        return jsonify({"msg":"Voted successfully", 'status': True}), 200 #SUCCESS
    
    return jsonify({"msg":"Already voted", 'status': False}), 409 #Already voted


@app.route('/delFriend', methods=['DEL'])
def delFriend():


    return jsonify({})



if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000,debug=True)
