# run.py
import logging
from app import create_app
from flask import Flask

# ========================
# Configuration du logger
# ========================
# DEBUG pour tout voir dans la console
logging.basicConfig(
    level=logging.DEBUG,  # Niveau DEBUG pour voir tous les logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# Création de l'application
# ========================
app = create_app()

# ========================
# Gestion globale des exceptions
# ========================
@app.errorhandler(Exception)
def handle_exception(e):
    # Log complet de l'erreur avec stack trace
    logger.exception("💥 Erreur interne : %s", e)
    # Retourne un message générique au client
    return "Internal Server Error", 500

# ========================
# Exemple de log pour test utilisateurs
# ========================
@app.before_request
def log_user_request():
    from flask_login import current_user
    try:
        if current_user.is_authenticated:
            logger.debug(f"Utilisateur connecté: ID={current_user.id}, Email={current_user.email}, Role={current_user.role}")
        else:
            logger.debug("Utilisateur non connecté accédant à la page")
    except Exception as e:
        logger.warning(f"Impossible de récupérer current_user: {e}")

# ========================
# Lancement de l'application
# ========================
if __name__ == '__main__':
    # debug=True pour développement local
    # host='0.0.0.0' pour que le serveur soit accessible depuis l'extérieur
    logger.info("🔹 Démarrage de l'application Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)