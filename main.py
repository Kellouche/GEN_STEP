#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
import logging
import time

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
    clear_screen()
    print("\033[1;34mMISE À JOUR DE L'ÉTAT DES OUVRAGES\033[0m")
    print("-" * 40 + "\n")

    station = select_station()
    if not station:
        return

    station_id = station.get('id')
    if not station_id:
        print("\033[1;31m❌ ID de station manquant. Opération annulée.\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
        return

    clear_screen()
    print(f"\033[1;34mMISE À JOUR DE L'ÉTAT DES OUVRAGES - {station.get('nom', 'N/A').upper()}\033[0m")
    print("-" * 40 + "\n")

    # Charger les états existants
    etats_actuels = charger_etats_station()
    etats_station = etats_actuels.get(station_id, [])

    # S'assurer que c'est toujours une liste
    if isinstance(etats_station, dict):
        etats_station = [etats_station]

    # Récupérer le dernier état des ouvrages s'il existe
    dernier_etat_ouvrages = {}
    if etats_station:
        etats_station.sort(key=lambda x: x.get('date_maj', ''), reverse=True)
        dernier_etat_ouvrages = etats_station[0].get('etat_ouvrages', {})

    # Fusionner avec les ouvrages du type de procédé pour n'afficher que les ouvrages pertinents
    ouvrages_procede = get_ouvrages_procede(station.get('type_procede'))
    if ouvrages_procede is None:
        return

    # Mettre à jour les états des ouvrages du procédé avec les derniers états connus
    for ouvrage in ouvrages_procede:
        if ouvrage in dernier_etat_ouvrages:
            ouvrages_procede[ouvrage] = dernier_etat_ouvrages[ouvrage]

    etat_ouvrages = ouvrages_procede

    while True:
        clear_screen()
        print(f"\033[1;34mMISE À JOUR POUR: {station.get('nom')}\033[0m")
        print("\033[2m(Tapez 'q' pour terminer la mise à jour)\033[0m\n")

        # Afficher l'état actuel des ouvrages
        for i, (ouvrage, etat) in enumerate(etat_ouvrages.items(), 1):
            etat_formate = etat.replace('_', ' ').capitalize()
            print(f"{i}. {ouvrage}: \033[1m{etat_formate}\033[0m")

        choix_ouvrage = input("\nEntrez le numéro de l'ouvrage à modifier (ou 'q') : ").strip()
        if choix_ouvrage.lower() == 'q':
            break

        try:
            choix_ouvrage_idx = int(choix_ouvrage) - 1
            if not (0 <= choix_ouvrage_idx < len(etat_ouvrages)):
                print("\033[1;31mNuméro d'ouvrage invalide.\033[0m")
                time.sleep(1)
                continue
            
            nom_ouvrage = list(etat_ouvrages.keys())[choix_ouvrage_idx]

            # Afficher le menu de sélection de l'état
            etat_selectionne = select_etat_interactive()
            if etat_selectionne is None:
                continue

            etat_ouvrages[nom_ouvrage] = etat_selectionne

        except ValueError:
            print("\033[1;31mVeuillez entrer un numéro valide.\033[0m")
            time.sleep(1)

    # Créer le nouvel enregistrement d'état
    etat = {
        'station_id': station_id,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'etat_ouvrages': etat_ouvrages,
        'date_maj': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    etats_station.append(etat)
    etats_actuels[station_id] = etats_station

    sauvegarder_etats_station(etats_actuels)
    print("\n\033[1;32m✅ État de la station mis à jour avec succès !\033[0m")
    time.sleep(2)

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
    """Récupère la liste des ouvrages pour un type de procédé donné."""
    try:
        with open('data/types.json', 'r', encoding='utf-8') as f:
            types_data = json.load(f)

        procede_info = types_data.get(type_procede)
        if not procede_info:
            print(f"\033[1;31m❌ Type de procédé '{type_procede}' non trouvé.\033[0m")
            time.sleep(2)
            return None

        ouvrages = set()

        # Extraction des ouvrages de la filière eau
        if 'filiere_eau' in procede_info:
            for etape, details in procede_info['filiere_eau'].items():
                if isinstance(details, list):
                    ouvrages.update(details)

        # Extraction des ouvrages de la filière boue
        if 'filiere_boue' in procede_info and isinstance(procede_info['filiere_boue'], list):
            ouvrages.update(procede_info['filiere_boue'])

        # Extraction du traitement tertiaire (si défini à la racine)
        if 'traitement_tertiaire' in procede_info and isinstance(procede_info['traitement_tertiaire'], list):
            ouvrages.update(procede_info['traitement_tertiaire'])

        if not ouvrages:
            print(f"\033[1;31m❌ Aucun ouvrage trouvé pour le type de procédé '{type_procede}'.\033[0m")
            time.sleep(2)
            return None

        # Retourner un dictionnaire avec l'état par défaut 'en_service'
        return {ouvrage: 'en_service' for ouvrage in sorted(list(ouvrages))}

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"\033[1;31m❌ Erreur lors de la lecture du fichier 'types.json': {e}\033[0m")
        time.sleep(2)
        return None

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
    """Supprime une station existante"""
    clear_screen()
    print("\033[1;34mSUPPRIMER UNE STATION\033[0m")
    print("-" * 40 + "\n")
    
    # Afficher la liste des stations
    try:
        stations = get_stations_list()
        
        if not stations:
            print("\033[1;31m❌ Aucune station n'a été trouvée dans la base de données.\033[0m")
            input("\nAppuyez sur Entrée pour continuer...")
            return
            
        print("Liste des stations disponibles :\n")
        for i, station in enumerate(stations, 1):
            print(f"{i}. {station['nom']} (ID: {station['id']})")
            
        while True:
            choix = input("\nEntrez le numéro de la station à supprimer (ou Entrée pour annuler) : ").strip()
            if not choix:
                return
                
            try:
                choix = int(choix) - 1
                if 0 <= choix < len(stations):
                    station = stations[choix]
                    break
                print(f"\033[1;31m❌ Veuillez entrer un nombre entre 1 et {len(stations)}\033[0m")
            except ValueError:
                print("\033[1;31m❌ Veuillez entrer un numéro valide.\033[0m")
        
        # Demander confirmation
        print(f"\n\033[1;33mÊtes-vous sûr de vouloir supprimer la station suivante ?\033[0m")
        print(f"Nom: {station['nom']}")
        print(f"ID: {station['id']}")
        print(f"Type de procédé: {station.get('type_procede', 'Non spécifié')}")
        
        confirm = input("\nCette action est irréversible. Confirmer la suppression (o/n) ? ").strip().lower()
        if confirm != 'o':
            print("\n\033[1;33mSuppression annulée.\033[0m")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        # Supprimer la station
        stations = [s for s in stations if s['id'] != station['id']]
        
        # Sauvegarder les modifications
        save_stations(stations)
        
        print(f"\n\033[1;32m✅ La station {station['nom']} a été supprimée avec succès !\033[0m")
        input("\nAppuyez sur Entrée pour continuer...")
            
    except Exception as e:
        print(f"\n\033[1;31m❌ Erreur lors de la suppression de la station: {str(e)}\033[0m")
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
        sys.exit(1)
