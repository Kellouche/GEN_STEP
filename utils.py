import logging
import os
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
from collections import OrderedDict
import shutil
import time
import unicodedata

def configurer_journal():
    """Configure le système de journalisation"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Format des logs
    format_log = '%(asctime)s - %(levelname)s - %(message)s'
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Configuration du fichier de log
    logging.basicConfig(
        level=logging.INFO,
        format=format_log,
        handlers=[
            logging.FileHandler(f'logs/app_{date_str}.log'),
            logging.StreamHandler()
        ]
    )

def log_erreur(message, exc_info=False):
    """Journalise un message d'erreur"""
    logging.error(message, exc_info=exc_info)

def log_info(message):
    """Journalise un message d'information"""
    logging.info(message)

def log_avertissement(message):
    """Journalise un avertissement"""
    logging.warning(message)

def formater_nom_procede(nom):
    """
    Formate un nom de procédé pour l'affichage en majuscules
    Exemple: 'boues_actives' -> 'BOUES ACTIVEES'
    """
    if not nom:
        return ""
    # Remplacer les underscores par des espaces et mettre en majuscules
    return ' '.join(word.upper() for word in nom.split('_'))

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Variables globales pour le cache des stations
_STATIONS_CACHE = None
_STATIONS_LAST_MODIFIED = 0

def get_stations_list(force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Récupère la liste des stations disponibles avec mise en cache.
    
    Args:
        force_reload: Si True, force le rechargement du fichier
        
    Returns:
        Liste des stations avec leurs informations
    """
    global _STATIONS_CACHE, _STATIONS_LAST_MODIFIED
    
    try:
        file_path = 'data/stations.json'
        
        # Si le fichier n'existe pas, retourner une liste vide
        if not os.path.exists(file_path):
            os.makedirs('data', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
            
        current_mtime = os.path.getmtime(file_path)
        
        # Si le fichier n'a pas été modifié et qu'on a un cache valide
        if not force_reload and _STATIONS_CACHE is not None and current_mtime <= _STATIONS_LAST_MODIFIED:
            return _STATIONS_CACHE
            
        # Sinon, on charge le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            _STATIONS_CACHE = json.load(f)
            _STATIONS_LAST_MODIFIED = current_mtime
            
        # S'assurer que le cache est une liste
        if not isinstance(_STATIONS_CACHE, list):
            log.warning("Le fichier stations.json ne contient pas une liste. Réinitialisation.")
            _STATIONS_CACHE = []
            save_stations(_STATIONS_CACHE)
            
        return _STATIONS_CACHE
        
    except json.JSONDecodeError as e:
        log.error(f"Erreur de décodage JSON dans stations.json: {e}")
        return []
    except Exception as e:
        log.error(f"Erreur lors de la lecture du fichier stations.json: {e}")
        return []

def save_stations(stations: List[Dict[str, Any]]) -> bool:
    """
    Sauvegarde la liste des stations dans le fichier et met à jour le cache.
    
    Args:
        stations: Liste des stations à sauvegarder
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    global _STATIONS_CACHE, _STATIONS_LAST_MODIFIED
    
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/stations.json', 'w', encoding='utf-8') as f:
            json.dump(stations, f, ensure_ascii=False, indent=2)
        
        # Mettre à jour le cache
        _STATIONS_CACHE = stations
        _STATIONS_LAST_MODIFIED = os.path.getmtime('data/stations.json')
        
        return True
    except Exception as e:
        log.error(f"Erreur lors de la sauvegarde des stations: {e}")
        return False

def update_stations_cache() -> None:
    """
    Force la mise à jour du cache des stations en rechargeant le fichier.
    """
    global _STATIONS_CACHE, _STATIONS_LAST_MODIFIED
    _STATIONS_CACHE = None
    _STATIONS_LAST_MODIFIED = 0
    get_stations_list(force_reload=True)

def get_station_by_id(station_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère une station par son ID en utilisant le cache.
    
    Args:
        station_id: ID de la station à récupérer
        
    Returns:
        La station correspondante ou None si non trouvée
    """
    stations = get_stations_list()
    for station in stations:
        if station.get('id') == station_id:
            return station
    return None

def charger_etats_station() -> Dict[str, Any]:
    """
    Charge l'état des stations depuis le fichier JSON.
    Gère plusieurs formats de données pour assurer la rétrocompatibilité.
    """
    try:
        if not os.path.exists('data/etat_station.json'):
            return {}
            
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats_data = json.load(f)
            
        # Si le fichier est vide ou pas un dictionnaire
        if not isinstance(etats_data, dict):
            log.warning("Le fichier etat_station.json ne contient pas un objet JSON valide")
            return {}
            
        result = {}
        
        for station_id, data in etats_data.items():
            if not data:
                continue
                
            # Cas 1: Données dans une liste (format attendu)
            if isinstance(data, list):
                etats_list = []
                for item in data:
                    # Si l'item est un dictionnaire avec une liste d'états
                    if isinstance(item, dict) and station_id in item and isinstance(item[station_id], list):
                        etats_list.extend(item[station_id])
                    # Si l'item est directement un état
                    elif isinstance(item, dict):
                        etats_list.append(item)
                
                if etats_list:
                    result[station_id] = etats_list
            # Cas 2: Données directes (ancien format)
            elif isinstance(data, dict):
                # Si c'est un état direct
                if 'etat_ouvrages' in data or 'date' in data or 'date_maj' in data:
                    result[station_id] = [data]
        
        # Nettoyer les données chargées
        for station_id, etats in result.items():
            for i, etat in enumerate(etats):
                if not isinstance(etat, dict):
                    continue
                    
                # S'assurer que chaque état a un champ etat_ouvrages
                if 'etat_ouvrages' not in etat:
                    etat['etat_ouvrages'] = {}
                # S'assurer que etat_ouvrages est un dictionnaire
                elif not isinstance(etat['etat_ouvrages'], dict):
                    try:
                        etat['etat_ouvrages'] = dict(etat['etat_ouvrages'])
                    except (TypeError, ValueError):
                        etat['etat_ouvrages'] = {}
                
                # S'assurer que l'ID de station est présent
                if 'station_id' not in etat:
                    etat['station_id'] = station_id
                
                # S'assurer que la date de mise à jour existe
                if 'date_maj' not in etat:
                    etat['date_maj'] = etat.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return result
        
    except json.JSONDecodeError as e:
        log_erreur(f"Erreur de décodage JSON dans etat_station.json: {e}")
        return {}
    except Exception as e:
        log_erreur(f"Erreur lors du chargement de etat_station.json: {e}")
        return {}

def sauvegarder_etats_station(etats_station, station_id):
    """
    Sauvegarde les états d'une station dans le fichier etat_station.json
    
    Args:
        etats_station (list): Liste des états de la station à sauvegarder
        station_id (str): ID de la station
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Vérifier que l'ID de station est valide
        if not station_id:
            log_erreur("ID de station manquant pour la sauvegarde")
            return False
            
        # Vérifier et corriger la structure des données
        if not isinstance(etats_station, list):
            log.warning("Les états de la station ne sont pas une liste, conversion en cours...")
            etats_station = [etats_station] if etats_station else []
        
        # Nettoyer et valider chaque état
        etats_a_sauvegarder = []
        for etat in etats_station:
            if not isinstance(etat, dict):
                log.warning(f"État invalide ignoré: {etat}")
                continue
                
            # Créer une copie pour éviter de modifier l'original
            etat_propre = {}
            
            # Copier uniquement les champs nécessaires
            for champ in ['station_id', 'date', 'date_maj', 'etat_ouvrages']:
                if champ in etat:
                    etat_propre[champ] = etat[champ]
            
            # S'assurer que chaque état a un champ etat_ouvrages
            if 'etat_ouvrages' not in etat_propre or not etat_propre['etat_ouvrages']:
                # Si etat_ouvrages est vide ou n'existe pas, initialiser avec les ouvrages par défaut
                station = get_station_by_id(station_id)
                if station and 'type_procede' in station:
                    ouvrages_par_defaut = get_ouvrages_procede(station['type_procede'])
                    if ouvrages_par_defaut:
                        # Créer une copie profonde des ouvrages par défaut
                        nouveaux_ouvrages = ouvrages_par_defaut.copy()
                        
                        # Conserver les états existants pour les ouvrages déjà présents
                        if 'etat_ouvrages' in etat and isinstance(etat['etat_ouvrages'], dict):
                            for ouvrage, etat_ouvrage in etat['etat_ouvrages'].items():
                                if ouvrage in nouveaux_ouvrages:
                                    nouveaux_ouvrages[ouvrage] = etat_ouvrage
                        
                        etat_propre['etat_ouvrages'] = nouveaux_ouvrages
                    else:
                        etat_propre['etat_ouvrages'] = {}
                else:
                    etat_propre['etat_ouvrages'] = {}
            
            # S'assurer que l'ID de station est présent
            if 'station_id' not in etat_propre:
                etat_propre['station_id'] = station_id
            
            # S'assurer que la date de mise à jour existe
            if 'date_maj' not in etat_propre:
                etat_propre['date_maj'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Supprimer la date simple si elle existe encore
            if 'date' in etat_propre:
                del etat_propre['date']
            
            etats_a_sauvegarder.append(etat_propre)
        
        # Charger les états existants
        etats_data = charger_etats_station()
        if not isinstance(etats_data, dict):
            etats_data = {}
        
        # S'assurer que etats_a_sauvegarder est une liste
        if not isinstance(etats_a_sauvegarder, list):
            etats_a_sauvegarder = [etats_a_sauvegarder] if etats_a_sauvegarder else []
        
        # Vérifier et nettoyer chaque état avant de le sauvegarder
        etats_propres = []
        for etat in etats_a_sauvegarder:
            if not isinstance(etat, dict):
                continue
                
            # Créer une copie propre de l'état
            etat_propre = {
                'station_id': str(etat.get('station_id', station_id)),
                'date_maj': etat.get('date_maj', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'etat_ouvrages': {}
            }
            
            # Copier les états des ouvrages existants
            if 'etat_ouvrages' in etat and isinstance(etat['etat_ouvrages'], dict):
                # Créer une copie profonde du dictionnaire des états
                for k, v in etat['etat_ouvrages'].items():
                    if isinstance(k, str) and isinstance(v, str):
                        etat_propre['etat_ouvrages'][k] = v
            
            # S'assurer que tous les champs sont des chaînes de caractères
            for key, value in etat_propre.items():
                if isinstance(value, (int, float, bool)):
                    etat_propre[key] = str(value)
            
            etats_propres.append(etat_propre)
        
        # Mettre à jour les états pour cette station
        etats_data[str(station_id)] = etats_propres
        
        # Créer le répertoire de données s'il n'existe pas
        os.makedirs('data', exist_ok=True)
        
        # Créer un fichier temporaire avec un nom unique
        temp_file = os.path.join('data', f'etat_station_{os.getpid()}_{int(time.time())}.tmp')
        
        try:
            # Écrire dans le fichier temporaire
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(etats_data, f, ensure_ascii=False, indent=2, default=str)
            
            # Vérifier que le fichier temporaire a été correctement écrit
            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                raise IOError("Le fichier temporaire n'a pas été correctement écrit")
            
            # Chemin du fichier de destination
            etat_file = os.path.join('data', 'etat_station.json')
            
            # Remplacer l'ancien fichier par le nouveau
            shutil.move(temp_file, etat_file)
            log.info(f"Fichier {etat_file} mis à jour avec succès")
            
            return True
            
        except Exception as e:
            log_erreur(f"Erreur lors de l'écriture du fichier: {str(e)}")
            # Essayer de supprimer le fichier temporaire en cas d'erreur
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e2:
                log_erreur(f"Impossible de supprimer le fichier temporaire {temp_file}: {str(e2)}")
            return False
            
    except Exception as e:
        log_erreur(f"Erreur inattendue lors de la sauvegarde: {str(e)}")
        return False

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
        print(f"\n[DEBUG] Recherche du type de procédé: {type_procede}")
        
        # Vérifier si le fichier existe
        if not os.path.exists('data/types.json'):
            print("[ERREUR] Le fichier data/types.json n'existe pas")
            return None
            
        with open('data/types.json', 'r', encoding='utf-8') as f:
            types_data = json.load(f)
            
        print(f"[DEBUG] Types de procédés disponibles: {list(types_data.keys())}")

        # Normaliser les clés pour être insensibles à la casse et aux accents
        def normalize(s):
            return ''.join(c for c in unicodedata.normalize('NFD', str(s).lower())
                         if not unicodedata.combining(c))

        # Trouver la clé correspondante en ignorant la casse et les accents
        procede_key = None
        for key in types_data.keys():
            if normalize(key) == normalize(type_procede):
                procede_key = key
                break

        if not procede_key:
            print(f"\033[1;31m❌ Type de procédé '{type_procede}' non trouvé dans types.json.\033[0m")
            return None

        procede_info = types_data[procede_key]
        print(f"[DEBUG] Procédé trouvé: {procede_info.keys()}")

        # Créer un dictionnaire ordonné pour maintenir l'ordre des ouvrages
        ouvrages_ordonnes = OrderedDict()
        
        # Fonction pour ajouter des ouvrages à partir d'une source
        def ajouter_ouvrages(source, etat_par_defaut='en_service'):
            if isinstance(source, list):
                for ouvrage in source:
                    if isinstance(ouvrage, str) and ouvrage.strip():
                        ouvrages_ordonnes[ouvrage] = etat_par_defaut
            elif isinstance(ouvrage, str) and source.strip():
                ouvrages_ordonnes[source] = etat_par_defaut
        
        # 1. Ajouter les ouvrages de prétraitement
        if 'filiere_eau' in procede_info and 'pretraitement' in procede_info['filiere_eau']:
            ajouter_ouvrages(procede_info['filiere_eau']['pretraitement'])
        
        # 2. Ajouter le traitement primaire
        if 'filiere_eau' in procede_info and 'traitement_primaire' in procede_info['filiere_eau']:
            ajouter_ouvrages(procede_info['filiere_eau']['traitement_primaire'])
        
        # 3. Ajouter le traitement secondaire
        if 'filiere_eau' in procede_info and 'traitement_secondaire' in procede_info['filiere_eau']:
            ajouter_ouvrages(procede_info['filiere_eau']['traitement_secondaire'])
        
        # 4. Ajouter le traitement tertiaire
        if 'filiere_eau' in procede_info and 'traitement_tertiaire' in procede_info['filiere_eau']:
            ajouter_ouvrages(procede_info['filiere_eau']['traitement_tertiaire'])
        
        # 5. Ajouter la filière boue
        if 'filiere_boue' in procede_info:
            ajouter_ouvrages(procede_info['filiere_boue'])
        
        print(f"[DEBUG] Ouvrages ordonnés: {list(ouvrages_ordonnes.keys())}")
        return ouvrages_ordonnes
        
    except Exception as e:
        print(f"\n[ERREUR] Dans get_ouvrages_procede: {str(e)}")
        import traceback
        traceback.print_exc()
        time.sleep(2)
        return None

def load_json(file_path):
    """
    Charge un fichier JSON en préservant l'ordre des clés.
    
    Args:
        file_path (str): Chemin vers le fichier JSON à charger
        
    Returns:
        dict or list: Données chargées ou structure vide en cas d'erreur
    """
    try:
        # Vérifie si le fichier existe et n'est pas vide
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return [] if "etat_station" in file_path or "stations" in file_path else OrderedDict()
            
        def object_pairs_hook(pairs):
            # Crée un OrderedDict à partir des paires clé-valeur
            return OrderedDict(pairs)
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f, object_pairs_hook=object_pairs_hook)
            
            # Si c'est une liste, on la convertit en liste d'OrderedDict
            if isinstance(data, list):
                return [OrderedDict(item) if isinstance(item, dict) else item for item in data]
            return data
            
    except json.JSONDecodeError as e:
        log_erreur(f"Erreur de décodage JSON dans {file_path}: {str(e)}")
        return [] if "etat_station" in file_path or "stations" in file_path else OrderedDict()
    except Exception as e:
        log_erreur(f"Erreur lors du chargement de {file_path}: {str(e)}")
        return [] if "etat_station" in file_path or "stations" in file_path else OrderedDict()

def save_json(file_path, data, indent=2):
    """
    Sauvegarde des données dans un fichier JSON en préservant l'ordre des clés.
    
    Args:
        file_path (str): Chemin vers le fichier de sortie
        data: Données à sérialiser en JSON
        indent (int): Indentation pour le fichier de sortie
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Crée le répertoire s'il n'existe pas
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(ordered_data, f, indent=indent, ensure_ascii=False, sort_keys=False)
        
        return True
    except Exception as e:
        log_erreur(f"Erreur lors de la sauvegarde dans {file_path}: {str(e)}")
        return False

def clear_screen():
    """Efface l'écran de la console de manière multiplateforme"""
    try:
        # Pour Windows
        if os.name == 'nt':
            os.system('cls')
        # Pour Unix/Linux/MacOS
        else:
            os.system('clear')
    except Exception as e:
        # En cas d'erreur, on affiche plusieurs sauts de ligne
        print('\n' * 100)
        log_erreur(f"Erreur lors du nettoyage de l'écran: {str(e)}")

# Initialisation de la configuration des logs au chargement du module
configurer_journal()
