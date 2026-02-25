#!/usr/bin/env python
"""
Script de sauvegarde manuelle de la base de données PostgreSQL
À exécuter périodiquement pour des sauvegardes supplémentaires
"""

import os
import datetime
import subprocess
import sys
from pathlib import Path

def backup_database():
    """Crée une sauvegarde de la base de données PostgreSQL"""
    
    # Récupérer l'URL de la base depuis les variables d'environnement
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ Erreur: DATABASE_URL non définie")
        print("   Utilisez: $env:DATABASE_URL='postgresql://...'")
        return False
    
    # Créer le dossier backups s'il n'existe pas
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    # Générer un nom de fichier avec timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = backup_dir / f"backup_{timestamp}.sql"
    
    print(f"📦 Sauvegarde en cours...")
    print(f"   Fichier: {filename}")
    
    try:
        # Commande pg_dump
        cmd = f"pg_dump {db_url} > {filename}"
        
        # Exécuter la commande
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Vérifier la taille du fichier
            size = os.path.getsize(filename)
            print(f"✅ Sauvegarde réussie! ({size:,} octets)")
            
            # Garder seulement les 10 dernières sauvegardes
            cleanup_old_backups(backup_dir, keep=10)
            
            return True
        else:
            print(f"❌ Erreur pg_dump: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def cleanup_old_backups(backup_dir, keep=10):
    """Garde seulement les N sauvegardes les plus récentes"""
    backups = sorted(backup_dir.glob('backup_*.sql'), reverse=True)
    
    if len(backups) > keep:
        for old in backups[keep:]:
            old.unlink()
            print(f"   🗑️ Ancienne sauvegarde supprimée: {old.name}")

def list_backups():
    """Liste toutes les sauvegardes disponibles"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        print("📂 Aucun dossier backups trouvé")
        return
    
    backups = sorted(backup_dir.glob('backup_*.sql'), reverse=True)
    
    if not backups:
        print("📂 Aucune sauvegarde trouvée")
        return
    
    print(f"\n📋 Sauvegardes disponibles ({len(backups)}):")
    print("-" * 50)
    
    total_size = 0
    for i, b in enumerate(backups, 1):
        size = os.path.getsize(b)
        total_size += size
        mod_time = datetime.datetime.fromtimestamp(b.stat().st_mtime)
        print(f"{i:2}. {b.name}  ({size:,} octets)  {mod_time.strftime('%d/%m/%Y %H:%M')}")
    
    print("-" * 50)
    print(f"Total: {len(backups)} fichiers, {total_size:,} octets")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_backups()
    else:
        backup_database()