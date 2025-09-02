#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
import logging
import time
from collections import OrderedDict

# Import des fonctions utilitaires
from utils import (
    clear_screen,
    log_erreur,
    log_info,
    log_avertissement,
    load_json,
    save_json
)

# Importer les utilitaires
from utils import get_stations_list, save_stations, update_stations_cache, get_station_by_id, charger_etats_station, sauvegarder_etats_station

# Configuration du logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def save_json(filename, data):
    """Sauvegarde des données dans un fichier JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

try:
    from gen_station import get_types, get_stations, get_etats, get_ouvrages_procede
    print("Import de gen_station réussi")
except ImportError as e:
    print("Erreur d'importation de gen_station:", e)
    raise

from create_station import create_station

def clear_screen():
    """Efface l'écran de la console avec un message de bienvenue"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[1;36m" + "=" * 50)
    print("   GESTION DES STATIONS D'ÉPURATION")
    print("=" * 50 + "\033[0m")

def show_menu():
    """Affiche le menu principal avec des icônes et des couleurs"""
    print("\n\033[1;34mMENU PRINCIPAL\033[0m")
    print("\033[1;32m➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖")
    print("\033[1;33m1. \033[0m➕ Créer une nouvelle station")
    print("\033[1;33m2. \033[0m📊 Afficher le schéma d'une station")
    print("\033[1;33m3. \033[0m🔄 Mettre à jour l'état des ouvrages")
    print("\033[1;33m4. \033[0m📋 Lister toutes les stations")
    print("\033[1;33m5. \033[0m🗑️  Supprimer une station")
    print("\033[1;31m6. ❌ Quitter\033[0m")
    print("\033[1;34m➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\033[0m")
    
    while True:
        try:
            choix = input("\n\033[1;36m🛠️  Votre choix (1-6): \033[0m").strip()
            if choix in ['1', '2', '3', '4', '5', '6']:
                return choix
            else:
                print("\033[1;31m❌ Erreur: Veuillez entrer un nombre entre 1 et 6\033[0m")
        except KeyboardInterrupt:
            print("\n\033[1;33mOpération annulée par l'utilisateur.\033[0m")
            return '6'
        except Exception as e:
            print(f"\033[1;31m❌ Erreur: {str(e)}\033[0m")

def select_station():
    """Permet à l'utilisateur de sélectionner une station"""
    clear_screen()
    print("\n\033[1;34mSELECTION D'UNE STATION\033[0m")
    print("-" * 40 + "\n")
    
    try:
        stations = get_stations_list()
        
        if not isinstance(stations, list) or not stations:
            print("\033[1;31m❌ Aucune station n'a été trouvée dans la base de données.\033[0m")
            return None
            
        print("Liste des stations disponibles :\n")
        for i, station in enumerate(stations, 1):
            print(f"{i}. {station.get('nom', 'Nom inconnu')} (ID: {station.get('id', 'N/A')})")
            
        while True:
            choix = input("\nEntrez le numéro de la station (ou Entrée pour annuler) : ").strip()
            if not choix:
                return None
                
            try:
                choix = int(choix) - 1
                if 0 <= choix < len(stations):
                    return stations[choix]
                print(f"\033[1;31m❌ Veuillez entrer un nombre entre 1 et {len(stations)}\033[0m")
            except ValueError:
                print("\033[1;31m❌ Veuillez entrer un numéro valide.\033[0m")
                
    except Exception as e:
        log.error(f"Erreur lors de la sélection de la station: {e}")
        return None

def show_schema():
    """Affiche le schéma d'une station sélectionnée"""
    while True:  # Boucle pour permettre à l'utilisateur de voir plusieurs schémas s'il le souhaite
        clear_screen()
        print("\033[1;34mAFFICHAGE DU SCHEMA\033[0m")
        print("-" * 40)
        print("Appuyez sur 'q' à tout moment pour revenir au menu précédent\n")
        
        # Importer la fonction de génération de diagramme
        from diagramme_flux import generer_diagramme_station
        
        try:
            # Appeler la fonction de génération de diagramme
            generer_diagramme_station()
            
            # Demander à l'utilisateur s'il souhaite voir un autre schéma
            choix = input("\nVoulez-vous voir un autre schéma ? (o/n) : ").strip().lower()
            if choix != 'o':
                break
                
        except KeyboardInterrupt:
            print("\n\033[1;33mOpération annulée par l'utilisateur.\033[0m")
            break
        except Exception as e:
            print(f"\n\033[1;31m❌ Erreur lors de la génération du schéma: {str(e)}\033[0m")
            import traceback
            traceback.print_exc()
            input("\nAppuyez sur Entrée pour continuer...")
            break

def update_ouvrage_state():
    """Met à jour l'état des ouvrages d'une station"""
    while True:
        clear_screen()
        print("\033[1;34mMISE À JOUR DE L'ÉTAT DES OUVRAGES\033[0m")
        print("-" * 40 + "\n")
        
        # Afficher le menu des options
        print("1. Créer une nouvelle mise à jour")
        print("2. Modifier une mise à jour existante")
        print("3. Retourner au menu principal")
        
        choix = input("\nVotre choix (1-3): ").strip()
        
        if choix == '1':
            # Créer une nouvelle mise à jour
            update_ouvrage_state_new()
        elif choix == '2':
            # Modifier une mise à jour existante
            update_ouvrage_state_edit()
        elif choix == '3':
            # Retour au menu principal
            return
        else:
            print("\033[1;31m❌ Choix invalide. Veuillez réessayer.\033[0m")
            time.sleep(1)

def update_ouvrage_state_new():
    """Crée une nouvelle mise à jour pour une station"""
    clear_screen()
    print("\033[1;34mNOUVELLE MISE À JOUR D'ÉTAT DES OUVRAGES\033[0m")
    print("-" * 40 + "\n")
    
    # Sélectionner une station
    station = select_station()
    if not station:
        return
        
    station_id = station.get('id')
    if not station_id:
        print("\033[1;31m❌ ID de station manquant. Opération annulée.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    # Charger les états existants
    etats_actuels = charger_etats_station()
    etats_station = etats_actuels.get(station_id, [])
    
    # Récupérer le dernier état si disponible
    etat_precedent = {}
    if etats_station:
        dernier_etat = max(etats_station, key=lambda x: x.get('date_maj', ''))
        etat_precedent = dernier_etat.get('etat_ouvrages', {})
    
    # Obtenir les ouvrages du procédé
    type_procede = station.get('type_procede')
    if not type_procede:
        print("\033[1;31m❌ Type de procédé non spécifié pour cette station.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    # Utiliser la fonction d'affichage et modification
    nouveaux_etats = afficher_et_modifier_etats(
        etat_precedent.copy() or get_ouvrages_procede(type_procede),
        station.get('nom'),
        type_procede
    )
    
    if not nouveaux_etats:
        print("\n\033[1;33mAucune modification apportée.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    # Créer la nouvelle entrée
    nouvelle_entree = {
        'etat_ouvrages': nouveaux_etats,
        'date_maj': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Ajouter à la liste des états
    if not isinstance(etats_station, list):
        etats_station = []
    etats_station.append(nouvelle_entree)
    etats_actuels[station_id] = etats_station
    
    # Sauvegarder les modifications
    if sauvegarder_etats_station(etats_actuels):
        print("\n\033[1;32m✅ Mise à jour enregistrée avec succès !\033[0m")
    else:
        print("\n\033[1;31m❌ Erreur lors de l'enregistrement de la mise à jour.\033[0m")
    
    input("\nAppuyez sur Entrée pour continuer...")

def update_ouvrage_state_edit():
    """Modifie une mise à jour existante pour une station"""
    clear_screen()
    print("\033[1;34mMODIFICATION D'UNE MISE À JOUR EXISTANTE\033[0m")
    print("-" * 40 + "\n")

    station = select_station()
    if not station:
        return

    station_id = station.get('id')
    if not station_id:
        print("\033[1;31m❌ ID de station manquant. Opération annulée.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # Charger les états existants
    etats_actuels = charger_etats_station()
    etats_station = etats_actuels.get(station_id, [])

    # S'assurer que c'est toujours une liste
    if isinstance(etats_station, dict):
        etats_station = [etats_station]
    
    if not etats_station:
        print("\033[1;33m⚠️  Aucune mise à jour trouvée pour cette station.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    # Trier par date (plus récent en premier)
    etats_station.sort(key=lambda x: x.get('date_maj', ''), reverse=True)
    
    # Afficher la liste des mises à jour disponibles
    clear_screen()
    print(f"\033[1;34mSÉLECTIONNEZ LA MISE À JOUR À MODIFIER - {station.get('nom', 'N/A').upper()}\033[0m")
    print("-" * 40 + "\n")
    
    print("Mises à jour disponibles :")
    for i, maj in enumerate(etats_station, 1):
        date_maj = maj.get('date', 'Date inconnue')
        print(f"{i}. {date_maj}")
    
    # Demander à l'utilisateur de choisir une mise à jour
    while True:
        choix = input("\nEntrez le numéro de la mise à jour à modifier (ou 'q' pour annuler) : ").strip()
        if choix.lower() == 'q':
            return
            
        try:
            choix_idx = int(choix) - 1
            if 0 <= choix_idx < len(etats_station):
                break
            print("\033[1;31mNuméro invalide. Veuillez réessayer.\033[0m")
        except ValueError:
            print("\033[1;31mVeuillez entrer un numéro valide.\033[0m")
    
    # Récupérer l'état des ouvrages de la mise à jour sélectionnée
    etat_ouvrages = etats_station[choix_idx].get('etat_ouvrages', {})

    # Afficher le contenu de etat_ouvrages
    print("\n\033[1;33m=== ÉTAT ACTUEL DES OUVRAGES ===\033[0m")
    if not etat_ouvrages:
        print("Aucun ouvrage trouvé dans cette mise à jour.")
    else:
        for ouvrage, etat in etat_ouvrages.items():
            print(f"- {ouvrage}: {etat}")

    input("\nAppuyez sur Entrée pour continuer...")
    
    # Modifier les états des ouvrages
    if not modifier_etats_ouvrages(etat_ouvrages, station.get('nom')):
        return
    
    # Mettre à jour la date de modification
    etats_station[choix_idx]['etat_ouvrages'] = etat_ouvrages
    etats_station[choix_idx]['date_maj'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Trier à nouveau par date (plus récent en premier)
    etats_station.sort(key=lambda x: x.get('date_maj', ''), reverse=True)
    
    # Sauvegarder les modifications
    etats_actuels[station_id] = etats_station
    if sauvegarder_etats_station(etats_actuels):
        print("\n\033[1;32m✅ Mise à jour modifiée avec succès !\033[0m")
    else:
        print("\n\033[1;31m❌ Erreur lors de la sauvegarde des modifications.\033[0m")
    
    time.sleep(2)

def modifier_etats_ouvrages(etat_ouvrages, nom_station, type_procede=None):
    modifications = False
    
    # Créer un nouveau dictionnaire ordonné pour stocker les résultats
    nouveaux_etats = OrderedDict()
    
    # Obtenir l'ordre des ouvrages selon le type de procédé
    if type_procede:
        ouvrages_ordre = get_ouvrages_procede(type_procede)
        if ouvrages_ordre:
            # Créer une liste ordonnée des ouvrages existants
            ouvrages_a_afficher = [o for o in ouvrages_ordre if o in etat_ouvrages]
            # Ajouter les ouvrages manquants
            for o in etat_ouvrages:
                if o not in ouvrages_a_afficher:
                    ouvrages_a_afficher.append(o)
        else:
            ouvrages_a_afficher = list(etat_ouvrages.keys())
    else:
        ouvrages_a_afficher = list(etat_ouvrages.keys())
    
    # Afficher et modifier chaque ouvrage dans l'ordre défini
    for i, nom in enumerate(ouvrages_a_afficher, 1):
        etat = etat_ouvrages[nom]
        # Ajouter l'état actuel au nouveau dictionnaire ordonné
        nouveaux_etats[nom] = etat
        
        etat_formate = etat.replace('_', ' ').capitalize()
        
        print(f"\n\033[1m--- Ouvrage {i}: {nom} (État actuel: {etat_formate}) ---\033[0m")
        print("1. ✅  En service (rendement conforme)")
        print("2. ❌  En panne (arrêt total)")
        print("3. ⚠️  En dysfonctionnement (fonctionnement dégradé)")
        print("4. 🔧  En maintenance (entretien/réparation)")
        print("5. 🚫  Hors service (non exploité)")
        print("6. ❓  Inexistant (non construit)")
        print("7. ⏸️  À l'arrêt volontaire (arrêt choisi)")
        print("8. 📈  Surchargé / Saturé (au-delà capacité)")
        print("9. ✨  Nouvel ouvrage (construit nouvellement)")
        print("10. ➡️  Passer au suivant")
        
        while True:
            choix = input("\nVotre choix (1-10): ").strip().lower()
            if not choix:
                print("Veuillez sélectionner une option valide.")
                continue
                
            if choix == '10' or choix == 'q':
                break
                
            etats = OrderedDict([
                ('1', 'en_service'),
                ('2', 'en_panne'),
                ('3', 'en_dysfonctionnement'),
                ('4', 'en_maintenance'),
                ('5', 'hors_service'),
                ('6', 'inexistant'),
                ('7', 'arret_volontaire'),
                ('8', 'surcharge_sature'),
                ('9', 'nouvel_ouvrage')
            ])
            
            if choix in etats:
                nouvel_etat = etats[choix]
                # Mettre à jour à la fois le dictionnaire ordonné et le dictionnaire d'origine
                nouveaux_etats[nom] = nouvel_etat
                etat_ouvrages[nom] = nouvel_etat
                print(f"État de {nom} mis à jour: {nouvel_etat.replace('_', ' ').title()}")
                modifications = True
                break
            else:
                print("❌ Option invalide. Veuillez réessayer.")
    
    # Mettre à jour le dictionnaire d'origine avec l'ordre correct
    etat_ouvrages.clear()
    etat_ouvrages.update(nouveaux_etats)
    
    return modifications

def select_etat_interactive():
    """Affiche un menu interactif pour sélectionner un état et le retourne."""
    etats_options = {
        '1': ('en_service', '✅ En service'),
        '2': ('en_panne', '❌ En panne'),
        '3': ('en_dysfonctionnement', '⚠️ En dysfonctionnement'),
        '4': ('en_maintenance', '🔧 En maintenance'),
        '5': ('hors_service', '⛔ Hors service'),
        '6': ('inexistant', '❓ Inexistant'),
        '7': ('arret_volontaire', '🛑 Arrêt volontaire'),
        '8': ('surcharge_sature', '📈 Surchargé / Saturé'),
        '9': ('nouvel_ouvrage', '✨ Nouvel ouvrage')
    }

    print("\n\033[1;34mChoisissez le nouvel état :\033[0m")
    for key, (_, display_text) in etats_options.items():
        print(f"  {key}. {display_text}")

    while True:
        choix = input("\nVotre choix (ou 'q' pour annuler) : ").strip()
        if choix.lower() == 'q':
            return None
        if choix in etats_options:
            return etats_options[choix][0]
        else:
            print("\033[1;31mChoix invalide. Veuillez réessayer.\033[0m")

def get_ouvrages_procede(type_procede):
    """
    Récupère la liste des ouvrages pour un type de procédé donné en respectant l'ordre logique de traitement.
    
    L'ordre logique est le suivant :
    1. Prétraitement (dégrillage, dessablage/dégraissage)
    2. Traitement primaire (décanteur primaire)
    3. Traitement secondaire (bassins d'aération, décanteur secondaire, etc.)
    4. Traitement tertiaire (filtration, désinfection)
    5. Traitement des boues (épaississement, déshydratation, séchage)
    """
    try:
        with open('data/types.json', 'r', encoding='utf-8') as f:
            types_data = json.load(f)

        procede_info = types_data.get(type_procede)
        if not procede_info:
            print(f"\033[1;31m❌ Type de procédé '{type_procede}' non trouvé.\033[0m")
            time.sleep(2)
            return None

        # Créer un dictionnaire ordonné pour maintenir l'ordre des ouvrages
        ouvrages_ordonnes = OrderedDict()
        
        # 1. Ajouter les ouvrages de prétraitement
        if 'filiere_eau' in procede_info and 'pretraitement' in procede_info['filiere_eau']:
            pretraitement = procede_info['filiere_eau']['pretraitement']
            if isinstance(pretraitement, list):
                for ouvrage in pretraitement:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = 'en_service'
            elif isinstance(pretraitement, str) and pretraitement.strip():
                ouvrages_ordonnes[pretraitement] = 'en_service'
        
        # 2. Ajouter le traitement primaire
        if 'filiere_eau' in procede_info and 'traitement_primaire' in procede_info['filiere_eau']:
            primaire = procede_info['filiere_eau']['traitement_primaire']
            if isinstance(primaire, list):
                for ouvrage in primaire:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = 'en_service'
            elif isinstance(primaire, str) and primaire.strip():
                ouvrages_ordonnes[primaire] = 'en_service'
        
        # 3. Ajouter le traitement secondaire
        if 'filiere_eau' in procede_info and 'traitement_secondaire' in procede_info['filiere_eau']:
            secondaire = procede_info['filiere_eau']['traitement_secondaire']
            if isinstance(secondaire, list):
                for ouvrage in secondaire:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = 'en_service'
            elif isinstance(secondaire, str) and secondaire.strip():
                ouvrages_ordonnes[secondaire] = 'en_service'
        
        # 4. Ajouter le traitement tertiaire
        if 'traitement_tertiaire' in procede_info:
            tertiaire = procede_info['traitement_tertiaire']
            if isinstance(tertiaire, list):
                for ouvrage in tertiaire:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = 'en_service'
            elif isinstance(tertiaire, str) and tertiaire.strip():
                ouvrages_ordonnes[tertiaire] = 'en_service'
        
        # 5. Ajouter la filière boue
        if 'filiere_boue' in procede_info:
            boues = procede_info['filiere_boue']
            if isinstance(boues, list):
                for ouvrage in boues:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = 'en_service'
            elif isinstance(boues, str) and boues.strip():
                ouvrages_ordonnes[boues] = 'en_service'
        
        return ouvrages_ordonnes
        
    except Exception as e:
        print(f"\033[1;31m❌ Erreur lors de la récupération des ouvrages : {str(e)}\033[0m")
        time.sleep(2)
        return None

def afficher_et_modifier_etats(etat_ouvrages, nom_station, type_procede=None):
    """
    Affiche et permet de modifier les états des ouvrages avec une interface cohérente.
    
    Args:
        etat_ouvrages (dict): Dictionnaire des états actuels des ouvrages
        nom_station (str): Nom de la station pour l'affichage
        type_procede (str, optional): Type de procédé pour ordonner les ouvrages
        
    Returns:
        dict: Dictionnaire des états mis à jour ou None si annulé
    """
    if not etat_ouvrages:
        return None
        
    print(f"\n\033[1;34mMODIFICATION DES OUVRAGES - {nom_station.upper()}\033[0m")
    print("\033[2m(Tapez 'q' pour terminer la mise à jour)\033[0m\n")
    
    # Créer une copie pour éviter de modifier l'original
    etats_mis_a_jour = etat_ouvrages.copy()
    
    # Obtenir l'ordre des ouvrages
    ouvrages_a_afficher = []
    if type_procede:
        ouvrages_ordre = get_ouvrages_procede(type_procede)
        if ouvrages_ordre:
            # D'abord les ouvrages dans l'ordre du procédé
            for ouvrage in ouvrages_ordre:
                if ouvrage in etats_mis_a_jour:
                    ouvrages_a_afficher.append(ouvrage)
            # Puis les autres ouvrages
            for ouvrage in etats_mis_a_jour:
                if ouvrage not in ouvrages_a_afficher:
                    ouvrages_a_afficher.append(ouvrage)
    
    if not ouvrages_a_afficher:
        ouvrages_a_afficher = list(etats_mis_a_jour.keys())
    
    # Afficher et modifier chaque ouvrage
    for i, nom in enumerate(ouvrages_a_afficher, 1):
        etat = etats_mis_a_jour[nom]
        etat_formate = etat.replace('_', ' ').capitalize()
        
        print(f"\n\033[1m--- Ouvrage {i}: {nom} (État actuel: {etat_formate}) ---\033[0m")
        print("1. ✅  En service (rendement conforme)")
        print("2. ❌  En panne (arrêt total)")
        print("3. ⚠️  En dysfonctionnement (fonctionnement dégradé)")
        print("4. 🔧  En maintenance (entretien/réparation)")
        print("5. 🚫  Hors service (non exploité)")
        print("6. ❓  Inexistant (non construit)")
        print("7. ⏸️  À l'arrêt volontaire (arrêt choisi)")
        print("8. 📈  Surchargé / Saturé (au-delà capacité)")
        print("9. ✨  Nouvel ouvrage (construit nouvellement)")
        print("10. ➡️  Passer au suivant")
        
        while True:
            choix = input("\nVotre choix (1-10): ").strip().lower()
            if not choix:
                print("Veuillez sélectionner une option valide.")
                continue
                
            if choix == '10' or choix == 'q':
                break
                
            etats = {
                '1': 'en_service',
                '2': 'en_panne',
                '3': 'en_dysfonctionnement',
                '4': 'en_maintenance',
                '5': 'hors_service',
                '6': 'inexistant',
                '7': 'arret_volontaire',
                '8': 'surcharge_sature',
                '9': 'nouvel_ouvrage'
            }
            
            if choix in etats:
                nouvel_etat = etats[choix]
                etats_mis_a_jour[nom] = nouvel_etat
                print(f"État de {nom} mis à jour: {nouvel_etat.replace('_', ' ').title()}")
                break
            else:
                print("❌ Option invalide. Veuillez réessayer.")
    
    return etats_mis_a_jour

def list_stations():
    """Affiche la liste de toutes les stations avec leurs informations"""
    try:
        stations = get_stations_list()
            
        if not isinstance(stations, list) or not stations:
            print("\n\033[1;31m❌ Aucune station n'a été trouvée dans la base de données.\033[0m")
            return
                
        print("\n=== LISTE DES STATIONS ===\n")
        for i, station in enumerate(stations, 1):
            print(f"{i}. {station['nom']}")
            print(f"   ID: {station['id']}")
            print(f"   Localisation: {station.get('localisation', 'Non spécifiée')}")
            print(f"   Type de procédé: {station.get('type_procede', 'Non spécifié')}")
            print(f"   Débit nominal: {station.get('debit_nominal', 'Non spécifié')} m³/j")
            print(f"   Date de création: {station.get('date_creation', 'Inconnue')}")
            print("-" * 40)
                    
    except Exception as e:
        print(f"\n\033[1;31m❌ Erreur lors de la lecture des stations: {str(e)}\033[0m")

def delete_station():
    """Supprime une station existante et ses états associés"""
    clear_screen()
    print("\033[1;34mSUPPRIMER UNE STATION\033[0m")
    print("-" * 40 + "\n")
    
    # Afficher la liste des stations
    stations = load_json("data/stations.json")
    if not stations:
        print("\033[1;33mAucune station à supprimer.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    print("\033[1mListe des stations :\033[0m\n")
    for i, station in enumerate(stations, 1):
        print(f"{i}. {station['nom']} (ID: {station['id']})")
        
    while True:
        choix = input("\nEntrez le numéro de la station à supprimer (ou Entrée pour annuler) : ").strip()
        if not choix:
            return
            
        try:
            index = int(choix) - 1
            if 0 <= index < len(stations):
                station = stations[index]
                break
            print("\033[1;31m❌ Numéro de station invalide.\033[0m")
        except ValueError:
            print("\033[1;31m❌ Veuillez entrer un numéro valide.\033[0m")
    
    # Demander confirmation
    print(f"\n\033[1;33mÊtes-vous sûr de vouloir supprimer la station suivante ?\033[0m")
    print(f"Nom: {station['nom']}")
    print(f"ID: {station['id']}")
    print(f"Type de procédé: {station.get('type_procede', 'Non spécifié')}")
    
    if input("\nConfirmez la suppression (o/n) ? ").lower() != 'o':
        input("\nSuppression annulée. Appuyez sur Entrée pour continuer...")
        return
    
    try:
        # 1. Supprimer la station de la liste des stations
        stations = [s for s in stations if s['id'] != station['id']]
        save_json("data/stations.json", stations)
        
        # 2. Supprimer les états associés dans etat_station.json
        etats_data = load_json("data/etat_station.json")
        if isinstance(etats_data, dict) and station['id'] in etats_data:
            del etats_data[station['id']]
            save_json("data/etat_station.json", etats_data)
        
        print(f"\n\033[1;32m✓ Station '{station['nom']}' et ses données associées ont été supprimées avec succès.\033[0m")
    except Exception as e:
        print(f"\n\033[1;31m❌ Erreur lors de la suppression de la station : {str(e)}\033[0m")
    
    input("\nAppuyez sur Entrée pour continuer...")

def main():
    """Fonction principale"""
    # Vérifier si le répertoire data existe, sinon le créer
    os.makedirs('data', exist_ok=True)
    
    # Vérifier si les fichiers nécessaires existent, sinon les créer
    if not os.path.exists('data/stations.json'):
        save_stations([])
    
    if not os.path.exists('data/etat_station.json'):
        with open('data/etat_station.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    
    while True:
        clear_screen()
        choix = show_menu()
        
        if choix == '1':
            create_station()
            # Mettre à jour le cache après la création d'une nouvelle station
            update_stations_cache()
        elif choix == '2':
            show_schema()
        elif choix == '3':
            update_ouvrage_state()
        elif choix == '4':
            list_stations()
            input("\nAppuyez sur Entrée pour continuer...")
        elif choix == '5':
            delete_station()
        elif choix == '6':
            print("\n" + "=" * 50)
            print("\033[1;33m👋  Merci d'avoir utilisé le gestionnaire de stations d'épuration !\033[0m")
            print("=" * 50 + "\n")
            break

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Configuration des chemins
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Désactiver les logs de débogage de matplotlib
    import matplotlib as mpl
    mpl.rcParams['figure.max_open_warning'] = 0
    
    # Lancer l'application
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[1;33m🛑 Arrêt du programme par l'utilisateur\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n\033[1;31m❌ Une erreur critique est survenue: {e}\033[0m")
        import traceback
        traceback.print_exc()
        1
