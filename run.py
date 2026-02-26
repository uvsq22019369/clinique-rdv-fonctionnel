# run.py
from app import create_app
import logging

# Désactiver les logs verbeux
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = create_app()

# Gestion globale des erreurs (message générique)
@app.errorhandler(Exception)
def handle_exception(e):
    # On peut logguer minimalement si besoin
    print("Erreur interne serveur.")

    return "Une erreur interne est survenue.", 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )