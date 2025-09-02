import logging
import os
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
from collections import OrderedDict
import shutil
import time

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
    Gère à la fois l'ancien et le nouveau format de données.
    """
    try:
        if not os.path.exists('data/etat_station.json'):
            return {}
            
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats_data = json.load(f)
            
        # Si le fichier est vide ou pas un dictionnaire
        if not isinstance(etats_data, dict):
            return {}
            
        # Vérifier si c'est l'ancien format (sans liste)
        result = {}
        for station_id, data in etats_data.items():
            if isinstance(data, dict):
                # Ancien format - convertir en liste
                result[station_id] = [data]
            elif isinstance(data, list):
                # Nouveau format - garder tel quel
                result[station_id] = data
                
        return result
        
    except Exception as e:
        log.error(f"Erreur lors du chargement de etat_station.json: {e}")
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
        # Charger les états existants
        etats_data = charger_etats_station()
        if not isinstance(etats_data, dict):
            etats_data = {}
        
        # Vérifier et corriger la structure des données
        if not isinstance(etats_station, list):
            etats_station = [etats_station]
            
        # S'assurer que chaque état a un champ etat_ouvrages
        for etat in etats_station:
            if 'etat_ouvrages' not in etat:
                etat['etat_ouvrages'] = {}
            # S'assurer que etat_ouvrages est un OrderedDict
            if not isinstance(etat['etat_ouvrages'], OrderedDict):
                etat['etat_ouvrages'] = OrderedDict(etat['etat_ouvrages'])
        
        # Mettre à jour les états pour cette station
        etats_data[station_id] = etats_station
        
        # Créer un fichier temporaire
        temp_file = os.path.join('data', f'etat_station_{int(time.time())}.tmp')
        
        # Écrire dans le fichier temporaire
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(etats_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Remplacer l'ancien fichier par le nouveau
        etat_file = os.path.join('data', 'etat_station.json')
        backup_file = f"{etat_file}.bak.{int(time.time())}"
        
        # Créer une sauvegarde de l'ancien fichier
        if os.path.exists(etat_file):
            shutil.copy2(etat_file, backup_file)
        
        # Remplacer l'ancien fichier par le nouveau
        shutil.move(temp_file, etat_file)
        
        # Supprimer les anciennes sauvegardes si nécessaire
        # self.cleanup_old_backups('data', 'etat_station.json.bak.')
        
        return True
        
    except Exception as e:
        log_erreur(f"Erreur lors de la sauvegarde des états de la station {station_id}: {str(e)}")
        return False

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
