# run.py
from app import create_app
import logging
import traceback
import os
import sys

# Configuration des logs selon l'environnement
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

# Désactiver les logs verbeux de Werkzeug (requêtes HTTP)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Configuration du logger principal
if ENV == 'production':
    # En production : logs minimaux, fichier de log
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Désactiver complètement les logs de débogage
    logging.getLogger('werkzeug').disabled = True
else:
    # En développement : logs détaillés
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

app = create_app()

# Gestion globale des erreurs avec affichage adapté à l'environnement
@app.errorhandler(Exception)
def handle_exception(e):
    if ENV == 'production':
        # En production, log dans le fichier
        app.logger.error(f"Erreur: {type(e).__name__} - {str(e)}")
        app.logger.error(traceback.format_exc())
        return "Une erreur interne est survenue.", 500
    else:
        # En développement, affichage détaillé
        print("\n" + "="*60)
        print("❌ ERREUR DÉTECTÉE :")
        print("="*60)
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\nTraceback complet:")
        traceback.print_exc()
        print("="*60 + "\n")
        return f"Erreur interne: {str(e)}", 500
if __name__ == '__main__':
    print("="*60)
    print(f"🚀 Serveur démarré - Environnement: {ENV}")
    print(f"🔧 Debug mode: {DEBUG}")
    print(f"📌 Port: {PORT}")
    if ENV == 'development':
        print(f"👉 Accède à http://127.0.0.1:{PORT}")
    else:
        print("👉 Application en production")
    print("="*60)
    
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG
    )