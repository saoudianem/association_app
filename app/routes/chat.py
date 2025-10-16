from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Message, Room
from app import db

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


# 🧭 Liste des salons
@chat_bp.route("/")
@login_required
def room_list():
    rooms = Room.query.order_by(Room.name.asc()).all()

    # Crée un salon "Général" s’il n’existe pas encore
    if not rooms:
        general = Room(name="Général")
        db.session.add(general)
        db.session.commit()
        rooms = [general]

    # 🔔 Ajoute un compteur de messages non lus pour chaque salon
    for room in rooms:
        room.unread_count = (
            Message.query.filter_by(room_id=room.id, is_read=False)
            .filter(Message.user_id != current_user.id)
            .count()
        )

    return render_template("rooms.html", rooms=rooms)


# ✅ Création de salon (admin seulement)
@chat_bp.route("/create", methods=["POST"])
@login_required
def create_room():
    if current_user.role != "admin":
        flash("⚠️ Seuls les administrateurs peuvent créer des salons.", "warning")
        return redirect(url_for("chat.room_list"))

    name = request.form.get("name", "").strip()
    if not name:
        flash("Le nom du salon ne peut pas être vide.", "danger")
        return redirect(url_for("chat.room_list"))

    if Room.query.filter_by(name=name).first():
        flash("Un salon avec ce nom existe déjà.", "warning")
        return redirect(url_for("chat.room_list"))

    room = Room(name=name)
    db.session.add(room)
    db.session.commit()
    flash(f"✅ Salon '{name}' créé avec succès !", "success")
    return redirect(url_for("chat.room_list"))


# ✏️ Modification du nom d’un salon
@chat_bp.route("/<int:room_id>/edit", methods=["POST"])
@login_required
def edit_room(room_id):
    if current_user.role != "admin":
        flash("⚠️ Seuls les administrateurs peuvent modifier un salon.", "warning")
        return redirect(url_for("chat.room_list"))

    room = Room.query.get_or_404(room_id)
    new_name = request.form.get("new_name", "").strip()
    if not new_name:
        flash("Le nom du salon ne peut pas être vide.", "danger")
        return redirect(url_for("chat.room_list"))

    if Room.query.filter(Room.name == new_name, Room.id != room.id).first():
        flash("Un autre salon porte déjà ce nom.", "warning")
        return redirect(url_for("chat.room_list"))

    room.name = new_name
    db.session.commit()
    flash(f"✏️ Salon renommé en '{new_name}'", "info")
    return redirect(url_for("chat.room_list"))


# 🗑️ Suppression d’un salon
@chat_bp.route("/<int:room_id>/delete", methods=["POST"])
@login_required
def delete_room(room_id):
    if current_user.role != "admin":
        flash("⚠️ Seuls les administrateurs peuvent supprimer un salon.", "warning")
        return redirect(url_for("chat.room_list"))

    room = Room.query.get_or_404(room_id)
    if room.name.lower() == "général":
        flash("🚫 Impossible de supprimer le salon 'Général'.", "danger")
        return redirect(url_for("chat.room_list"))

    db.session.delete(room)
    db.session.commit()
    flash(f"🗑️ Salon '{room.name}' supprimé.", "success")
    return redirect(url_for("chat.room_list"))


# 💬 Affichage du chat d’un salon
@chat_bp.route("/<int:room_id>")
@login_required
def chat(room_id):
    room = Room.query.get_or_404(room_id)

    # 🟢 Marquer les messages du salon comme lus pour l’utilisateur courant
    Message.query.filter_by(room_id=room.id, is_read=False).filter(
        Message.user_id != current_user.id
    ).update({"is_read": True})
    db.session.commit()

    messages = (
        Message.query.filter_by(room_id=room.id)
        .order_by(Message.timestamp.desc())
        .all()
    )

    return render_template("chat_room.html", room=room, messages=messages)

# ======================================================
# 📎 Upload d’un fichier (image ou PDF) dans un salon
# ======================================================
import os
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@chat_bp.route("/upload/<int:room_id>", methods=["POST"])
@login_required
def upload_file(room_id):
    """Permet à un utilisateur d'envoyer un fichier dans un salon"""
    file = request.files.get("file")

    # ⚠️ Aucun fichier sélectionné
    if not file or file.filename == "":
        flash("⚠️ Aucun fichier sélectionné.", "warning")
        return redirect(url_for("chat.chat", room_id=room_id))

    # ❌ Fichier non autorisé
    if not allowed_file(file.filename):
        flash("❌ Format de fichier non autorisé. (PDF, PNG, JPG, GIF uniquement)", "danger")
        return redirect(url_for("chat.chat", room_id=room_id))

    # 🔒 Sauvegarde sécurisée
    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    # 💾 Enregistrement du message dans la base
    msg = Message(
        content=None,
        user_id=current_user.id,
        room_id=room_id,
        file_path=f"uploads/{filename}"  # chemin relatif depuis /static/
    )
    db.session.add(msg)
    db.session.commit()

    flash("✅ Fichier envoyé avec succès !", "success")
    return redirect(url_for("chat.chat", room_id=room_id))
