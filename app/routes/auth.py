from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from app import db

# 🔐 Blueprint Authentification
auth_bp = Blueprint("auth", __name__)

# =======================================
# 🔑 Connexion utilisateur
# =======================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si l'utilisateur est déjà connecté, redirige vers l'accueil
    if current_user.is_authenticated:
        flash(f"Déjà connecté en tant que {current_user.username}", "info")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = User.query.filter_by(username=username).first()

        # Vérifie l'existence, le mot de passe et l'état actif
        if user and user.check_password(password) and user.active:
            login_user(user)
            flash(f"Bienvenue {user.username} 👋", "success")
            return redirect(url_for("main.index"))
        else:
            flash("❌ Identifiants invalides ou compte inactif.", "danger")

    return render_template("login.html")


# =======================================
# 🚪 Déconnexion utilisateur
# =======================================
@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("✅ Déconnexion réussie.", "info")
    return redirect(url_for("auth.login"))


# =======================================
# 🔒 Modification du mot de passe
# =======================================
@auth_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    # 🔒 Vérifie que seul un admin peut accéder à cette page
    if current_user.role != "admin":
        flash("⛔ Seul un administrateur peut modifier son mot de passe ici.", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        old_pw = request.form.get("old_password")
        new_pw = request.form.get("new_password")

        # Vérifie l'ancien mot de passe
        if not current_user.check_password(old_pw):
            flash("❌ Ancien mot de passe incorrect.", "danger")
        elif len(new_pw) < 6:
            flash("⚠️ Le nouveau mot de passe doit contenir au moins 6 caractères.", "warning")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("✅ Mot de passe administrateur mis à jour avec succès !", "success")
            return redirect(url_for("main.index"))

    return render_template("change_password.html")

