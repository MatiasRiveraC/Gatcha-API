from logging import FATAL
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import psycopg2
import threading
import random

if __name__ == "__main__":
    from models import *
    conn = psycopg2.connect(database="postgres", user="postgres", host="localhost", port="5432",password="password")
    conn.autocommit = True
    
    
    #create()


app = Flask(__name__)
app.secret_key = "donRecabarren"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:password@localhost:5432/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_size': 10, 'max_overflow': 30} # cambiar o testear
app.config["SQLALCHEMY_POOL_RECYCLE"] = 5


db = SQLAlchemy(app)
db.app = app
migrate = Migrate(app, db)

    

'''  
@app.teardown_appcontext
def shutdown_session(exception=None):
    print("@app.teardown_appcontext: shotdown_session()")
    db.session.remove()
'''
#https://reqbin.com/


@app.route('/test', methods=['GET'])
def test():
    cur = conn.cursor()
    cur.execute("SELECT * FROM USERS")
    #cur.close()
    cur.close()

    return jsonify({'status': True}), 200 #OK

@app.route('/login', methods=['POST'])
def login():
    try:
        name = request.json['Username']
        pswd = request.json['Password']
        fb_token = request.json['fb_token']
    except:
        return jsonify({'status': False, 'token': '', 'user_id':''}), 400 #BAD REQUEST null values or werent passed

    print(f"FB_TOKEN: {fb_token}")
    if not name or not pswd or not fb_token:
        return jsonify({'status': False, 'token': '', 'user_id':''}), 400 #BAD REQUEST null values or werent passed

    cur = conn.cursor()
    cur.execute(f"SELECT uuid, token, password_hash FROM USERS WHERE username = '{name}';")
    usr = cur.fetchone()
    try:
        uuid, token, password_hash = usr[0], usr[1], usr[2]
    except:
        return jsonify({'status': False, 'token': '', 'user_id':''}), 404 #USER DOESNT EXIST or BAD PASSWORD
    #print(usr, verify_password(pswd, password_hash))
    if not usr or not verify_password(pswd, password_hash):
        cur.close()
        return jsonify({'status': False, 'token': '', 'user_id':''}), 404 #USER DOESNT EXIST or BAD PASSWORD
    else:
        uuid, token = usr[0], usr[1]
        cur.execute(f"UPDATE USERS SET fb_token = '{fb_token}' WHERE uuid = '{uuid}'")
        cur.close()
        return jsonify({'status': True, 'token': token, 'user_id': uuid}), 200 #OK


@app.route('/signup', methods=['POST'])
def signup():
    try:
        name = request.json['Username']
        pswd = request.json['Password']
    except:
        return jsonify({'status': False}), 400 #BAD REQUEST null values or werent passed

    if not name or not pswd:
        return jsonify({'status': False}), 400 #BAD REQUEST empty parameters

    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE username = '{name}';")
    found_user = cur.fetchone()
    if found_user:
        cur.close()
        return jsonify({'status': False}), 409 # Duplicate exists
    else:
        usr = Users(name)
        usr.hash_password(pswd)
        pswd_hash = usr.password_hash
        token = usr.token
        usrStats = UserStats(usr.uuid)
        uuid = usr.uuid
        SQLTotal = ""
        SQLTotal += f"INSERT INTO USERS(username, password_hash, token, fb_token, uuid) VALUES('{name}','{pswd_hash}', '{token}', NULL, '{uuid}');"
        SQLTotal += f"INSERT INTO USERSTATS(uuid, vtry_pts, total_games, won_games, bet_wins, total_frnds, maxgatcha, createdate) VALUES('{uuid}', 0,0,0,0,0,0, '{usrStats.createdate}');"
        cur.execute(SQLTotal)
        cur.close()
        return jsonify({'status': True}) ,201 # User created
    


@app.route('/addFriend', methods=['POST'])
def addFriend():
    try:
        friend_id = request.json['friend_id']
    except:
        return jsonify({'status': False, 'msg': 'No ID received', 'fb_token':''}), 400 #BAD REQUEST null values or werent passed
    print(friend_id)
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    print(f"UUID - {user_uuid}")
    ## END REYCLE TOKEN CALL 
    cur.execute(f"SELECT username FROM USERS WHERE uuid = '{friend_id}';")
    friend = cur.fetchone()
    if not friend:
        return jsonify({"status":False, "msg":"Friend doesn't exist", 'fb_token':''}), 404

    cur.execute(f"SELECT id FROM FRIENDS WHERE _id_friend1 = '{user_uuid}' AND _id_friend2 = '{friend_id}'")
    friendQ1 = cur.fetchone()
    cur.execute(f"SELECT id FROM FRIENDS WHERE _id_friend1 = '{friend_id}' AND _id_friend2 = '{user_uuid}'")
    friendQ2 = cur.fetchone()
    
    if not friendQ1 and not friendQ2:
        cur.execute(f"INSERT INTO FRIENDS(_id_friend1, _id_friend2, accepted) VALUES ('{user_uuid}','{friend_id}', NULL);") 
        cur.execute(f"SELECT fb_token FROM USERS WHERE uuid = '{friend_id}'")
        fb_token = cur.fetchone()[0]
        cur.close()
        return jsonify({'status': True, 'msg':'Success', 'fb_token':fb_token}), 200 #OK
    else:
        cur.close()
        return jsonify({'status': False , 'msg': 'Already added', 'fb_token':''}) , 409 # Duplicate



@app.route('/getRequests', methods=['GET'])
def getRequests():
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    print(f"UUID - {user_uuid}")
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT _id_friend1, _id_friend2 FROM FRIENDS WHERE _id_friend2 = '{user_uuid}' AND accepted IS NULL;")
    friends = cur.fetchall()
    print(friends)
    requests = []
    for friend in friends:
        _id_friend1, _id_friend2 = friend
        if _id_friend2 == user_uuid:
            friend_id = _id_friend1
            cur.execute(f"SELECT username FROM USERS WHERE uuid = '{friend_id}';")
            usr = cur.fetchone()[0]
            requests.append({"friend_id":friend_id, "Username":usr})
    cur.close()
    return jsonify({"friends":requests}), 200 #OK


@app.route('/friendResponse', methods=['POST'])
def friendResponse():

    try:
        friend_id = request.json['friend_id']
        response = request.json['response'] #Boolean
    except:
        return jsonify({'status': False, "msg": "Bad parameters"}), 400 #BAD REQUEST null values or werent passed

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT id FROM FRIENDS WHERE _id_friend1 = '{friend_id}' AND _id_friend2 = '{user_uuid}'")
    friendId = cur.fetchone()[0]
    if not friendId:
        return jsonify({"status":False, "msg":"Request is not valid anymore"}), 400 

    if response:
        SQLTotal = ""
        SQLTotal += f"UPDATE FRIENDS set accepted = TRUE WHERE id = {friendId};"
        SQLTotal += f"UPDATE USERSTATS set total_frnds = total_frnds + 1  WHERE uuid = '{user_uuid}';"
        SQLTotal += f"UPDATE USERSTATS set total_frnds = total_frnds + 1 WHERE uuid = '{friend_id}';"
        cur.execute(SQLTotal)
    else:
        cur.execute(f"UPDATE FRIENDS set accepted = FALSE WHERE id = {friendId};")
    cur.close()
    return jsonify({"status":True, "msg":"Success"}), 200  #OK


    
@app.route('/friendList', methods=['GET'])
def friendList():
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL
    cur.execute(f"SELECT _id_friend1, _id_friend2 FROM FRIENDS WHERE (_id_friend1 = '{user_uuid}' OR _id_friend2 = '{user_uuid}') AND (accepted = TRUE);")
    friends = cur.fetchall()
    print(f"UUID -  {user_uuid}")
    print(friends)
    
    friendList = []
    for friend in friends:
        _id_friend1, _id_friend2 = friend
        if _id_friend1 != user_uuid:
            friend_id = _id_friend1
        else:
            friend_id = _id_friend2
        cur.execute(f"SELECT username FROM USERS WHERE uuid = '{friend_id}';")
        usr = cur.fetchone()[0]
        friendList.append({"friend_id":friend_id, "Username":usr})
    cur.close()

    return jsonify({"friends":friendList, "msg":"Success"}), 200 #OK


@app.route('/getRooms', methods=['GET'])
def getRooms():
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL
    cur.execute(f"SELECT roomname FROM USERROOMS WHERE uuid = '{user_uuid}' AND accepted = TRUE AND deleted = FALSE;")
    rooms = cur.fetchall()
    rooms = [x[0] for x in rooms]
    print(f"UUID -  {user_uuid} ROOMS - {rooms}")
    roomList = []
    for room in rooms:
        cur.execute(f"SELECT COUNT(*) FROM USERROOMS WHERE roomname = '{room}' AND accepted = TRUE;")
        amountPlayers = cur.fetchone()[0]
        cur.execute(f"SELECT maxplayers, voting FROM ROOMS WHERE roomname = '{room}';")
        maxSize, voting = cur.fetchone()
        #print(room, amountPlayers, maxSize, voting)
        roomList.append({"roomName":room, "currSize":amountPlayers, "maxPlayers":maxSize, "voting": voting})
    cur.close()
    print(f"ROOMS: {roomList}")
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

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL


    mems = []
    cur.execute(f"SELECT uuid, gatchas FROM USERROOMS WHERE roomname = '{roomName}' AND accepted = TRUE;")
    members = cur.fetchall()
    for member in members:
        uuid, gatchas = member
        cur.execute(f"SELECT username FROM USERS WHERE uuid = '{uuid}';")
        usrName = cur.fetchone()[0]

        mems.append({"Username": usrName, "user_id": uuid, "gatchas": gatchas})


    cur.execute(f"SELECT lastresult, curr_round, voting, minBet FROM ROOMS WHERE roomname = '{roomName}';")
    query = cur.fetchone()
    lastresult, curr_round, voting, minbet = query[0],query[1],query[2], query[3]

    print({"room":mems, "msg":"Success", "lastResult": lastresult, "curr_round": curr_round, "voting":voting})
    cur.close()
    return jsonify({"room":mems, "msg":"Success", "lastResult": lastresult, "curr_round": curr_round, "voting":voting, "minBet": minbet}), 200 #OK

##                                              CHANGE FUNCTIONS BELOW

@app.route('/delRoom', methods=['POST'])
def delRoom():
    try:
        print(f"ROOMNAME DELETE: {request.json['roomName']}")
        roomName = request.json['roomName']
        
    except:
        return jsonify({'room': [], "msg":"Bad parameters"}), 400 #BAD REQUEST null values or werent passed

    if roomName == "" or roomName == None:
        return jsonify({'room':[], "msg":"Empty parameters"}), 402

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    sql = f"UPDATE USERROOMS set deleted = TRUE WHERE uuid = '{user_uuid}' and roomname = '{roomName}';"
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()
    return jsonify({'status': True, "msg":"SUCCESS"}) , 200 # OK


@app.route('/roomInvite', methods=['POST'])
def roomInvite():
    try:
        friend_id = request.json['friend_id']
        roomName = request.json['roomName']
    except:
        return jsonify({'status': False, "msg":"Bad parameters", 'fb_token':''}), 400 #BAD REQUEST null values or werent passed

    if friend_id == "" or friend_id == None or roomName == "" or roomName == "None":
        return jsonify({"status":False, "msg":"Empty parameters", 'fb_token':''}), 400

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT id FROM USERROOMS WHERE roomname = '{roomName}' AND uuid = '{user_uuid}';")  #if inviter is in room
    usrRoomQuery = cur.fetchone()
    cur.execute(f"SELECT id FROM USERROOMS WHERE roomname = '{roomName}' AND uuid = '{friend_id}' AND accepted IS NULL;") # if friend is in room
    usrRoomQuery2 = cur.fetchone()


    if not usrRoomQuery: #User inviter isnt in this room
        cur.close()
        print("USER IS NOT IN ROOM")
        return jsonify({'status': False, "msg": "User is not in room", 'fb_token':''}), 400 # BAD REQUEST
    elif usrRoomQuery2:
        cur.close()
        print("FRIEND IS ALREADY INVITED")
        return jsonify({'status': False, "msg": "Friend is already invited", 'fb_token':''}), 409 # BAD REQUEST, may trigger if already invited or is in room,check later
    else:
        #CHECK SIZE OF PLAYERS IN ROOM FIRST
        cur.execute(f"SELECT maxplayers FROM ROOMS WHERE roomname = '{roomName}';")
        maxplayers = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM USERROOMS WHERE roomname = '{roomName}' AND accepted = TRUE;")
        roomQuery = cur.fetchone()[0]
        if maxplayers < roomQuery:
            cur.close()
            print("ROOM FULL")
            return jsonify({'status': False, "msg": "Room full", 'fb_token':''}), 409 # ROOM FULL

        cur.execute(f"INSERT INTO USERROOMS(roomname, uuid, accepted, gatchas, deleted) VALUES('{roomName}', '{friend_id}', NULL, 2000, FALSE);")

        cur.execute(f"SELECT fb_token FROM USERS WHERE uuid = '{friend_id}';")
        fb_token = cur.fetchone()[0]
        print(f"fb_token: {fb_token}")
        cur.close()
        return jsonify({'status': True, "msg":"Invite successful", 'fb_token': fb_token}) , 200 # OK

@app.route('/roomResponse', methods=['POST'])
def roomResponse():
    try:
        roomName = request.json["roomName"]
        response = request.json['response'] #Boolean
    except:
        return jsonify({'status': False, "msg":"Bad parameters"}), 200 #BAD REQUEST null values or werent passed

    if roomName == "" or roomName == None or response == "" or response == None:
        return jsonify({'status':False,"msg":"Empty parameters"}), 200

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL


   
    if response: #Join
        cur.execute(f"SELECT COUNT(*) FROM USERROOMS WHERE roomname = '{roomName}' AND accepted = TRUE;")
        count = cur.fetchone()[0]
        cur.execute(f"SELECT maxplayers FROM ROOMS WHERE roomname = '{roomName}';")
        maxSize = cur.fetchone()[0]
        if maxSize <= count:
            print(maxSize, count, "FULL")
            cur.close()
            return jsonify({'status': False, "msg":"Room full"}), 200 #ROOM FULL
        else:
            print("ACCEPT")
            cur.execute(f"UPDATE USERROOMS SET accepted = TRUE WHERE roomname = '{roomName}';")
            cur.close()

            return jsonify({'status':True, 'msg':"Joined room"}), 200 #OK
    else: #DENY
        print("DENY")
        cur.execute(f"UPDATE ROOMS SET accepted = FALSE WHERE roomname = '{roomName}';")
        cur.close()

        return jsonify({'status':True, 'msg':"Denied room"}), 200 #OK


@app.route('/roomRequests', methods=['GET'])
def roomInvs():

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT roomname FROM USERROOMS WHERE uuid = '{user_uuid}' AND accepted IS NULL;")
    rooms = cur.fetchall()


    requests = []

    for room in rooms:
        roomname = room[0]
        requests.append({"roomName":roomname})

    cur.close()
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
        return jsonify({'status': False, "msg":"Bad parameters"}), 400 #BAD REQUEST null values or werent passed

    if not roomName or not pswd or not maxPlayers or not minBet or not rounds:
        return jsonify({'status': False, "msg":"Empty parameters"}), 400 #BAD REQUEST empty parameters

    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT roomname FROM ROOMS WHERE roomname = '{roomName}';")
    query = cur.fetchone()
    if query:
        return jsonify({"status":False, "msg":"Room already exists"}), 409 #ROOM ALREADY EXISTS

    room = Rooms(roomName, maxPlayers, minBet, rounds)
    room.hash_password(pswd)
    cur.execute(f"INSERT INTO ROOMS(roomname, password_hash, maxplayers, minbet, rounds, curr_round, lastresult, voting) VALUES('{roomName}', '{room.password_hash}', {maxPlayers}, {minBet}, {rounds}, 1, NULL, TRUE);")
    cur.execute(f"INSERT INTO USERROOMS(roomname, uuid, accepted, gatchas, deleted) VALUES('{roomName}', '{user_uuid}', TRUE, 2000, FALSE);")
    cur.close()

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

    valid = [0,1,2,3,4,5,6,7,8,9,10,11,12]
    if not roomName or vote not in valid or not bet or not round:
        return jsonify({'status': False, "msg":"Empty parameters"}), 400 #BAD REQUEST empty parameters
    
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL
    cur.execute(f"SELECT id FROM USERVOTE WHERE uuid = '{user_uuid}' AND round = {round} AND roomname = '{roomName}';")
    voteCheck = cur.fetchone()
    if not voteCheck:
        cur.execute(f"SELECT maxplayers, rounds, curr_round, voting, minbet FROM ROOMS WHERE roomname = '{roomName}';")
        roomquery = cur.fetchone()
        maxplayers, rounds, curr_round, voting, minbet = roomquery[0],roomquery[1],roomquery[2],roomquery[3],roomquery[4] #puedo conseguir, maxPlayers, rounds, curr round, voting y lastResult
        if not voting: # no se puede votar mas
            cur.close()
            return jsonify({"status":False, "msg":"Room's closed!"}), 400 #Room's closed!

        cur.execute(f"INSERT INTO USERVOTE(roomname, uuid, vote, bet, round) VALUES('{roomName}', '{user_uuid}', {vote}, {bet}, {round});")

        cur.execute(f"SELECT vote, bet, uuid FROM USERVOTE WHERE roomname = '{roomName}' AND round = {curr_round};")
        votes = cur.fetchall() #obtener todos los votos de la ronda actual
        cur.execute(f"SELECT COUNT(*) FROM USERVOTE WHERE roomname = '{roomName}' AND round = {curr_round};")
        count = cur.fetchone()[0] #cantidad de votos en ronda actual


        if maxplayers == count: #cantidad votos = cantidad de jugadores
            rng = random.randint(0,9)
            deadPlayers = 0
            totalSQL = ""
            gatchasDic = {}
            for vote in votes:
                user_vote, user_bet, uuid = vote[0],vote[1],vote[2]

                cur.execute(f"SELECT gatchas FROM USERROOMS WHERE roomname = '{roomName}' AND uuid = '{uuid}' AND accepted = TRUE;")
                user_gatchas = cur.fetchone()[0] #conseguir gatchas

                if user_gatchas:
                    cur.execute(f"SELECT bet_wins, total_games FROM USERSTATS WHERE uuid = '{uuid}';")
                    query = cur.fetchone()
                    user_bet_wins, user_total_games = query[0],query[1]
                    result = voteResult(rng, user_vote)
                    if result > 0:
                        user_bet_wins += 1 # add bet wins
                    bet_wins  = user_bet_wins
                    accepted = "TRUE"
                    gatchas = user_gatchas + user_bet * result # gatchas - 1x bet
                    print(f"Current gatchas - {gatchas}")
                    if gatchas < minbet:
                        accepted = "FALSE" #desuscribirlo
                        user_total_games += 1
                        deadPlayers += 1
                    total_games = user_total_games

                    usrRoomSQL = f"UPDATE UserRooms SET accepted = {accepted}, gatchas = {gatchas} WHERE (uuid = '{uuid}' AND roomname = '{roomName}');"
                    usrStatsSQL = f"UPDATE UserStats SET bet_wins = {bet_wins}, total_games = {total_games} WHERE uuid = '{uuid}';"
                    gatchasDic[uuid] = {'gatchas':gatchas}
                    totalSQL += usrRoomSQL + usrStatsSQL
            print(totalSQL)
            cur.execute(totalSQL)

            roomSQL = f"UPDATE ROOMS SET maxPlayers = {maxplayers - deadPlayers}, lastResult = {rng}, "
            usrStatsSQLs = ""
            if rounds == curr_round: #se llego al ultimo round
                cur.execute(f"SELECT uuid, gatchas FROM USERROOMS WHERE roomname = '{roomName}' AND accepted = TRUE;")
                usrRooms = cur.fetchall()
                for usr in usrRooms:
                    uuid, user_gatchas = usr[0],usr[1]
                    gatchas = gatchasDic[uuid]['gatchas']
                    print(f"UUID: {uuid} roomname: {roomName} gatchas: {user_gatchas}")
                    cur.execute(f"SELECT maxgatcha FROM USERSTATS WHERE uuid = '{uuid}';")
                    maxGatcha = cur.fetchone()[0]
                    
                    if maxGatcha < gatchas:
                        maxGatcha = gatchas #INC MAX GATCHA

                    StatsSQL = f"UPDATE UserStats SET total_games = total_games + 1, vtry_pts = vtry_pts + {gatchas }, won_games = won_games + 1, maxGatcha = {maxGatcha} WHERE uuid = '{uuid}';"
                    usrStatsSQLs += StatsSQL
                
                #sumar victory points = cantidad gatchas y total games, max gatcha
                
                roomSQL += f"voting = FALSE WHERE roomName = '{roomName}';"
            else:
                roomSQL += f"curr_round = {curr_round + 1} WHERE roomName = '{roomName}';"
            usrStatsSQLs += roomSQL
            print(usrStatsSQLs)
            cur.execute(usrStatsSQLs)
            cur.close()



            return jsonify({"msg":"Voted successfully", 'status': True}), 200 #SUCCESS

        return jsonify({"msg":"Voted successfully", 'status': True}), 200 #SUCCESS
    cur.close()
    return jsonify({"msg":"Already voted", 'status': False}), 409 #Already voted


@app.route('/getStats', methods=['GET'])
def getStats():
    ##REYCLE TOKEN CALL
    token = request.headers.get('token')
    print(f"TOKEN: {token}")
    cur = conn.cursor()
    cur.execute(f"SELECT uuid FROM USERS WHERE token = '{token}'")
    user = cur.fetchone()
    if not user[0]:
        print("User not found")
        return jsonify({'status': False, "msg":"Token isn't valid"}), 404 #BAD REQUEST null values or werent passed
    user_uuid = user[0]
    ## END REYCLE TOKEN CALL

    cur.execute(f"SELECT vtry_pts, total_games, won_games, bet_wins, total_frnds, maxgatcha, createdate FROM USERSTATS WHERE uuid = '{user_uuid}';")
    query = cur.fetchone()


    vtry_pts, total_games, won_games, bet_wins, total_frnds, maxgatcha, createdate = query[0],query[1],query[2],query[3],query[4],query[5],query[6],
    cur.close()

    return jsonify({"status":True,"msg":"sucess", "vtry_pts": vtry_pts, "total_games":total_games, "won_games":won_games,
    "bet_wins":bet_wins, "total_frnds": total_frnds, "maxGatcha": maxgatcha, "createDate": createdate})



if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000,debug=True)
    except:
        conn.close()