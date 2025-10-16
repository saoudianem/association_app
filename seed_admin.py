from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin", active=True)
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin créé : admin / admin")
    else:
        print("ℹ️ Un utilisateur 'admin' existe déjà")
