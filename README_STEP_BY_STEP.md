    # Intranet Associatif — Installation (sans environnement virtuel)

    ## 1) Installer les dépendances globalement
    pip install -r requirements.txt

    ## 2) Initialiser la base de données
    python -c "from app import create_app, db; app=create_app(); from flask_migrate import upgrade as _u; print('✔ Base prête')"

    (ou simplement)
    python - <<'PY'
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
print("✔ Tables créées")
PY

    ## 3) Créer l'admin par défaut
    python seed_admin.py

    Identifiants: admin / admin

    ## 4) Lancer le serveur
    python run.py

    Ouvrez http://localhost:5001 dans votre navigateur.
