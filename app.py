from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

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
    except:
        return jsonify({'status': False, 'token': '', 'uuid':''}), 400 #BAD REQUEST null values or werent passed

    if not name or not pswd:
        return jsonify({'status': False, 'token': '', 'uuid':''}), 400 #BAD REQUEST empty parameters

    usr = User.query.filter_by(username = name).first()
    if not usr or not usr.verify_password(pswd):
        return jsonify({'status': False, 'token': '', 'uid':''}), 404 #USER DOESNT EXIST or BAD PASSWORD
    else:
        return jsonify({'status': True, 'token': usr.token, 'uuid': usr.uuid}), 200 #OK


@app.route('/signup', methods=['POST'])
def setSignUp():

    try:
        name = request.json['Username']
        pswd = request.json['Password']
    except:
        return jsonify({'userCreated': False}), 400 #BAD REQUEST null values or werent passed

    if not name or not pswd:
        return jsonify({'userCreated': False}), 400 #BAD REQUEST empty parameters

    found_user = User.query.filter_by(username = name).first()
    if found_user:
        return jsonify({'userCreated': False}), 409 # Duplicate exists
    else:
        usr = User(name)
        usr.hash_password(pswd)
        db.session.add(usr)
        db.session.commit()
        return jsonify({'userCreated': True}) ,201 # User created

@app.route('/addFriend', methods=['POST'])
def addFriend():
    try:
        user_id = request.json['user_id']
        friend_id = request.json['friend_id']
    except:
        return jsonify({'friendAdded': False}), 400 #BAD REQUEST null values or werent passed

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token, uuid = user_id).first()
    if not found_user:
        return jsonify({'friendAdded': False}), 400 #BAD REQUEST null values or werent passed
    
    friendQuery = Friends.query.filter(((Friends._id_friend1 == user_id )|(Friends._id_friend2 == friend_id)) | ((Friends._id_friend1 == friend_id )|(Friends._id_friend2 == user_id)) ).first()
    if not friendQuery:
        friend = Friends(user_id, friend_id)
        db.session.add(friend)
        db.session.commit()
        return jsonify({'friendAdded': True}), 200 #OK

    return jsonify({'friendAdded': False}) , 409 # Duplicate

@app.route('/getRequests/<user_id>', methods=['GET'])
def getRequests(user_id):
    try:
        user_id = request.view_args['user_id']
    except:
        return jsonify({'Requests': {}}), 400 #BAD REQUEST null values or werent passed

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token, uuid = user_id).first()
    if not found_user:
        return jsonify({'Requests': {}}), 400 #BAD REQUEST null values or werent passed
    


    friends = Friends.query.filter(((Friends._id_friend1 == user_id )|(Friends._id_friend2 == user_id)) & (Friends.accepted == False)).all()
    requests = []
    for friend in friends:
        if friend._id_friend2 == user_id:
            print(friend.accepted)
            friend_id = friend._id_friend1
            usr = User.query.filter_by(uuid = friend_id).first()
            requests.append({"user_id":friend_id, "Username":usr.username})


    return jsonify({"Requests":requests}), 200 #OK

@app.route('/acceptFriend', methods=['POST'])
def acceptFriend():
    try:
        user_id = request.json['user_id']
        friend_id = request.json['friend_id']
    except:
        return jsonify({'status': False}), 400 #BAD REQUEST null values or werent passed

    token = request.headers.get('token')
    found_user = User.query.filter_by(token = token, uuid = user_id).first()
    if not found_user:
        return jsonify({'status': False}), 400 #BAD REQUEST null values or werent passed

    friend = Friends.query.filter_by(_id_friend1 = friend_id, _id_friend2 = user_id).first()
    friend.accepted = True
    db.session.commit()
    print(friend.accepted)
    return jsonify({"status":friend.accepted})

@app.route('/friendList', methods=['GET'])
def friendList():


    return jsonify({})

@app.route('/roomList', methods=['GET'])
def roomList():


    return jsonify({})

@app.route('/roomInvs', methods=['GET'])
def roomInvs():


    return jsonify({})

@app.route('/createRoom', methods=['POST'])
def createRoom():


    return jsonify({})

@app.route('/delFriend', methods=['DEL'])
def delFriend():


    return jsonify({})



if __name__ == '__main__':

    app.run(host='localhost', port=5000,debug=True)
