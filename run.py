# run.py
from app import create_app
import logging
from flask import Flask

# Crée l'application
app = create_app()

# Configuration du logger
logging.basicConfig(level=logging.DEBUG)  # DEBUG pour tout loguer
logger = logging.getLogger(__name__)

# Gestion globale des exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    # Log complet de l'erreur avec stack trace
    logger.exception("💥 Erreur interne : %s", e)
    # Retourne un message générique au client
    return "Internal Server Error", 500

if __name__ == '__main__':
    # debug=True fonctionne localement
    # host='0.0.0.0' pour que Railway puisse accéder au port
    app.run(debug=True, host='0.0.0.0', port=5000)