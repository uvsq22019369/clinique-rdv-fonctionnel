from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from models import Clinique, User, Availability, Appointment, Patient
from datetime import datetime, timedelta
from app.utils.email_utils import envoyer_confirmation_annulation, envoyer_confirmation_rdv
from app.utils.sms_utils import envoyer_sms_confirmation_rdv, formater_numero_senegal

public_bp = Blueprint('public', __name__)

# =======================================================
# ROUTES D'ANNULATION (existantes)
# =======================================================
@public_bp.route('/annuler-rdv/<token>')
def annuler_rdv_public(token):
    """Page publique d'annulation de rendez-vous"""
    rdv = Appointment.query.filter_by(annulation_token=token).first()

    if not rdv:
        flash('Lien d\'annulation invalide ou expiré', 'danger')
        return redirect(url_for('auth.login'))

    # Vérifier que le RDV n'est pas déjà passé
    if rdv.date < datetime.now().date():
        flash('Ce rendez-vous est déjà passé', 'warning')
        return redirect(url_for('auth.login'))

    # Vérifier que le RDV n'est pas déjà annulé
    if rdv.statut == 'annule':
        flash('Ce rendez-vous a déjà été annulé', 'info')
        return redirect(url_for('auth.login'))

    return render_template('public/annuler_rdv.html', rdv=rdv, token=token)


@public_bp.route('/annuler-rdv/<token>/confirmer', methods=['POST'])
def confirmer_annulation(token):
    """Confirmer l'annulation"""
    rdv = Appointment.query.filter_by(annulation_token=token).first()

    if not rdv:
        flash('Lien d\'annulation invalide', 'danger')
        return redirect(url_for('auth.login'))

    # Sauvegarder les infos pour l'email avant de modifier
    patient_nom = rdv.patient.nom
    patient_email = rdv.patient.email
    date_rdv = rdv.date.strftime('%d/%m/%Y')
    heure_rdv = rdv.heure
    medecin_nom = rdv.doctor.nom

    # Annuler le rendez-vous
    rdv.statut = 'annule'
    db.session.commit()

    # Envoyer email de confirmation d'annulation
    if patient_email:
        envoyer_confirmation_annulation(
            patient_nom=patient_nom,
            patient_email=patient_email,
            date_rdv=date_rdv,
            heure_rdv=heure_rdv,
            medecin_nom=medecin_nom
        )

    flash('Votre rendez-vous a bien été annulé', 'success')
    return redirect(url_for('public.annulation_confirmee'))


@public_bp.route('/annulation-confirmee')
def annulation_confirmee():
    """Page de confirmation d'annulation"""
    return render_template('public/annulation_confirmee.html')


# =======================================================
# ROUTES PUBLIQUES DE PRISE DE RENDEZ-VOUS
# =======================================================
@public_bp.route('/<slug>/prendre-rdv')
def prendre_rdv_public(slug):
    """Page publique de prise de rendez-vous pour une clinique"""
    clinique = Clinique.query.filter_by(slug=slug, abonnement_actif=True).first_or_404()
    
    # Récupérer les médecins actifs de cette clinique
    medecins = User.query.filter_by(
        role='medecin',
        actif=True,
        clinique_id=clinique.id
    ).all()
    
    return render_template('public/prendre_rdv.html', clinique=clinique, medecins=medecins)


@public_bp.route('/public/disponibilites/<int:medecin_id>/<date>')
def get_disponibilites_public(medecin_id, date):
    """API publique pour les disponibilités"""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Vérifier que le médecin existe
        medecin = User.query.get_or_404(medecin_id)
        
        # Récupérer les disponibilités
        dispos = Availability.query.filter_by(
            medecin_id=medecin_id,
            date=date_obj
        ).first()
        
        # Récupérer les rendez-vous déjà pris
        rdv_pris = Appointment.query.filter_by(
            medecin_id=medecin_id,
            date=date_obj,
            statut='confirme'
        ).all()
        
        heures_pris = [r.heure for r in rdv_pris]
        
        creneaux = []
        if dispos:
            debut = datetime.strptime(dispos.heure_debut, '%H:%M')
            fin = datetime.strptime(dispos.heure_fin, '%H:%M')
            duree = dispos.duree_rdv or 30
            
            current = debut
            while current < fin:
                heure_str = current.strftime('%H:%M')
                if heure_str not in heures_pris:
                    creneaux.append(heure_str)
                current += timedelta(minutes=duree)
        
        return {'creneaux': creneaux}
    except Exception as e:
        return {'creneaux': [], 'error': str(e)}


@public_bp.route('/<slug>/reserver', methods=['POST'])
def reserver_rdv_public(slug):
    """Réservation publique de rendez-vous"""
    clinique = Clinique.query.filter_by(slug=slug).first_or_404()
    
    medecin_id = request.form.get('medecin_id')
    patient_nom = request.form.get('patient_nom', '').strip()
    patient_tel = request.form.get('patient_tel', '').strip()
    patient_email = request.form.get('patient_email', '').strip()
    date = request.form.get('date')
    heure = request.form.get('heure')
    motif = request.form.get('motif', '').strip()
    
    if not all([medecin_id, patient_nom, patient_tel, date, heure]):
        flash('Tous les champs sont obligatoires', 'danger')
        return redirect(url_for('public.prendre_rdv_public', slug=slug))
    
    try:
        # Créer ou récupérer le patient
        patient = Patient.query.filter_by(telephone=patient_tel).first()
        if not patient:
            patient = Patient(
                nom=patient_nom,
                telephone=patient_tel,
                email=patient_email if patient_email else None,
                clinique_id=clinique.id
            )
            db.session.add(patient)
            db.session.commit()
        
        # Vérifier disponibilité
        rdv_existant = Appointment.query.filter_by(
            medecin_id=medecin_id,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            heure=heure,
            statut='confirme'
        ).first()
        
        if rdv_existant:
            flash('Ce créneau n\'est plus disponible', 'danger')
            return redirect(url_for('public.prendre_rdv_public', slug=slug))
        
        # Créer le rendez-vous
        rdv = Appointment(
            patient_id=patient.id,
            medecin_id=medecin_id,
            clinique_id=clinique.id,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            heure=heure,
            motif=motif,
            statut='confirme'
        )
        
        db.session.add(rdv)
        db.session.commit()
        
        # Envoyer confirmation
        medecin = User.query.get(medecin_id)
        date_formatee = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        if patient.email:
            envoyer_confirmation_rdv(
                patient_nom=patient.nom,
                patient_email=patient.email,
                date_rdv=date_formatee,
                heure_rdv=heure,
                medecin_nom=medecin.nom,
                annulation_token=rdv.annulation_token
            )
        
        if patient.telephone:
            try:
                numero_sms = formater_numero_senegal(patient.telephone)
                envoyer_sms_confirmation_rdv(
                    numero=numero_sms,
                    patient_nom=patient.nom,
                    date_rdv=date_formatee,
                    heure_rdv=heure,
                    medecin_nom=medecin.nom
                )
            except Exception as e:
                print(f"Erreur SMS: {e}")
        
        flash('Rendez-vous confirmé ! Vous allez recevoir une confirmation par SMS.', 'success')
        return redirect(url_for('public.confirmation_page', slug=slug))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('public.prendre_rdv_public', slug=slug))


@public_bp.route('/<slug>/merci')
def confirmation_page(slug):
    """Page de confirmation après réservation"""
    clinique = Clinique.query.filter_by(slug=slug).first_or_404()
    return render_template('public/confirmation.html', clinique=clinique)