# run.py
from app import create_app
import logging
import traceback

# Désactiver les logs verbeux
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = create_app()

# Gestion globale des erreurs avec affichage détaillé
@app.errorhandler(Exception)
def handle_exception(e):
    print("\n" + "="*60)
    print("❌ ERREUR DÉTECTÉE :")
    print("="*60)
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\nTraceback complet:")
    traceback.print_exc()  # ← Affiche la pile d'erreurs complète
    print("="*60 + "\n")
    
    return f"Erreur interne: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Démarrage du serveur...")
    print("👉 Accède à http://127.0.0.1:5000")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )