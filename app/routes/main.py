from flask import Blueprint, render_template
from flask_login import login_required
from app.models import User, Message

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@login_required
def index():
    total_users = User.query.count()
    total_messages = Message.query.count()
    latest_messages = Message.query.order_by(Message.timestamp.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_messages=total_messages,
        latest_messages=latest_messages
    )
