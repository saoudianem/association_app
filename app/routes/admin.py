from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Room, Message
from app import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# === Tableau de bord général ===
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    total_users = User.query.count()
    total_rooms = Room.query.count()
    total_messages = Message.query.count()

    room_stats = []
    for room in Room.query.order_by(Room.name.asc()).all():
        count = Message.query.filter_by(room_id=room.id).count()
        room_stats.append({"name": room.name, "count": count})

    top_users = (
        db.session.query(User.username, db.func.count(Message.id).label("count"))
        .join(Message)
        .group_by(User.id)
        .order_by(db.func.count(Message.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_rooms=total_rooms,
        total_messages=total_messages,
        room_stats=room_stats,
        top_users=top_users,
    )


# === Gestion des utilisateurs avec recherche + pagination ===
@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    # ✅ Si le formulaire d’ajout est soumis
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "member")

        if not username or not password:
            flash("⚠️ Veuillez remplir tous les champs.", "warning")
            return redirect(url_for("admin.users"))

        # Vérifie si le nom d’utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash("🚫 Ce nom d’utilisateur existe déjà.", "danger")
            return redirect(url_for("admin.users"))

        # Crée et enregistre le nouvel utilisateur
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"✅ Utilisateur '{username}' ajouté avec succès.", "success")
        return redirect(url_for("admin.users"))

    # ✅ Sinon (GET) : on affiche la liste
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = User.query
    if search_query:
        query = query.filter(User.username.ilike(f"%{search_query}%"))

    pagination = query.order_by(User.username.asc()).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return render_template(
        "admin_users.html",
        users=users,
        pagination=pagination,
        search_query=search_query
    )


# ✅ Activer / désactiver un utilisateur
@admin_bp.route("/toggle/<int:user_id>")
@login_required
def toggle_user(user_id):
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        flash("🚫 Impossible de désactiver l’administrateur principal.", "danger")
        return redirect(url_for("admin.users"))

    user.active = not user.active
    db.session.commit()
    status = "activé" if user.active else "désactivé"
    flash(f"✅ Utilisateur {user.username} {status}.", "success")
    return redirect(url_for("admin.users"))


# 🏅 Promouvoir / rétrograder un utilisateur
@admin_bp.route("/promote/<int:user_id>")
@login_required
def promote_user(user_id):
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        flash("🚫 Impossible de modifier le rôle de l’administrateur principal.", "danger")
        return redirect(url_for("admin.users"))

    if user.role == "admin":
        user.role = "member"
        flash(f"👤 {user.username} est redevenu membre.", "info")
    else:
        user.role = "admin"
        flash(f"⭐ {user.username} est maintenant administrateur.", "success")

    db.session.commit()
    return redirect(url_for("admin.users"))

# 🗑️ Supprimer un utilisateur
@admin_bp.route("/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    # protection : on ne supprime pas le compte admin principal
    if user.username == "admin":
        flash("🚫 Impossible de supprimer l’administrateur principal.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"🗑️ Utilisateur '{user.username}' supprimé avec succès.", "success")
    return redirect(url_for("admin.users"))

# ✏️ Modifier un utilisateur (rôle ou mot de passe)
@admin_bp.route("/edit/<int:user_id>", methods=["POST"])
@login_required
def edit_user(user_id):
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        flash("🚫 Impossible de modifier l’administrateur principal.", "danger")
        return redirect(url_for("admin.users"))

    new_role = request.form.get("role")
    new_password = request.form.get("password")

    # Mise à jour du rôle
    if new_role and new_role != user.role:
        user.role = new_role
        flash(f"✅ Rôle de {user.username} mis à jour en '{new_role}'.", "success")

    # Mise à jour du mot de passe
    if new_password:
        user.set_password(new_password)
        flash(f"🔒 Mot de passe de {user.username} réinitialisé.", "info")

    db.session.commit()
    return redirect(url_for("admin.users"))

# 🔁 Réinitialiser le mot de passe d’un utilisateur
@admin_bp.route("/reset_password/<int:user_id>", methods=["POST"])
@login_required
def reset_password(user_id):
    if current_user.role != "admin":
        flash("⛔ Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    if user.username == "admin":
        flash("🚫 Impossible de réinitialiser le mot de passe de l’administrateur principal.", "danger")
        return redirect(url_for("admin.users"))

    # Nouveau mot de passe temporaire
    new_password = "Temp1234!"
    user.set_password(new_password)
    db.session.commit()

    flash(f"🔁 Mot de passe de {user.username} réinitialisé : <b>{new_password}</b>", "info")
    return redirect(url_for("admin.users"))
