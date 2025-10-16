from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="member")
    active = db.Column(db.Boolean, default=True, index=True)
    messages = db.relationship("Message", backref="user", lazy=True)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    # 🔽 ajoute tes helpers de rôle ici
    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_moderator(self) -> bool:
        return self.role == "moderator"

    def has_role(self, *roles) -> bool:
        return self.role in roles

    def is_active_member(self) -> bool:
        return self.active and self.role in {"admin", "moderator", "member"}

    def __repr__(self):
        return f"<User {self.username}>"

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    messages = db.relationship(
        "Message",
        backref="room",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Room {self.name}>"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    file_path = db.Column(db.String(255), nullable=True)  # 🆕

    def __repr__(self):
        return f"<Message {self.id} room={self.room_id}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
