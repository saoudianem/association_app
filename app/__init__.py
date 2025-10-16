from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO(async_mode="threading")
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    login_manager.login_view = "auth.login"

    # Enregistrement des blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # Import des sockets (pour le chat en temps réel)
    from app import sockets

    # Création des tables (si pas encore existantes)
    with app.app_context():
        db.create_all()

    return app  # ✅ bien aligné, sans indentations en trop
