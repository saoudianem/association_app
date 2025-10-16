from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from app.models import Message, Room
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app

# Liste des utilisateurs connectés
online_users = set()


# ✅ Connexion d’un utilisateur
@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        return
    online_users.add(current_user.username)
    emit("update_user_list", sorted(list(online_users)), broadcast=True)
    emit("system_message", {"text": f"✅ {current_user.username} s’est connecté"}, broadcast=True)


# 🚪 Déconnexion
@socketio.on("disconnect")
def handle_disconnect():
    if not current_user.is_authenticated:
        return
    if current_user.username in online_users:
        online_users.remove(current_user.username)
        emit("update_user_list", sorted(list(online_users)), broadcast=True)
        emit("system_message", {"text": f"❌ {current_user.username} s’est déconnecté"}, broadcast=True)


# 📥 Rejoindre / quitter un salon
@socketio.on("join_room")
def handle_join(data):
    join_room(data["room_id"])

@socketio.on("leave_room")
def handle_leave(data):
    leave_room(data["room_id"])


# 💬 Envoi d’un message texte
@socketio.on("send_message")
def handle_send_message(data):
    room = Room.query.get(data["room_id"])
    if not room:
        return

    msg = Message(
        content=data["content"],
        user_id=current_user.id,
        room_id=room.id,
        is_read=False
    )
    db.session.add(msg)
    db.session.commit()

    emit("receive_message", {
        "user": current_user.username,
        "content": data["content"],
        "timestamp": datetime.utcnow().strftime("%d/%m %H:%M"),
        "room_id": room.id,
        "user_id": current_user.id
    }, broadcast=True)


# 📎 Envoi d’un fichier via Socket.IO (optionnel mais cool)
@socketio.on("send_file")
def handle_send_file(data):
    """Réception d’un fichier (base64) envoyé par le client"""
    import base64

    file_data = data.get("file_data")
    filename = secure_filename(data.get("filename"))
    room_id = data.get("room_id")

    # 🔒 Vérifie les extensions autorisées
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return

    # 📂 Sauvegarde du fichier
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    with open(save_path, "wb") as f:
        f.write(base64.b64decode(file_data))

    # 💾 Enregistre le message
    msg = Message(
        content=None,
        user_id=current_user.id,
        room_id=room_id,
        file_path=f"uploads/{filename}"
    )
    db.session.add(msg)
    db.session.commit()

    # 📡 Diffuse à tous
    emit("receive_file", {
        "user": current_user.username,
        "room_id": room_id,
        "timestamp": datetime.utcnow().strftime("%d/%m %H:%M"),
        "file_path": f"uploads/{filename}",
        "ext": ext
    }, broadcast=True)
