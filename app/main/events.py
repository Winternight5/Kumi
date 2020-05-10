import os, datetime
from flask import current_app as app
from flask import session, json, request, jsonify, redirect, url_for
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, login_required
from .. import socketio, db
from . import main, routes
from .models import User, Post, Friend, Channel
	
clients = []
datas = {}
rooms = {}
	
def getKeys(dict): 
    return list(dict.keys())
	
def getValues(dict): 
    return list(dict.values())
	
def checkDatas():
    currentRoom = session.get('room')
    if not currentRoom in datas.keys(): 
        datas[currentRoom] = {}
        datas[currentRoom]['d'] = []
		
    if not datas[currentRoom]['d'] is None:
        if len(datas[currentRoom]['d']) > 3000:
            del datas[currentRoom]['d'][0:500]
            
def clearDatas(currentRoom):
    datas[currentRoom] = {}
    datas[currentRoom]['d'] = []
    
@socketio.on('joined', namespace='/')
def joined():
    '''
    New User Joined
    ---------------

    Add user to the room array.
    '''
    global rooms
    members = []
    currentRoom = session.get('room')
    clients.append(str(current_user.id))
    
    join_room(currentRoom)
    rooms[currentRoom] = str(sum(1 for i in clients if i == currentRoom))

    channel_id = Channel.query.filter_by(b64name=currentRoom).first()
    session['channel_id'] = channel_id

    for member in User.query.filter(User.id.in_(clients)).all():
        temp = {}
        temp['id'] = member.id
        temp['status'] = member.status
        temp['online_status'] = routes.online_status(member.status)
        members.append(temp)

    emit('status', {
        'users': members,
        'count': len(clients),
        'clients': [int(i) for i in clients]
    }, broadcast=True)
    print('Rooms: '+str(rooms))
    print('clients list: '+str(clients))
    print('--------------------------------------------------------------------------')

@socketio.on('update_stats', namespace='/')
def update_stats():
    '''
    Update User Stats
    '''
    currentRoom = session.get('room')

    data = {}
    data['id'] = current_user.id
    data['status'] = current_user.status
    data['online_status'] = routes.online_status(current_user.status)

    emit('status', {
        'users': [data],
        'count': len(clients),
        'clients': [int(i) for i in clients]
    }, broadcast=True)

@socketio.on('disconnect', namespace='/')
def disconnect():
    '''
    User Disconnected
    ---------------

    Remove the user from the room array.
    '''
    global rooms
    currentRoom = session.get('room')
    
    clients.remove(str(current_user.id))
    rooms[currentRoom] = str(sum(1 for i in clients if i == currentRoom))

    users = {
            'id':current_user.id,
            'status': 3,
            'online_status': 'off',
        }

    leave_room(currentRoom)
    #updateRooms()
    emit('status', {
        'users': [users],
        'count': len(clients),
        'clients': [int(i) for i in clients]
    }, broadcast=True)
    print('Rooms: '+str(rooms))
    print('clients list: '+str(clients))
    print('--------------------------------------------------------------------------')

@main.route('/ch/<int:id>/<string:b64>')
@login_required
def changeChannel(id, b64):
    '''
    User Change Channel
    ---------------

    Remove the user from the room
    And join a new room.
    '''
    oldRoom = session.get('room')
    leave_room(oldRoom)
    
    currentRoom = session['room'] = b64

    channelCheck = Channel.query.filter_by(b64name=currentRoom).first()
    print(channelCheck)
    if (channelCheck is None):
        newChannel = Channel(b64name=currentRoom,
                       owner_id=current_user.id,
                       access_type=id)
        db.session.add(newChannel)
        db.session.commit()
    
    channel_id = Channel.query.filter_by(b64name=currentRoom).first()
    session['channel_id'] = channel_id

    join_room(currentRoom)
    return '1'

@socketio.on('channel', namespace='/')
def changeChannel(data):
    '''
    User Change Channel
    ---------------

    Remove the user from the room
    And join a new room.
    '''
    oldRoom = session.get('room')
    leave_room(oldRoom)
    
    currentRoom = session['room'] = data['b64']

    channelCheck = Channel.query.filter_by(b64name=currentRoom).first()
    print(channelCheck)
    if (channelCheck is None):
        newChannel = Channel(b64name=currentRoom,
                       owner_id=current_user.id,
                       access_type=data['id'])
        db.session.add(newChannel)
        db.session.commit()
    
    channel_id = Channel.query.filter_by(b64name=currentRoom).first()
    session['channel_id'] = channel_id

    join_room(currentRoom)

@socketio.on('text', namespace='/')
def text(data):
    '''
    Text Messaging Feature
    ---------------

    Save current user text data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')
    currentChannel = session.get('channel_id')

    msg = {
        'type': data['type'],
        'msg': data['msg']
        }

    type = 1 if data['type'] == 'file' else 0

    newPost = Post(b64name=currentRoom, 
                   body=json.dumps(msg), 
                   user_id=current_user.id,
                   channel_id=currentChannel.id)
    db.session.add(newPost)
    db.session.flush()
    db.session.commit()
    db.session.refresh(newPost)

    emit('message', {
        'body': msg,
        'id': newPost.id,
        'user_id': current_user.id,
        'imgUrl': current_user.imgUrl,
        'timestamp': str(newPost.timestamp),
        'visible': 1,
        'track': type
    }, room=currentRoom)

@socketio.on('update_text', namespace='/')
def update_text(data):
    '''
    Update Text Messaging Feature
    ---------------

    Save current user text data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')

    msg = {
        'type': 'file',
        'msg': data['msg']
        }

    current_post = Post.query.filter_by(id=data['id']).first()
    current_post.body = json.dumps(msg)
    db.session.commit()

    emit('updated_text', {
        'msg': data['msg'],
        'id_name': data['id_name']
    }, room=currentRoom)

@socketio.on('disable_text', namespace='/')
def text(data):
    '''
    Text Messaging Feature
    ---------------

    Save current user text data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')
    
    current_post = Post.query.filter_by(id=data['id']).first()
    current_post.visible = None
    db.session.commit()

    emit('hide_message', {
        'id': data['id']
    }, room=currentRoom)

@socketio.on('friend', namespace='/')
def friend_request(data):
    '''
    Add Friend Feature
    ---------------

    Emit friend request.
    '''
    currentRoom = session.get('room')

    emit('friend_request', data, broadcast=True)


@socketio.on('friend_accept', namespace='/')
def friend_accept(data):
    '''
    Add Friend Feature
    ---------------

    Emit friend handshake completed.
    '''
    data['confirmed'] = 0

    f1, f2 = handshake = [
        Friend(user_id=data['id'], friend_id=data['friend']),
        Friend(user_id=data['friend'], friend_id=data['id'])
        ]

    try:
        db.session.add_all(handshake)
        db.session.commit()
        data['confirmed'] = 1
    except Exception as e:
        return "FAILED entry: "+str(e)

    update_stats()
    emit('friend_completed', data, broadcast=True)

@socketio.on('drawing', namespace='/')
def drawing(data):
    '''
    Drawing Feature
    ---------------

    Save current user drawing data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')
    checkDatas()
    datas[currentRoom]['d'].append(data)
    emit('drawing', data, room=currentRoom)
	
@socketio.on('fill', namespace='/')
def fill(data):
    '''
    Fill Feature
    ---------------

    Save current user fill data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')
    checkDatas()
    datas[currentRoom]['d'].append(data['color'])
    emit('fill', {
        'color': data['color']
    }, room=currentRoom)	
    
@socketio.on('img', namespace='/')
def loadImg(data):
    '''
    Image Feature
    ---------------

    Save current user image data into memory and emit data to all users in the room.
    '''
    currentRoom = session.get('room')
    clearDatas(currentRoom)
    datas[currentRoom]['i'] = data
    print(data)
    emit('img', data, room=currentRoom)

@socketio.on('new', namespace='/')
def new(data):
    '''
    New Canvas
    ---------------

    Clear memory and emit to all users.
    '''
    currentRoom = session.get('room')
    clearDatas(currentRoom)
    emit('new', {}, room=currentRoom)	
    
@socketio.on('save', namespace='/')
def save(newdata):
    '''
    Save Feature
    ---------------

    Save current user canvas data into database.
    '''
    currentRoom = session.get('room')
    
    id = newdata['id'] if newdata['id'] is not None else ''
    title = newdata['title'] if newdata['title'] is not None else ''
    tags = newdata['tags'] if newdata['tags'] is not None else ''
    thumbnail = newdata['DataURL'] if newdata['DataURL'] is not None else ''
    data = datas[currentRoom].copy() if datas[currentRoom] is not None else ''
    
    if id is not '':
        saveData = routes.saveCanvasById(id, title, tags, thumbnail, data)
    else:
        saveData = routes.saveCanvas(title, tags, thumbnail, data)
        
    emit('saved', saveData, room=currentRoom)
    print('Canvas Saved')

def revokeAccess():
    '''
    Revoke Access
    ---------------

    Init and emit revoke access to all current active shared users.
    '''
    currentRoom = session.get('room')
    socketio.emit('accessRevoked', {}, room=currentRoom)	
    
@main.route('/img', methods=['GET'])
def img():
    '''
    Get Image
    ---------------

    Get Image data.
    '''
    currentRoom = session.get('room')
    return datas
