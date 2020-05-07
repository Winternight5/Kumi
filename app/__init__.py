from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_heroku import Heroku
from flask_socketio import SocketIO

socketio = SocketIO()
heroku = Heroku()
db = SQLAlchemy()
login = LoginManager()

def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config.from_object(Config)
    
    from .main import main as main_blueprint
    #from . import routes, events, models
    app.register_blueprint(main_blueprint)
    
    db.init_app(app)
    socketio.init_app(app)
    login.init_app(app)
    login.login_view = 'login'
    
    return app

