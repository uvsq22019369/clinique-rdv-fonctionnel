# run.py
from app import create_app
import logging
import traceback
from flask import Flask

# =======================================================
# CONFIGURATION DU LOGGER
# =======================================================
logging.basicConfig(level=logging.DEBUG)  # DEBUG pour tout loguer
logger = logging.getLogger(__name__)

# Logger du serveur Flask (werkzeug)
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.DEBUG)

# =======================================================
# CRÉATION DE L'APPLICATION
# =======================================================
app = create_app()

# =======================================================
# GESTION GLOBALE DES EXCEPTIONS
# =======================================================
@app.errorhandler(Exception)
def handle_exception(e):
    # Affiche la trace complète dans la console
    print("💥 Exception attrapée !")
    traceback.print_exc()

    # Log complet via logger
    logger.exception("💥 Erreur interne : %s", e)

    # Retourne un message générique au client
    return "Internal Server Error", 500

# =======================================================
# LANCEMENT DU SERVEUR
# =======================================================
if __name__ == '__main__':
    # debug=True pour développement
    # host='0.0.0.0' pour que d'autres machines du réseau puissent accéder
    app.run(debug=True, host='0.0.0.0', port=5000)