import os
from flask import render_template, flash, redirect, url_for, request, jsonify, json, session
from .. import db
from . import main
from .forms import LoginForm, RegistrationForm, ResetForm
from .models import User, Post, Friend, Channel, ChannelRelationship
from flask_login import current_user, login_user, logout_user, login_required, login_manager
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import random, string, html, re, uuid, pybase64
from sqlalchemy.orm import Session
from sqlalchemy import or_

theme = {
    'theme': 'gradient-45deg-indigo-blue', #value if type == '' else '',
    'mode': '',
    'collapse': '',
    'menu': 'sidenav-active-square',
    'chatarea': 'bg-image-shattered',
    }
ALL_CHANNELS = []
ALLOWED_EXTENSIONS = { 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'doc', 'xlsx', 'xls', 'ppt', 'pptx' }
UPLOAD_FOLDER = 'static/files/'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------------------------------------------------------------------------------------------
#----- Demo
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/demo')
def demo():
    '''Demo page
    '''
    return render_template('demo.html')

# -------------------------------------------------------------------------------------------------------------------------
# ----- Landing Page
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/')
def welcome():
    '''Landing Page / login screen
    '''
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    data = [
        'Log In / Out',
        'Team Channel',
        'Messaging in Real Time',
        'Private Messaging',
        'Unsend Message',
        'Emoji Options',
        'Send Files',
        'Interactive Whiteboard',
        'Member\'s Online Status',
        'Friend Request',
        'Theme Customization',
        'Tasks'
        ]

    form=LoginForm()
    #email = "admin@test.com"
    #data['email'] = pybase64.urlsafe_b64encode(email.encode()).decode()

    return render_template('welcome.html', form=form, data=data)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Register Page
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/r/<string:email>')
def register(email):
    '''Registration Page
    '''
    data = {}

    form=LoginForm()
    try:
        data['email'] = pybase64.b64decode(email).decode()
    except Exception as e:
        data['email'] = ''
        print(e)

    return render_template('welcome.html', form=form, data=data)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Index
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/home')
@login_required
def index():
    '''Main home page

    *login required*

    :return: Display all of user's notes
    '''

    if current_user.block_login:
        flash('Your account has been permanently suspended')
        logout_user()
        return redirect(url_for('main.welcome'))

    if current_user.suspend_date is not None and current_user.suspend_date > datetime.utcnow():
        flash('Your account has been temporary suspended until '+str(current_user.suspend_date.strftime('%b %d, %Y at %I:%M %p')))
        logout_user()
        return redirect(url_for('main.welcome'))

    global theme, ALL_CHANNELS
    get_all_channels()
    current_user.fullname = current_user.firstname+' '+current_user.lastname
    current_user.online_status = online_status(current_user.status)
    members = []
    friends = []
    channels = []

    current_channel = Channel.query.filter(Channel.id == 1).first()
    current_channel.active = 'active'
    channels.append(current_channel)

    chats = getMessages(channels[0].b64name)
    room = session['room'] = b64name_channel(channels[0].name)

    channels_query = (Channel.query
        .filter(Channel.users.any(ChannelRelationship.user_id == current_user.id))
        .all())

    for channel in channels_query:
        channels.append(channel)
    print(channels)
    # Query friend database
    # Retrieve all friends of current_user
    friends_query = (User.query
        .filter(User.friendships_of.any(Friend.user_id == current_user.id))
        #.outerjoin(Post, db.and_(
        #        u_alice.ID == Friendship.User_id,
        #        User.ID == Friendship.Friend_id
        #))
        .order_by(User.access_type.asc())
        .all())
    
    for friend in friends_query:
        friend.fullname = friend.firstname+' '+friend.lastname
        # string of online status
        friend.online_status = online_status(friend.status)
        # room name
        friend.b64name = b64name_dm(current_user.email, friend.email)
        #friend.active = 'active' if friend.id is 3 else ''
        friends.append(friend)

    # Query User database
    # Retrieve all active members from last 6 months
    last_6months = datetime.today() - timedelta(days = 180)
    for member in User.query.order_by(User.firstname.asc()).filter(
            User.email != 'admin', 
            User.last_login >= last_6months
        ).all():
        member.fullname = member.firstname+' '+member.lastname
        member.online_status = online_status(member.status)
        member.b64name = b64name_dm(current_user.email, member.email)
        members.append(member)

    settings = json.loads(current_user.settings) if current_user.settings else theme
    #print(settings)
    return render_template('home.html', 
                           title='Home',
                           room=room,
                           current_user=current_user,
                           settings=settings,
                           channels=channels,
                           current_channel=current_channel,
                           all_channels=ALL_CHANNELS,
                           chats=chats,
                           members=members,
                           friends=friends)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Helper functions
# -------------------------------------------------------------------------------------------------------------------------
def getMessages(id, offset = 0):
    chats = []
    q = Post.query.outerjoin(
            User, db.and_(
                Post.user_id == User.id
            )
        ).filter(Post.b64name == id).order_by(Post.id.asc()).offset(offset).limit(30)

    for chat in q:
        temp = {}
        temp['id'] = chat.id
        temp['user_id'] = chat.user.id
        temp['firstname'] = chat.user.firstname
        temp['body'] = json.loads(chat.body)
        temp['imgUrl'] = chat.user.imgUrl
        temp['timestamp'] = chat.timestamp
        temp['visible'] = chat.visible
        chats.append(temp)

    return chats

def online_status(data):
    '''Online Status detail
    Convert int (0) to str (online)

    :return: online status value
    '''
    return {
        0: 'online',
        1: 'busy',
        2: 'away',
        3: 'off'
        }.get(data, 'off')

def b64name_channel(data):
    '''Generate b64name
    if channel, use channel name
    :return: encrypted base64
    '''
    return pybase64.urlsafe_b64encode(data.encode()).decode()

def b64name_dm(user1, user2):
    '''Generate b64name
    If between users, use email + email
    :return: encrypted base64
    '''
    list = [user1, user2]
    list.sort()
    data = ','.join(list)

    return pybase64.urlsafe_b64encode(data.encode()).decode()

def get_all_channels():
    global ALL_CHANNELS
    ALL_CHANNELS = []

    channels = Channel.query.filter(Channel.name != None).order_by(Channel.name.asc()).all()
    ALL_CHANNELS = channels

# -------------------------------------------------------------------------------------------------------------------------
# ----- Get Channel JSON for Channels Manager
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/cm/<string:form_user>')
@login_required
def json_channels(form_user):
    '''Get Channel JSON
    '''
    data = []
    fullname = str(form_user).split(' ')
    user = User.query.filter(User.firstname==fullname[0], User.lastname==fullname[1]).first()

    channels_query = (Channel.query
        .filter(Channel.users.any(ChannelRelationship.user_id == user.id))
        .all())
    if len(channels_query) > 0:
        for channel in channels_query:
            temp = {
                'id': channel.id,
                'name': channel.name
                }
            data.append(temp)

        return json.dumps(data)

    return "0"

# -------------------------------------------------------------------------------------------------------------------------
# ----- Channels Manager - Form Submit
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/cfs', methods=['POST'])
@login_required
def cfs():
    print(request.form)
    if request.method == 'POST' and current_user.admin_level == 0:
        form_user = request.form.get("user")
        fullname = str(form_user).split(' ')
        # check if the post request has user field
        if form_user is not None and form_user != '':
            user = User.query.filter(User.firstname==fullname[0], User.lastname==fullname[1]).first()
            new_channels = request.form.getlist('channels')
            print(user.id)
            if user is None: 
                return "User Not Found"

            channels_query = ChannelRelationship.query.filter(ChannelRelationship.user_id == user.id).all()
            for i in channels_query:
                db.session.delete(i)

            if len(new_channels) > 0:
                for i in new_channels:
                    user.channels.append(ChannelRelationship(users=Channel.query.filter(Channel.id==i).first()))

            try:
                db.session.commit()
            except Exception as e:
                print("FAILED entry: "+str(e));
            
            return {
                'id': user.id,
                'channels': new_channels,
                'msg':"Channel Applied Successfully"
                } 

        return "Error: Failed to Apply Changes"
        
    return "Access Denied"

# -------------------------------------------------------------------------------------------------------------------------
# ----- Get Person JSON
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/p/<int:id>')
@login_required
def json_person(id):
    '''Get Person JSON
    '''
    data = {}
    
    user = User.query.filter(User.id == id).first()
    data['id'] = user.id
    data['fullname'] = user.firstname+' '+user.lastname
    data['online_status'] = online_status(user.status)
    data['status'] = user.status
    data['imgUrl'] = user.imgUrl

    return json.dumps(data)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Get Person JSON
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/getfriends')
@login_required
def json_getFriend():
    '''Get all friends and return JSON
    '''
    data = {}
    
    friends_query = (User.query
        .filter(User.friendships_of.any(Friend.user_id == current_user.id))
        .order_by(User.status.asc())
        .all())

    for user in friends_query:
        data[user.id] = 1

    return json.dumps(data)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Get Channel JSON
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/channel/<string:name>')
@login_required
def json_getChannel(name):
    '''Get all friends and return JSON
    '''
    if not name: return '0'

    data = {}
    
    #query = User.query.filter(User.email == d_name[0]).first() if name[:2] == 'I0' else Channel.query.filter(Channel.b64name == name).first()
    query = Channel.query.filter(Channel.b64name == name).first()
    user_id = query.owner_id if current_user.id == query.access_type else query.access_type
    
    if query.name:
        data['name'] = query.name
        data['title'] = query.title
        data['imgUrl'] = query.imgUrl
        data['type'] = 0
    else:
        user = User.query.filter(User.id == user_id).first()
        data['name'] = user.firstname+" "+user.lastname
        data['title'] = user.title
        data['imgUrl'] = user.imgUrl
        data['type'] = user.id
        #if current_user.friendships is not None:
        #    for temp in current_user.friendships:
        #        print(str(current_user.firstname)+" = "+str(temp.id)+" : "+str(temp.user_id)+" / "+str(temp.friend_id)+" | "+str(query.access_type)+"-"+str(current_user.id))
        #        if temp.friend_id == current_user.id:
        #            data['type'] = temp.id

    return json.dumps(data)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Update Theme
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/update/<string:type>/<string:value>')
@login_required
def updateTheme(type, value):
    '''Update Theme
    '''
    if not type or not value: return '0'

    global theme

    current_theme = json.loads(current_user.settings) if current_user.settings else theme

    if str(type) == 'theme': current_theme['theme'] = value
    if str(type) == 'mode': current_theme['mode'] = value
    if str(type) == 'collapse': current_theme['collapse'] = value
    if str(type) == 'menu': current_theme['menu'] = value
    if str(type) == 'chatarea': current_theme['chatarea'] = value
    #print(current_theme)
    current_user.settings = json.dumps(current_theme)
    db.session.commit()

    return '1'

# -------------------------------------------------------------------------------------------------------------------------
# ----- Update Current User Status
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/cs/<int:type>')
@login_required
def changeStatus(type):
    '''Update User Status
    '''
    current_user.status = type
    db.session.commit()

    return '1'

# -------------------------------------------------------------------------------------------------------------------------
# ----- Get Person JSON
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/gm/<string:id>')
@login_required
def getJSONMessages(id):
    '''Update User Status
    '''
    chats = getMessages(id)

    return json.dumps(chats)

# -------------------------------------------------------------------------------------------------------------------------
# ----- Suspension submit
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/sfs/<string:id>', methods=['POST'])
@login_required
def sfs(id):
    if request.method == 'POST' and current_user.admin_level == 0:
        user = User.query.filter_by(id=id).first()
        suspend_date = request.form.get("user")
        suspend_time = request.form.get("user")
        # check if the post request has date and time filled
        if suspend_date is not None and suspend_date != '' and suspend_time is not None and suspend_time != '':
            timestamp = datetime.fromtimestamp(int(request.form['timestamp']))
            user.suspend_date = timestamp
        else:
            user.suspend_date = None
            
        if 'suspend_perma' in request.form and request.form['suspend_perma'] == 'on':
            user.block_login = 1
        else:
            user.block_login = None

        if request.form['comment'] != '':
            user.comment = str(request.form['comment'])

        try:
            db.session.commit()
        except Exception as e:
            print("FAILED entry: "+str(e));
            
        return "Suspension update applied"
        
    return "Access Denied"
# -------------------------------------------------------------------------------------------------------------------------
# ----- Suspension submit
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/gsd/<string:id>')
@login_required
def gsd(id):
    user = User.query.filter_by(id=id).first()

    data = {
        'permanent': 'checked' if user.block_login else '',
        'timestamp': user.suspend_date,
        'comment': user.comment
        }
        
    return data

# -------------------------------------------------------------------------------------------------------------------------
# ----- File Upload
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file-upload' not in request.files:
            flash('No file part')
            return '0'
        file = request.files['file-upload']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(main.root_path, '../static/files'), exist_ok=True)
            file.save(os.path.join(main.root_path, '../static/files', filename))
        else:
            flash('File not allowed')
            return '0'
    return '1'

# -------------------------------------------------------------------------------------------------------------------------
# ----- User login & Registation / Logout
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    '''Login Function

    :return:Get radio form "login-option" to route functions to Login, Logout or Registration


    sign-in
    +++++++

    :return: Get user's input email and password, then validate and authenticate the user.


    sign-up
    +++++++

    :return: Get user's filled form data, then validate and create a new user.


    reset-login
    +++++++++++

    :return: Get user's input email, then validate the email on file and send a reset password email to the user's email.
    '''
        # if user logged in, go to main home page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # get post data of radio button 'login-option'
    option = request.form.get('login-option')
    form = LoginForm()
    form.login_message = ""

    # if radio is sign-in, autheticate user
    if (option == "sign-in"):
    
        # validate form
        if form.validate_on_submit():
            print('validating')
            # look at first result first()
            user = User.query.filter_by(email=form.email.data.lower()).first()

            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('main.welcome'))
            
            if user.block_login:
                flash('Your account has been permanently suspended')
                return redirect(url_for('main.welcome'))

            if user.suspend_date is not None and user.suspend_date > datetime.utcnow():
                flash('Your account has been temporary suspended until '+str(user.suspend_date.strftime('%b %d, %Y at %I:%M %p'))+' GMT')
                return redirect(url_for('main.welcome'))

            user.last_login = datetime.utcnow()
            db.session.commit()
            #login_user(user, remember=form.remember_me.data)
            login_user(user)

            # return to page before user got asked to login
            next_page = request.args.get('next')

            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.welcome')

            return redirect(next_page)

        print('unable to login')
        return render_template('welcome.html', form=form)

    # if sign-up validate registration form and create user
    elif (option == "sign-up"):
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))

        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(email=form.email.data.lower(), firstname=form.firstname.data.capitalize(), lastname=form.lastname.data.capitalize())
            user.set_password(form.password.data)
            try:
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                print("\n FAILED entry: {}\n".format(json.dumps(data)))
                print(e)
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('main.login'))
        return render_template('welcome.html', form=form, loginOption=option)

    # reset-login
    elif (option == "reset-login"):
        form = ResetForm()
        flash('reset function not set yet')
        return render_template('welcome.html', form=form, loginOption=option)

    return render_template('welcome.html', form=form)
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/logout')
@login_required
def logout():
    '''Logout Function

    *login required*

    :return: Log the user out
    '''
    logout_user()
    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------
# ----- Admin & skrunkworks stuff
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/db')
@login_required
def showdb():
    if current_user.email == "admin" or current_user.id == 2:
        Users = User.query.all()
        Posts = Post.query.order_by(Post.id.desc()).all()
        Friends = Friend.query.all()
        Channels = Channel.query.all()
        for post in Posts:
            post.body = post.body[0:100]

        return render_template('result.html', Users=Users, Posts=Posts, friends=Friends, channels=Channels)

    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/delshareid/<int:id>', methods=['GET'])
@login_required
def delShareId(id):
    if current_user.email == "admin":
        shared = AllPosts.query.filter_by(id=id).first()
        if shared is None:
            return "id not found"
        else:
            db.session.delete(shared)
            db.session.commit()

        return redirect(url_for('main.showdb'))

    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/delid/<int:id>', methods=['GET'])
@login_required
def delID(id):
    if current_user.email == "admin":
        user = User.query.filter_by(id=id).first()
        if user is None:
            return "id not found"
        else:
            db.session.delete(user)
            db.session.commit()

        return redirect(url_for('main.showdb'))

    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/db_init')
def fillCheck():
    db.create_all()
    user = User.query.first()
    if user is not None:
        return str(user.email)
    addadmin()
    return redirect(url_for('main.showdb'))

def addadmin():
    u1, u2, u3, u4, u5, u6, u7 = users = [
    User(firstname='admin', lastname='sidenote', email='admin', admin_level='0', access_type='999'),
    User(firstname='Tai', lastname='Huynh', email='tai@mail.com', status=0, title='Project Architect', imgUrl='avatar-13.png', admin_level='0', access_type='2'),
    User(firstname='Alice', lastname='Hawker', email='alice@mail.com', status=0, title='Tai\'s Girlfriend (Girl Bot)', imgUrl='avatar-10.png', access_type='10'),
    User(firstname='Nathaniel', lastname='Wallace', email='nathaniel@mail.com', status=1, title='UX Designer', imgUrl='avatar-2.png', access_type='3'),
    User(firstname='Tatsuya', lastname='Hayashi', email='tatsuya@mail.com', status=0, title='HR Specialist', imgUrl='avatar-7.png', access_type='5'),
    User(firstname='Daniel', lastname='Saneel', email='daniel@mail.com', status=2, title='Marketing Guru', imgUrl='avatar-8.png', access_type='4'),
    User(firstname='Ishie', lastname='Eswar', email='ishie@mail.com', status=2, title='CEO', imgUrl='avatar-6.png', access_type='1')
    ]
    c1, c2, c3, c4, c5, c6 = channels = [
    Channel(b64name='I0hvbWU=', owner_id='1', name='#Home', title='Main Lobby', access_type='0', imgUrl='lobby.png'),
    Channel(b64name='I0VuZ2luZWVyLVRlYW0=', owner_id='1', name='#Engineer-Team', title='Engineer Lounge - coder only!', imgUrl='coder.png'),
    Channel(b64name='I0Rlc2lnbi1UZWFt', owner_id='1', name='#Design-Team', title='UI & UX Designers House', imgUrl='ux.png'),
    Channel(b64name='I01hcmtldGluZy1UZWFt', owner_id='1', name='#Marketing-Team', title='Killer Marketing Team - "essential"', imgUrl='marketing.png'),
    Channel(b64name='I0h1bWFuLVJlc291cmNlcw==', owner_id='1', name='#Human-Resources', title='Gatekeeper of policy and guideline',  imgUrl='hr.png'),
    Channel(b64name='I0V4ZWN1dGl2ZS1PZmZpY2U=', owner_id='1', name='#Executive-Office', title='The Office of the Executive', access_type='999', imgUrl='ceo.png')
    ]
    u1.set_password('1234')
    u2.set_password('1234')
    u3.set_password('1234')
    u4.set_password('1234')
    u5.set_password('1234')
    u6.set_password('1234')
    u7.set_password('1234')
    
    try:
        db.session.add_all(users)
        db.session.add_all(channels)
        u2.channels.append(ChannelRelationship(users=c2))
        u2.channels.append(ChannelRelationship(users=c3))
        u2.channels.append(ChannelRelationship(users=c4))
        u2.channels.append(ChannelRelationship(users=c5))
        u2.friendships.append(Friend(friendee=u3))
        u2.friendships.append(Friend(friendee=u4))
        u2.friendships.append(Friend(friendee=u5))
        u3.friendships.append(Friend(friendee=u2))
        u4.friendships.append(Friend(friendee=u2))
        u4.channels.append(ChannelRelationship(users=c3))
        u5.friendships.append(Friend(friendee=u2))
        u5.channels.append(ChannelRelationship(users=c5))
        u6.channels.append(ChannelRelationship(users=c4))
        u7.channels.append(ChannelRelationship(users=c6))
        db.session.commit()
        
    except Exception as e:
        return "FAILED entry: "+str(e)
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/db_clearposts')
@login_required
def clearPosts():
    if current_user.email == "admin":
        Post.query.delete()
        db.session.commit()
        return redirect(url_for('main.showdb'))

    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------
@main.route('/db_addposts')
@login_required
def addDB():
    if current_user.email == "admin":
        db.session.bulk_insert_mappings(
            Post,
            [
                dict(
                    body=genPosts(),
                    user_id=current_user.id
                )
                for i in range(random.randint(10, 30))
            ],
        )
        db.session.commit()

        return redirect(url_for('main.showdb'))

    return redirect(url_for('main.welcome'))
# -------------------------------------------------------------------------------------------------------------------------


def listToString(s, delimeter=' '):
    str1 = " "
    return (delimeter.join(str(v) for v in s))


def random_generator(size=4, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
