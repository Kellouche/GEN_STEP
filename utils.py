import logging
import os
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

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
    Retourne un dictionnaire vide en cas d'erreur ou si le fichier n'existe pas.
    """
    try:
        if not os.path.exists('data/etat_station.json'):
            return {}
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats_data = json.load(f)
        if not isinstance(etats_data, dict):
            log.warning("Le fichier etat_station.json ne contient pas un dictionnaire. Réinitialisation.")
            return {}
        return etats_data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        log.error(f"Erreur lors du chargement de etat_station.json: {e}")
        return {}

def sauvegarder_etats_station(etats_data: Dict[str, Any]) -> bool:
    """
    Sauvegarde l'état des stations dans le fichier JSON.
    
    Args:
        etats_data: Dictionnaire contenant les états des stations.
        
    Returns:
        True si la sauvegarde a réussi, False sinon.
    """
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/etat_station.json', 'w', encoding='utf-8') as f:
            json.dump(etats_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log.error(f"Erreur lors de la sauvegarde de etat_station.json: {e}")
        return False

# Initialisation de la configuration des logs au chargement du module
configurer_journal()
