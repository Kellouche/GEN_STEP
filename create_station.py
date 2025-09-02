import json
import uuid
import os
import platform
import subprocess
from datetime import datetime, timedelta
from collections import OrderedDict

# Import des fonctions utilitaires
from utils import log_erreur, log_info, log_avertissement, formater_nom_procede
from gen_station import get_types, get_ouvrages_procede, create_initial_state

def load_json(path):
    """
    Charge les données JSON à partir d'un fichier avec gestion des erreurs.
    
    Args:
        path (str): Chemin du fichier JSON
        
    Returns:
        dict or list: Les données JSON chargées ou un dictionnaire/liste vide si le fichier n'existe pas ou est invalide
    """
    try:
        # Vérifie si le fichier existe et n'est pas vide
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return [] if "etat_station" in path or "stations" in path else OrderedDict()
            
        def object_pairs_hook(pairs):
            # Crée un OrderedDict à partir des paires clé-valeur
            return OrderedDict(pairs)
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f, object_pairs_hook=object_pairs_hook)
            
            # Si c'est une liste, on la convertit en liste d'OrderedDict
            if isinstance(data, list):
                return [OrderedDict(item) if isinstance(item, dict) else item for item in data]
            return data
            
    except json.JSONDecodeError as e:
        log_erreur(f"Erreur de décodage JSON dans {path}: {str(e)}")
        return [] if "etat_station" in path or "stations" in path else OrderedDict()
    except Exception as e:
        log_erreur(f"Erreur lors du chargement de {path}: {str(e)}")
        return [] if "etat_station" in path or "stations" in path else OrderedDict()

def save_json(path, data):
    """
    Enregistre les données dans un fichier JSON avec gestion des erreurs.
    
    Args:
        path (str): Chemin du fichier JSON
        data: Données à enregistrer (doivent être sérialisables en JSON)
    """
    try:
        # Crée le répertoire si nécessaire
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Fonction pour convertir récursivement les dictionnaires en OrderedDict
        def make_ordered(obj):
            if isinstance(obj, dict):
                return OrderedDict((k, make_ordered(v)) for k, v in obj.items())
            elif isinstance(obj, list):
                return [make_ordered(item) for item in obj]
            else:
                return obj
        
        # Convertir les données en OrderedDict
        ordered_data = make_ordered(data)
        
        # Écrire dans le fichier en préservant l'ordre des clés
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ordered_data, f, indent=2, ensure_ascii=False, sort_keys=False)
        
        return True
    except Exception as e:
        log_erreur(f"Erreur lors de l'enregistrement du fichier {path}: {str(e)}")
        return False

def get_input(prompt, allow_commands=True):
    """
    Récupère la saisie de l'utilisateur avec gestion des commandes.
    
    Args:
        prompt (str): Le message à afficher à l'utilisateur
        allow_commands (bool): Autorise les commandes spéciales (Ctrl+X, Échap)
        
    Returns:
        tuple: (input_value, command) où command peut être 'exit' ou 'modify'
    """
    import msvcrt
    import sys
    import time
    
    # Affiche le message
    clean_prompt = prompt.rstrip(' :')
    print(f"{clean_prompt} : ", end='', flush=True)
    
    user_input = []
    while True:
        try:
            char = msvcrt.getwch()
            
            # Gère la touche Entrée
            if char == '\r' or char == '\n':
                print()
                return ''.join(user_input), ""
                
            # Gère la touche Retour arrière
            elif char == '\x08':
                if user_input:
                    user_input.pop()
                    print('\b \b', end='', flush=True)
                    
            # Gère Ctrl+X (modifier)
            elif char == '\x18' and allow_commands:
                print("\n[Modification] Appuyez sur Entrée pour annuler ou tapez une nouvelle valeur")
                new_input = input("Nouvelle valeur: ").strip()
                if new_input:
                    return new_input, "modify"
                print(f"{clean_prompt} : {''.join(user_input)}", end='', flush=True)
                
            # Gère Échap (exit)
            elif char == '\x1b' and allow_commands:
                print("\n[Annulation] Opération annulée par l'utilisateur")
                return "", "exit"
                
            # Gère la saisie de caractères normaux
            elif char.isprintable():
                user_input.append(char)
                print(char, end='', flush=True)
                
        except Exception as e:
            log_erreur(f"Erreur lors de la saisie: {str(e)}")
            return "", "exit"

def get_yes_no(prompt):
    """
    Récupère une réponse oui/non de l'utilisateur.
    
    Args:
        prompt (str): Le message à afficher
        
    Returns:
        bool or None: True pour 'o', False pour 'n', None pour annulation
    """
    while True:
        response, cmd = get_input(f"{prompt} (o/n)")
        
        if cmd == 'exit':
            return None
            
        response = response.lower().strip()
        
        if response == 'o':
            return True
        elif response == 'n':
            return False
            
        print("Veuillez répondre par 'o' pour oui ou 'n' pour non.")

def customiser_ouvrages(etats_ouvrages, type_procede=None):
    """
    Permet à l'utilisateur de personnaliser les paramètres d'ouvrage.
    
    Args:
        etats_ouvrages (dict): Dictionnaire des états des ouvrages à personnaliser
        type_procede (str, optional): Type de procédé pour ordonner les ouvrages
        
    Returns:
        dict: Dictionnaire des états mis à jour
    """
    if not etats_ouvrages or not isinstance(etats_ouvrages, dict):
        return etats_ouvrages
        
    print("\nPersonnalisation des ouvrages:")
    print("Entrez le numéro correspondant à l'état souhaité pour chaque ouvrage")
    
    # Si etats_ouvrages est déjà un dictionnaire d'états, on le copie
    # Sinon, on suppose que c'est une liste de noms d'ouvrages et on crée un état par défaut
    if not all(isinstance(v, str) for v in etats_ouvrages.values()):
        noms_ouvrages = etats_ouvrages  # C'est une liste de noms
        etats_ouvrages = {nom: 'en_service' for nom in noms_ouvrages}
    
    # Obtenir la liste ordonnée des ouvrages si le type de procédé est fourni
    if type_procede:
        from main import get_ouvrages_procede as main_get_ouvrages_procede
        ouvrages_ordre = main_get_ouvrages_procede(type_procede)
        if ouvrages_ordre:
            # Créer une liste ordonnée des ouvrages existants dans etat_ouvrages
            ouvrages_a_afficher = []
            # D'abord ajouter les ouvrages dans l'ordre du procédé
            for ouvrage in ouvrages_ordre:
                if ouvrage in etats_ouvrages:
                    ouvrages_a_afficher.append(ouvrage)
            # Puis ajouter les ouvrages restants qui ne sont pas dans l'ordre du procédé
            for ouvrage in etats_ouvrages:
                if ouvrage not in ouvrages_a_afficher:
                    ouvrages_a_afficher.append(ouvrage)
        else:
            # Si on ne peut pas obtenir l'ordre, on utilise l'ordre des clés
            ouvrages_a_afficher = list(etats_ouvrages.keys())
    else:
        # Si pas de type de procédé, on utilise l'ordre des clés
        ouvrages_a_afficher = list(etats_ouvrages.keys())
    
    for i, nom in enumerate(ouvrages_a_afficher, 1):
        etat = etats_ouvrages[nom]
        print(f"\n\033[1m--- Ouvrage {i}: {nom} (État actuel: {etat}) ---\033[0m")
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
            choix = input("\nVotre choix (1-10): ").strip()
            if not choix:  # Si l'utilisateur appuie juste sur Entrée
                print("Veuillez sélectionner une option valide.")
                continue
                
            if choix == '10':
                break  # Passer à l'ouvrage suivant
                
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
                etats_ouvrages[nom] = nouvel_etat
                print(f"État de {nom} mis à jour: {nouvel_etat.replace('_', ' ').title()}")
                break
            else:
                print("❌ Option invalide. Veuillez réessayer.")
    
    return etats_ouvrages

def clear_screen():
    """Efface l'écran de la console de manière multi-plateforme."""
    if platform.system() == 'Windows':
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        os.system('clear')

def creation_type_procede_section(types_dict):
    """
    Affiche les types de procédés disponibles et récupère la sélection de l'utilisateur.
    
    Args:
        types_dict (dict): Dictionnaire de types de procédés avec configurations
        
    Returns:
        str or None: Clé du type de procédé sélectionné ou None si annulation
    """
    if not types_dict:
        log_erreur("Aucun type de procédé disponible. Vérifiez le fichier types.json")
        return None
    
    print("\nTypes de procédé disponibles :")
    
    # Crée une liste de types de procédés pour la sélection
    procedure_list = list(types_dict.items())
    
    # Affiche les procédés disponibles avec noms formatés
    for i, (key, proc_data) in enumerate(procedure_list, 1):
        display_name = proc_data.get('display_name', formater_nom_procede(key))
        print(f"{i}. {display_name.upper()}")
    
    while True:
        choice, cmd = get_input("\nChoisissez un type de procédé (numéro)")
        
        if cmd == 'exit':
            return None
            
        if not choice.isdigit() or not (1 <= int(choice) <= len(procedure_list)):
            log_avertissement(f"Choix invalide. Veuillez entrer un numéro entre 1 et {len(procedure_list)}.")
            continue
            
        # Retourne la clé du type de procédé d'origine
        return procedure_list[int(choice) - 1][0]

def valider_texte(texte, champ):
    """
    Valide que le texte ne commence pas par un chiffre et n'est pas vide
    
    Args:
        texte (str): Le texte à valider
        champ (str): Le nom du champ pour le message d'erreur
        
    Returns:
        tuple: (bool, str) (est_valide, message_erreur)
    """
    if not texte or not texte.strip():
        return False, f"Le champ {champ} ne peut pas être vide."
    if texte[0].isdigit():
        return False, f"Le {champ} ne peut pas commencer par un chiffre."
    return True, ""

def get_input_valide(prompt, champ, allow_commands=True):
    """
    Demande une saisie à l'utilisateur avec validation
    """
    while True:
        valeur, cmd = get_input(prompt, allow_commands)
        if cmd == 'exit':
            return None, 'exit'
            
        est_valide, message = valider_texte(valeur, champ)
        if est_valide:
            return valeur, cmd
        else:
            print(f"❌ {message} Veuillez réessayer.")

def create_station():
    """
    Fonction principale pour créer une nouvelle station de traitement d'eau.
    
    Returns:
        str or None: ID de la station créée ou None si la création a échoué
    """
    data = {}
    
    try:
        # Affiche l'en-tête
        print("\n" + "="*50)
        print("  CRÉATION D'UNE NOUVELLE STATION")
        print("  " + "-"*46)
        print("  Commandes rapides :")
        print("  - Ctrl+X : Modifier la valeur actuelle")
        print("  - Échap  : Annuler et quitter")
        print("  - Entrée : Valider la saisie")
        print("="*50 + "\n")
        
        # 1. Récupère le nom de la station
        while True:
            nom, cmd = get_input_valide("Nom de la station", "nom de la station")
            if cmd == 'exit':
                return None
            if nom:
                data['nom'] = nom.strip()
                break
        
        # 2. Récupère la localisation de la station
        localisation, cmd = get_input_valide("Localisation (ville)", "lieu de localisation")
        if cmd == 'exit':
            return None
        data['localisation'] = localisation.strip()
        
        # 3. Récupère le débit nominal
        while True:
            debit_str, cmd = get_input("Débit nominal (m³/j)")
            if cmd == 'exit':
                return None
            if cmd == 'modify':
                continue
                
            try:
                debit = float(debit_str)
                if debit > 0:
                    data['debit_nominal'] = debit
                    break
                else:
                    print("❌ Le débit doit être un nombre positif.")
            except ValueError:
                print("❌ Veuillez entrer un nombre valide pour le débit.")
        
        # 4. Récupère le type de procédé
        types_dict = get_types()
        if not types_dict:
            log_erreur("Impossible de charger les types de procédés. Vérifiez le fichier types.json")
            return None
        
        procedure_type = creation_type_procede_section(types_dict)
        if procedure_type is None:
            return None
            
        data['type_procede'] = procedure_type
        
        # 5. Récupère la destination
        print("\nDestinations possibles :")
        destinations = ["Milieu naturel", "Irrigation agricole", "Irrigation des espaces verts", "Industrie", "Autre"]
        for i, dest in enumerate(destinations, 1):
            print(f"{i}. {dest}")
            
        while True:
            choix, cmd = get_input("\nChoisissez une destination (numéro)")
            if cmd == 'exit':
                return None
                
            if choix.isdigit() and 1 <= int(choix) <= len(destinations):
                data['destination'] = destinations[int(choix)-1]
                break
                
            log_avertissement(f"Veuillez entrer un nombre entre 1 et {len(destinations)}")
        
        # 6. Récupère la liste d'ouvrages avec leurs états initiaux
        etat_initial = get_ouvrages_procede(data['type_procede'], types_dict)
        if not etat_initial:
            log_erreur("Aucun ouvrage trouvé pour ce type de procédé.")
            return None
        
        # 7. Personnalise les ouvrages si nécessaire
        if get_yes_no("Voulez-vous personnaliser les ouvrages ?"):
            etat_initial = customiser_ouvrages(etat_initial, data['type_procede'])
            if etat_initial is None:  # User cancelled
                return None
        
        # 8. Génère un ID unique
        station_id = str(uuid.uuid4())
        
        # 9. Prépare les données de la station (sans la clé ouvrages)
        station_data = {
            'id': station_id,
            'nom': data['nom'],
            'localisation': data['localisation'],
            'debit_nominal': data['debit_nominal'],
            'type_procede': data['type_procede'],
            'destination': data['destination'],
            'date_creation': datetime.now().strftime("%Y-%m-%d")
        }
        
        # 10. Prépare les données de l'état initial
        print("\nOrdre des ouvrages avant enregistrement:")
        for i, (ouvrage, etat) in enumerate(etat_initial.items(), 1):
            print(f"{i}. {ouvrage}: {etat}")
            
        etat_data = {
            'station_id': station_id,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'etat_ouvrages': etat_initial,  # Déjà un OrderedDict
        }
        
        # 11. Enregistre les données
        try:
            # Enregistre la station
            stations = load_json("data/stations.json")
            if not isinstance(stations, list):
                stations = []
            stations.append(station_data)
            save_json("data/stations.json", stations)
            
            # Enregistre l'état initial
            etats_data = load_json("data/etat_station.json")
            if not isinstance(etats_data, dict):
                etats_data = OrderedDict()
            
            # Créer une nouvelle entrée avec l'ID de la station comme clé
            etats_data[station_id] = [etat_data]
            
            # Afficher l'ordre avant sauvegarde
            print("\nOrdre des ouvrages avant sauvegarde dans le fichier:")
            for i, (ouvrage, etat) in enumerate(etat_data['etat_ouvrages'].items(), 1):
                print(f"{i}. {ouvrage}: {etat}")
            
            save_json("data/etat_station.json", etats_data)
            
            # Vérifier l'ordre après chargement
            etats_verifies = load_json("data/etat_station.json")
            if station_id in etats_verifies and etats_verifies[station_id]:
                print("\nOrdre des ouvrages après chargement du fichier:")
                for i, (ouvrage, etat) in enumerate(etats_verifies[station_id][0]['etat_ouvrages'].items(), 1):
                    print(f"{i}. {ouvrage}: {etat}")
            
            log_info(f"Station '{data['nom']}' créée avec succès!")
            log_info(f"ID de la station: {station_id}")
            
            print(f"\n✅ Station '{data['nom']}' créée avec succès!")
            print(f"ID de la station: {station_id}")
            
            return station_id
            
        except Exception as e:
            log_erreur(f"Erreur lors de la sauvegarde des données: {str(e)}", exc_info=True)
            print("❌ Une erreur est survenue lors de la sauvegarde des données. Voir les logs pour plus de détails.")
            return None
            
    except KeyboardInterrupt:
        print("\nOpération annulée par l'utilisateur.")
        return None
    except Exception as e:
        log_erreur(f"Erreur inattendue lors de la création de la station: {str(e)}", exc_info=True)
        print("❌ Une erreur inattendue est survenue. Voir les logs pour plus de détails.")
        return None

def create_initial_state(ouvrages):
    """
    Crée un état initial pour les ouvrages de la station.
    
    Args:
        ouvrages: Liste des ouvrages du procédé
        
    Returns:
        dict: Dictionnaire des états initiaux des ouvrages
    """
    etat_initial = {}
    
    # Par défaut, tous les ouvrages sont en service
    for ouvrage in ouvrages:
        if isinstance(ouvrage, dict) and 'nom' in ouvrage:
            etat_initial[ouvrage['nom']] = 'en_service'
        elif isinstance(ouvrage, str):
            etat_initial[ouvrage] = 'en_service'
    
    return etat_initial

# Ce module est conçu pour être importé et utilisé par main.py
