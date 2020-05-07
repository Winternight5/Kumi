from datetime import datetime
from .. import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import backref


class User(UserMixin, db.Model):
    """
    This class is responsible for storing user's notes and login information.
    All of the attributes for this class are listed below. 
    """
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)
    firstname = db.Column(db.String(128))
    lastname = db.Column(db.String(128))
    title = db.Column(db.String(256))
    admin_level = db.Column(db.Integer)
    access_type = db.Column(db.Integer)
    password_hash = db.Column(db.String(128))
    settings = db.Column(db.Text, default='')
    imgUrl = db.Column(db.Text)
    status = db.Column(db.Integer)
    recent_channel = db.Column(db.Integer)
    last_login = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    chats = db.relationship('Post', backref='user', lazy='dynamic')
    channel_owner = db.relationship('Channel', backref='channel', lazy='dynamic')
    friendships = db.relationship(
        'Friend',
        foreign_keys='Friend.user_id',
        backref='friender',
    )
    friendships_of = db.relationship(
        'Friend',
        foreign_keys='Friend.friend_id',
        backref='friendee',
    )


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Post(db.Model):
    """
    This class is responsible for storing user's text messages.
    All of the attributes for this class are listed below. 
    """
    __tablename__ = "Post"
    id = db.Column(db.Integer, primary_key=True)
    b64name = db.Column(db.String(128), index=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    channel_id = db.Column(db.Integer, db.ForeignKey('Channel.id'))

    def __repr__(self):
        return '<Posts {}>'.format(self.id)

class Friend(db.Model):
    """
    This class contains the friend functionality. 
    All of the attributes for this class are listed below. 
    """
    __tablename__ = 'Friend'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    def __repr__(self):
        return '<Friend {}>'.format(self.id)

class Channel(db.Model):
    """
    This class contains the channel functionality. 
    All of the attributes for this class are listed below. 
    """
    __tablename__ = "Channel"
    id = db.Column(db.Integer, primary_key=True)
    b64name = db.Column(db.String(128), index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    name = db.Column(db.String(128))
    title = db.Column(db.String(256))
    access_type = db.Column(db.Integer)
    imgUrl = db.Column(db.Text)
    posts = db.relationship('Post', backref='channel', lazy='dynamic')

    def __repr__(self):
        return '<Channel {}>'.format(self.id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
