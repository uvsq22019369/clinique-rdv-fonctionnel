# run.py
from app import create_app
import logging
from flask import Flask

# =========================
# CRÉATION DE L'APPLICATION
# =========================
app = create_app()

# =========================
# CONFIGURATION DU LOGGER
# =========================
# DEBUG pour tout loguer (affiche les erreurs et les infos)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
# GESTION GLOBALE DES EXCEPTIONS
# =========================
@app.errorhandler(Exception)
def handle_exception(e):
    # Log complet de l'erreur avec stack trace
    logger.exception("💥 Erreur interne : %s", e)
    # Retourne un message générique au client
    return "Internal Server Error", 500

# =========================
# LANCEMENT DE L'APPLICATION
# =========================
if __name__ == '__main__':
    # debug=True permet de voir les erreurs dans le navigateur et la console
    # host='0.0.0.0' permet d'accéder depuis l'extérieur (Railway, Docker, etc.)
    app.run(debug=True, host='0.0.0.0', port=5000)