#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
import logging

# Importer les utilitaires
from utils import get_stations_list, save_stations, update_stations_cache, get_station_by_id

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
    print("=" * 50)
    print("GESTION DES STATIONS D'ÉPURATION")
    print("=" * 50)

def show_menu():
    """Affiche le menu principal avec des icônes"""
    print("\n🔹 1. ➕ Créer une nouvelle station")
    print("🔹 2. 📊 Afficher le schéma d'une station")
    print("🔹 3. 🔄 Mettre à jour l'état des ouvrages")
    print("🔹 4. 📋 Lister toutes les stations")
    print("🔹 5. 🗑️  Supprimer une station")
    print("🔹 6. ❌ Quitter")
    
    while True:
        try:
            choix = input("\n🛠️  Votre choix (1-6): ").strip()
            if choix in ['1', '2', '3', '4', '5', '6']:
                return choix
            print("❌ Erreur: Veuillez entrer un nombre entre 1 et 6.")
        except KeyboardInterrupt:
            print("\n\n⚠️  Opération annulée par l'utilisateur.")
            return '6'  # Quitter en cas de Ctrl+C

def select_station():
    """Permet à l'utilisateur de sélectionner une station"""
    clear_screen()
    print("\n📋 SELECTION D'UNE STATION")
    print("-" * 40 + "\n")
    
    try:
        stations = get_stations_list()
        
        if not isinstance(stations, list) or not stations:
            print("❌ Aucune station n'a été trouvée dans la base de données.")
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
                print(f"❌ Veuillez entrer un nombre entre 1 et {len(stations)}")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide.")
                
    except Exception as e:
        log.error(f"Erreur lors de la sélection de la station: {e}")
        return None

def show_schema():
    """Affiche le schéma d'une station sélectionnée"""
    while True:  # Boucle pour permettre à l'utilisateur de voir plusieurs schémas s'il le souhaite
        clear_screen()
        print("📊 AFFICHAGE DU SCHEMA")
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
            print("\nOpération annulée par l'utilisateur.")
            break
        except Exception as e:
            print(f"\n❌ Erreur lors de la génération du schéma: {str(e)}")
            import traceback
            traceback.print_exc()
            input("\nAppuyez sur Entrée pour continuer...")
            break

def update_ouvrage_state():
    """Met à jour l'état des ouvrages d'une station"""
    clear_screen()
    print("🔄 MISE À JOUR DE L'ÉTAT DES OUVRAGES")
    print("-" * 40 + "\n")
    
    # Sélectionner une station
    station = select_station()
    if not station:
        return
        
    clear_screen()
    print(f"🔄 MISE À JOUR DE L'ÉTAT DES OUVRAGES - {station['nom'].upper()}")
    print("-" * 40 + "\n")
    
    # Charger les états actuels
    try:
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        etats = []
    
    # Trouver les états existants pour cette station
    etats_station = [e for e in etats if e.get('station_id') == station['id']]
    
    # Si des états existent, proposer de les afficher
    if etats_station:
        print("Mises à jour existantes pour cette station :\n")
        for i, etat in enumerate(etats_station, 1):
            print(f"{i}. {etat.get('date_maj', 'Date inconnue')}")
        
        print("\nQue souhaitez-vous faire ?")
        print("1. Créer une nouvelle mise à jour")
        print("2. Modifier une mise à jour existante")
        print("3. Annuler")
        
        while True:
            choix = input("\nVotre choix (1-3): ").strip()
            if choix == '1':
                break  # Créer une nouvelle mise à jour
            elif choix == '2':
                # Modifier une mise à jour existante
                try:
                    idx = int(input("\nNuméro de la mise à jour à modifier: ").strip()) - 1
                    if 0 <= idx < len(etats_station):
                        etat = etats_station[idx]
                        break
                    else:
                        print("❌ Numéro invalide.")
                except ValueError:
                    print("❌ Veuillez entrer un numéro valide.")
            elif choix == '3':
                return  # Annuler
            else:
                print("❌ Veuillez entrer un nombre entre 1 et 3.")
    
    # Si on arrive ici, soit on crée une nouvelle mise à jour, soit on en modifie une existante
    if 'etat' not in locals():
        # Créer une nouvelle mise à jour
        etat = {
            'station_id': station['id'],
            'station_nom': station['nom'],
            'date_maj': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'etat_ouvrages': {}
        }
    
    # Afficher les ouvrages de la station et leur état actuel
    print(f"\nÉtat actuel des ouvrages de la station {station['nom']}:")
    
    # Récupérer la liste des ouvrages du procédé de la station
    try:
        ouvrages = get_ouvrages_procede(station['type_procede'])
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des ouvrages: {e}")
        input("\nAppuyez sur Entrée pour continuer...")
        return
    
    # Afficher et mettre à jour chaque ouvrage
    for i, (ouvrage_id, ouvrage) in enumerate(ouvrages.items(), 1):
        print(f"\n{i}. {ouvrage['nom']}")
        print(f"   Description: {ouvrage.get('description', 'Aucune description')}")
        
        # Afficher l'état actuel
        etat_actuel = etat['etat_ouvrages'].get(ouvrage_id, 'Fonctionnel')
        print(f"   État actuel: {etat_actuel}")
        
        # Proposer de changer l'état
        print("   Options d'état disponibles:")
        print("   1. Fonctionnel")
        print("   2. En maintenance")
        print("   3. Hors service")
        print("   4. Ne pas modifier")
        
        while True:
            choix_etat = input("   Votre choix (1-4): ").strip()
            if choix_etat == '1':
                etat['etat_ouvrages'][ouvrage_id] = 'Fonctionnel'
                break
            elif choix_etat == '2':
                etat['etat_ouvrages'][ouvrage_id] = 'En maintenance'
                break
            elif choix_etat == '3':
                etat['etat_ouvrages'][ouvrage_id] = 'Hors service'
                break
            elif choix_etat == '4':
                break
            else:
                print("   ❌ Veuillez entrer un nombre entre 1 et 4.")
    
    # Si c'est une nouvelle mise à jour, l'ajouter à la liste
    if etat not in etats:
        etats.append(etat)
    
    # Sauvegarder les modifications
    try:
        with open('data/etat_station.json', 'w', encoding='utf-8') as f:
            json.dump(etats, f, ensure_ascii=False, indent=2)
        print("\n✅ État des ouvrages mis à jour avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de la sauvegarde: {e}")
    
    input("\nAppuyez sur Entrée pour continuer...")

def list_stations():
    """Affiche la liste de toutes les stations avec leurs informations"""
    try:
        stations = get_stations_list()
            
        if not isinstance(stations, list) or not stations:
            print("\n❌ Aucune station n'a été trouvée dans la base de données.")
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
        print(f"\n❌ Erreur lors de la lecture des stations: {str(e)}")

def delete_station():
    """Supprime une station existante"""
    clear_screen()
    print("🗑️  SUPPRIMER UNE STATION")
    print("-" * 40 + "\n")
    
    # Afficher la liste des stations
    try:
        stations = get_stations_list()
        
        if not stations:
            print("❌ Aucune station n'a été trouvée dans la base de données.")
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
                print(f"❌ Veuillez entrer un nombre entre 1 et {len(stations)}")
            except ValueError:
                print("❌ Veuillez entrer un numéro valide.")
        
        # Demander confirmation
        print(f"\nÊtes-vous sûr de vouloir supprimer la station suivante ?")
        print(f"Nom: {station['nom']}")
        print(f"ID: {station['id']}")
        print(f"Type de procédé: {station.get('type_procede', 'Non spécifié')}")
        
        confirm = input("\nCette action est irréversible. Confirmer la suppression (o/n) ? ").strip().lower()
        if confirm != 'o':
            print("\nSuppression annulée.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        # Supprimer la station
        stations = [s for s in stations if s['id'] != station['id']]
        
        # Sauvegarder les modifications
        save_stations(stations)
        
        print(f"\n✅ La station {station['nom']} a été supprimée avec succès !")
        input("\nAppuyez sur Entrée pour continuer...")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la suppression de la station: {str(e)}")
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
            json.dump([], f, ensure_ascii=False, indent=2)
    
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
            print("👋  Merci d'avoir utilisé le gestionnaire de stations d'épuration !")
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
        print("\n\n🛑 Arrêt du programme par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Une erreur critique est survenue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
