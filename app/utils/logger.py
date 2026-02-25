import logging
import os
from datetime import datetime

# Configuration du logger
def setup_logger():
    """Configure le logger pour les événements de sécurité"""
    
    # Créer le dossier logs s'il n'existe pas
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configuration du logger
    logging.basicConfig(
        filename=os.path.join(log_dir, 'security.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_failed_login(email, ip):
    """Enregistre une tentative de connexion échouée"""
    logging.warning(f"ÉCHEC CONNEXION - Email: {email}, IP: {ip}")

def log_successful_login(user_id, email, ip):
    """Enregistre une connexion réussie"""
    logging.info(f"CONNEXION RÉUSSIE - User: {user_id}, Email: {email}, IP: {ip}")

def log_logout(user_id, email):
    """Enregistre une déconnexion"""
    logging.info(f"DÉCONNEXION - User: {user_id}, Email: {email}")

def log_password_change(user_id, email, ip):
    """Enregistre un changement de mot de passe"""
    logging.info(f"CHANGEMENT MDP - User: {user_id}, Email: {email}, IP: {ip}")

def log_failed_password_change(user_id, email, ip, reason):
    """Enregistre un échec de changement de mot de passe"""
    logging.warning(f"ÉCHEC CHANGEMENT MDP - User: {user_id}, Email: {email}, IP: {ip}, Raison: {reason}")

def log_account_created(user_id, email, created_by, ip):
    """Enregistre la création d'un compte"""
    logging.info(f"COMPTE CRÉÉ - User: {user_id}, Email: {email}, Créé par: {created_by}, IP: {ip}")