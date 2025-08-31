#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
from datetime import datetime

def load_json(file_path):
    """Charge un fichier JSON avec gestion des erreurs"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {file_path}: {e}")
        return None

def save_json(file_path, data):
    """Enregistre des données dans un fichier JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du fichier {file_path}: {e}")
        return False

def backup_file(file_path):
    """Crée une sauvegarde d'un fichier"""
    if not os.path.exists(file_path):
        return True
        
    backup_path = f"{file_path}.bak.{int(datetime.now().timestamp())}"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"Sauvegarde créée : {backup_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la création de la sauvegarde de {file_path}: {e}")
        return False

def migrate_stations_data():
    """Migre les données des stations vers le nouveau format"""
    print("\n=== Migration des données des stations ===")
    
    # Chemins des fichiers
    stations_path = "data/stations.json"
    etat_station_path = "data/etat_station.json"
    
    # Créer des sauvegardes
    if not backup_file(stations_path) or not backup_file(etat_station_path):
        print("❌ Échec de la création des sauvegardes. Annulation de la migration.")
        return False
    
    # Charger les données existantes
    stations = load_json(stations_path) or []
    etats = load_json(etat_station_path) or []
    
    # Créer un dictionnaire des états par ID de station
    etats_par_station = {}
    for etat in etats:
        station_id = etat.get('station_id')
        if station_id:
            if station_id not in etats_par_station:
                etats_par_station[station_id] = []
            etats_par_station[station_id].append(etat)
    
    # Mettre à jour les stations
    stations_mises_a_jour = []
    for station in stations:
        if not isinstance(station, dict):
            continue
            
        station_id = station.get('id')
        if not station_id:
            continue
        
        # Créer une copie de la station sans la clé 'ouvrages'
        nouvelle_station = {k: v for k, v in station.items() if k != 'ouvrages'}
        stations_mises_a_jour.append(nouvelle_station)
        
        # Vérifier si on a des états pour cette station
        if station_id in etats_par_station:
            # Mettre à jour les états existants
            for etat in etats_par_station[station_id]:
                if 'etat' in etat and 'etat_ouvrages' not in etat:
                    etat['etat_ouvrages'] = etat.pop('etat')
                
                # S'assurer que les champs de date sont présents
                if 'date' not in etat and 'date_maj' in etat:
                    etat['date'] = etat['date_maj'].split(' ')[0]
                elif 'date' not in etat:
                    etat['date'] = datetime.now().strftime('%Y-%m-%d')
                    
                if 'date_maj' not in etat:
                    etat['date_maj'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Créer un nouvel état si nécessaire
            if 'ouvrages' in station and isinstance(station['ouvrages'], dict):
                nouvel_etat = {
                    'station_id': station_id,
                    'date': station.get('date_creation', datetime.now().strftime('%Y-%m-%d')),
                    'etat_ouvrages': station['ouvrages'],
                    'date_maj': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                etats.append(nouvel_etat)
    
    # Enregistrer les données mises à jour
    if save_json(stations_path, stations_mises_a_jour):
        print(f"✅ {len(stations_mises_a_jour)} stations mises à jour avec succès")
    else:
        print("❌ Erreur lors de la sauvegarde des stations mises à jour")
        return False
    
    if save_json(etat_station_path, etats):
        print(f"✅ {len(etats)} états de station mis à jour avec succès")
    else:
        print("❌ Erreur lors de la sauvegarde des états de station mis à jour")
        return False
    
    return True

if __name__ == "__main__":
    print("=== MIGRATION DES DONNÉES VERS LE NOUVEAU FORMAT ===")
    print("Ce script va mettre à jour le format des données pour séparer les informations")
    print("des stations des états des ouvrages.\n")
    
    confirmation = input("Voulez-vous continuer ? (o/n) ").strip().lower()
    if confirmation != 'o':
        print("\nMigration annulée.")
        exit(0)
    
    print("\nDébut de la migration...")
    
    if migrate_stations_data():
        print("\n✅ Migration terminée avec succès !")
        print("Les fichiers originaux ont été sauvegardés avec l'extension .bak.timestamp")
    else:
        print("\n❌ La migration a échoué. Vérifiez les messages d'erreur ci-dessus.")
    
    input("\nAppuyez sur Entrée pour quitter...")
