from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import secrets

db = SQLAlchemy()

# =======================================================
# MODÈLE CLINIQUE (avec gestion abonnement)
# =======================================================
class Clinique(db.Model):
    __tablename__ = 'cliniques'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Gestion abonnement
    abonnement_actif = db.Column(db.Boolean, default=True)
    date_debut_abonnement = db.Column(db.DateTime, default=datetime.utcnow)
    date_fin_abonnement = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    users = db.relationship('User', backref='clinique', lazy=True)
    patients = db.relationship('Patient', backref='clinique', lazy=True)
    appointments = db.relationship('Appointment', backref='clinique', lazy=True)
    availabilities = db.relationship('Availability', backref='clinique', lazy=True)
    prescriptions = db.relationship('Prescription', backref='clinique', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(200), nullable=False)
    
    # Rôles étendus
    role = db.Column(db.String(20), default='medecin')
    # Possibilités : 'super_admin', 'admin_clinique', 'medecin', 'secretaire'
    
    telephone = db.Column(db.String(20))
    specialite = db.Column(db.String(100))
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Lien vers clinique (NULL pour super_admin)
    clinique_id = db.Column(db.Integer, db.ForeignKey('cliniques.id'), nullable=True)
    
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, foreign_keys='Appointment.medecin_id')
    availabilities = db.relationship('Availability', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True, foreign_keys='Prescription.medecin_id')

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    date_naissance = db.Column(db.Date)
    adresse = db.Column(db.String(200))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Lien vers clinique
    clinique_id = db.Column(db.Integer, db.ForeignKey('cliniques.id'), nullable=False)
    
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure = db.Column(db.String(5), nullable=False)
    motif = db.Column(db.String(200))
    statut = db.Column(db.String(20), default='confirme')
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Token unique pour annulation
    annulation_token = db.Column(db.String(100), unique=True, nullable=False, 
                                  default=lambda: secrets.token_urlsafe(32))
    
    # Lien vers clinique
    clinique_id = db.Column(db.Integer, db.ForeignKey('cliniques.id'), nullable=False)
    
    prescription = db.relationship('Prescription', backref='appointment', uselist=False, lazy=True)

class Availability(db.Model):
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    medecin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_debut = db.Column(db.String(5), nullable=False)
    heure_fin = db.Column(db.String(5), nullable=False)
    duree_rdv = db.Column(db.Integer, default=30)
    
    # Lien vers clinique
    clinique_id = db.Column(db.Integer, db.ForeignKey('cliniques.id'), nullable=False)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    medicaments = db.Column(db.Text, nullable=False)
    conseils = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    fichier_pdf = db.Column(db.String(200))
    
    # Lien vers clinique
    clinique_id = db.Column(db.Integer, db.ForeignKey('cliniques.id'), nullable=False)