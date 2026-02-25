from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt, limiter
from models import User
from app.utils.decorators import super_admin_required
from app.utils.logger import (
    log_successful_login, log_failed_login, log_logout,
    log_password_change, log_failed_password_change, log_account_created
)
import re
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# =======================================================
# FONCTION DE VALIDATION DES MOTS DE PASSE
# =======================================================
def validate_password(password):
    """
    Vérifie la force d'un mot de passe
    Retourne (bool, message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not re.search(r"[0-9]", password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    return True, "OK"


# =======================================================
# CONNEXION
# =======================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('appointments.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False
        
        if not email or not password:
            flash('Veuillez remplir tous les champs', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        ip = request.remote_addr  # Récupère l'IP du client
        
        if user and bcrypt.check_password_hash(user.mot_de_passe_hash, password):
            
            # Vérifier que l'utilisateur est actif
            if not user.actif:
                log_failed_login(email, ip, "Compte désactivé")
                flash('Votre compte est désactivé. Contactez l\'administrateur.', 'danger')
                return render_template('login.html')
            
            # Vérifier que l'utilisateur a une clinique (sauf super_admin)
            if user.role != 'super_admin' and not user.clinique_id:
                log_failed_login(email, ip, "Pas de clinique associée")
                flash('Votre compte n\'est pas associé à une clinique. Contactez l\'administrateur.', 'danger')
                return render_template('login.html')
            
            # Vérifier l'abonnement de la clinique (sauf super_admin)
            if user.role != 'super_admin' and user.clinique:
                if user.clinique.date_fin_abonnement and user.clinique.date_fin_abonnement < datetime.now():
                    log_failed_login(email, ip, "Abonnement expiré")
                    flash('L\'abonnement de votre clinique a expiré. Contactez l\'administrateur.', 'danger')
                    return render_template('login.html')
                
                if not user.clinique.abonnement_actif:
                    log_failed_login(email, ip, "Abonnement inactif")
                    flash('L\'abonnement de votre clinique est inactif. Contactez l\'administrateur.', 'danger')
                    return render_template('login.html')
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # Log de connexion réussie
            log_successful_login(user.id, user.email, ip)
            
            flash(f'Bienvenue {user.nom}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('appointments.dashboard'))
        else:
            # Log de tentative échouée
            log_failed_login(email, ip)
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')


# =======================================================
# INSCRIPTION (admin uniquement)
# =======================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@super_admin_required
def register():
    """Inscription d'un nouveau médecin (admin uniquement)"""
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        telephone = request.form.get('telephone', '').strip()
        specialite = request.form.get('specialite', '').strip()
        ip = request.remote_addr
        
        # Validations
        errors = []
        
        if not nom or len(nom) < 2:
            errors.append("Le nom doit contenir au moins 2 caractères")
        
        if not email or '@' not in email:
            errors.append("Email invalide")
        
        # Validation du mot de passe avec notre nouvelle fonction
        is_valid, msg = validate_password(password)
        if not is_valid:
            errors.append(msg)
        
        if password != confirm_password:
            errors.append("Les mots de passe ne correspondent pas")
        
        if not telephone or len(telephone) < 9:
            errors.append("Numéro de téléphone invalide")
        
        # Vérifier si l'utilisateur existe déjà
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            errors.append("Cet email est déjà utilisé")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', 
                                 nom=nom, email=email, telephone=telephone, specialite=specialite)
        
        # Créer le nouvel utilisateur
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            nom=nom,
            email=email,
            mot_de_passe_hash=hashed_password,
            telephone=telephone,
            specialite=specialite,
            role='medecin',
            actif=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log de création de compte
        log_account_created(new_user.id, new_user.email, current_user.email, ip)
        
        print(f"Nouvel utilisateur créé par admin: {email} - {nom}")
        flash(f'Médecin {nom} créé avec succès!', 'success')
        return redirect(url_for('admin.gestion_utilisateurs'))
    
    return render_template('register.html')


# =======================================================
# DÉCONNEXION
# =======================================================
@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    # Log de déconnexion
    log_logout(current_user.id, current_user.email)
    
    nom = current_user.nom
    logout_user()
    flash(f'À bientôt {nom}!', 'info')
    return redirect(url_for('auth.login'))


# =======================================================
# PROFIL UTILISATEUR
# =======================================================
@auth_bp.route('/profil')
@login_required
def profil():
    """Page de profil utilisateur"""
    return render_template('profil.html', user=current_user)


@auth_bp.route('/profil/modifier', methods=['POST'])
@login_required
def modifier_profil():
    """Modifier les informations du profil"""
    nom = request.form.get('nom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    specialite = request.form.get('specialite', '').strip()
    
    if nom and len(nom) >= 2:
        current_user.nom = nom
    
    if telephone and len(telephone) >= 9:
        current_user.telephone = telephone
    
    if specialite:
        current_user.specialite = specialite
    
    db.session.commit()
    flash('Profil mis à jour avec succès', 'success')
    return redirect(url_for('auth.profil'))


# =======================================================
# CHANGEMENT DE MOT DE PASSE
# =======================================================
@auth_bp.route('/changer-mot-de-passe', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def changer_mot_de_passe():
    """Changer le mot de passe"""
    ancien = request.form.get('ancien_mot_de_passe', '')
    nouveau = request.form.get('nouveau_mot_de_passe', '')
    confirmer = request.form.get('confirmer_mot_de_passe', '')
    ip = request.remote_addr
    
    if not bcrypt.check_password_hash(current_user.mot_de_passe_hash, ancien):
        log_failed_password_change(current_user.id, current_user.email, ip, "Ancien mot de passe incorrect")
        flash('Ancien mot de passe incorrect', 'danger')
        return redirect(url_for('auth.profil'))
    
    # Validation du nouveau mot de passe
    is_valid, msg = validate_password(nouveau)
    if not is_valid:
        log_failed_password_change(current_user.id, current_user.email, ip, msg)
        flash(msg, 'danger')
        return redirect(url_for('auth.profil'))
    
    if nouveau != confirmer:
        log_failed_password_change(current_user.id, current_user.email, ip, "Les mots de passe ne correspondent pas")
        flash('Les mots de passe ne correspondent pas', 'danger')
        return redirect(url_for('auth.profil'))
    
    current_user.mot_de_passe_hash = bcrypt.generate_password_hash(nouveau).decode('utf-8')
    db.session.commit()
    
    log_password_change(current_user.id, current_user.email, ip)
    flash('Mot de passe changé avec succès', 'success')
    return redirect(url_for('auth.profil'))


# =======================================================
# CHANGEMENT DE LANGUE
# =======================================================
@auth_bp.route('/changer-langue/<lang>')
@login_required
def changer_langue(lang):
    """Changer la langue de l'interface"""
    if lang in ['fr', 'en']:
        session['language'] = lang
        flash('Langue changée avec succès', 'success')
    return redirect(request.referrer or url_for('appointments.dashboard'))