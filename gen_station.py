import json
import os
from datetime import datetime
import logging
from collections import OrderedDict

# Configuration du système de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Alias pour les logs
log_info = logging.info
log_avertissement = logging.warning
log_erreur = logging.error

# --- Fonctions utilitaires ---
def formater_nom_procede(nom_procede):
    """
    Formate un nom de procédé pour l'affichage.
    
    Args:
        nom_procede (str): Nom du procédé (ex: 'boues_activees')
        
    Returns:
        str: Nom formaté (ex: 'Boues Activées')
    """
    if not isinstance(nom_procede, str):
        return str(nom_procede)
        
    # Remplace les underscores par des espaces et met en majuscule la première lettre de chaque mot
    mots = nom_procede.split('_')
    mots_formates = [mot.capitalize() for mot in mots if mot]
    return ' '.join(mots_formates)

# --- Chargement des données ---
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Erreur de décodage JSON dans {file_path}: {str(e)}"
        log_erreur(error_msg)
        raise
    except FileNotFoundError as e:
        error_msg = f"Fichier non trouvé: {file_path}"
        log_erreur(error_msg)
        raise
    except Exception as e:
        error_msg = f"Erreur inattendue lors du chargement de {file_path}: {str(e)}"
        log_erreur(error_msg)
        raise

def get_types():
    """
    Load and return procedure types from types.json with formatted display names.
    
    Returns:
        dict: Dictionary of procedure types with their configurations and display names
    """
    try:
        types = load_json("data/types.json")
        if not isinstance(types, dict):
            error_msg = "Le fichier types.json ne contient pas un format de dictionnaire valide"
            log_erreur(error_msg)
            return {}
            
        # Add formatted display name to each procedure type
        for key, value in types.items():
            if isinstance(value, dict):
                value['display_name'] = formater_nom_procede(key)
        
        return types
        
    except Exception as e:
        log_erreur("Erreur lors du chargement des types de procédés", exc_info=True)
        return {}

def create_initial_state(ouvrages):
    """
    Crée un état initial pour les ouvrages fournis
    
    Args:
        ouvrages (list): Liste des noms d'ouvrages
        
    Returns:
        dict: Dictionnaire des états initiaux (tous en service par défaut)
    """
    if not isinstance(ouvrages, list):
        log_erreur("Le paramètre 'ouvrages' doit être une liste")
        return {}
        
    # Créer un dictionnaire avec tous les ouvrages en service par défaut
    etat_initial = {}
    for ouvrage in ouvrages:
        if isinstance(ouvrage, str) and ouvrage.strip():
            etat_initial[ouvrage.strip()] = 'en_service'
    
    return etat_initial

def get_ouvrages_procede(procedure_type, types_data):
    """
    Récupère la liste des ouvrages pour un type de procédé donné en respectant l'ordre logique de traitement.
    
    Args:
        procedure_type (str): Le type de procédé (ex: 'MBR')
        types_data (dict): Les données des types de procédés
        
    Returns:
        OrderedDict: Dictionnaire ordonné des états initiaux des ouvrages
    """
    if not procedure_type or not isinstance(types_data, dict):
        log_avertissement("Type de procédé ou données de types invalides")
        return OrderedDict()
    
    try:
        # Vérifier si le type de procédé existe
        if procedure_type not in types_data:
            log_avertissement(f"Type de procédé '{procedure_type}' non trouvé dans les données")
            return OrderedDict()
            
        procedure_data = types_data[procedure_type]
        if not isinstance(procedure_data, dict):
            log_avertissement(f"Données du procédé '{procedure_type}' invalides")
            return OrderedDict()
        
        etat_initial = OrderedDict()
        
        # 1. Filière eau - prétraitement
        pretraitement = procedure_data.get('filiere_eau', {}).get('pretraitement', [])
        if isinstance(pretraitement, list):
            for item in pretraitement:
                if isinstance(item, str) and item.strip():
                    etat_initial[item.strip()] = 'en_service'
        
        # 2. Filière eau - traitement primaire
        traitement_primaire = procedure_data.get('filiere_eau', {}).get('traitement_primaire', [])
        if isinstance(traitement_primaire, list):
            for item in traitement_primaire:
                if isinstance(item, str) and item.strip():
                    etat_initial[item.strip()] = 'en_service'
        
        # 3. Filière eau - traitement secondaire
        traitement_secondaire = procedure_data.get('filiere_eau', {}).get('traitement_secondaire', [])
        if isinstance(traitement_secondaire, list):
            for item in traitement_secondaire:
                if isinstance(item, str) and item.strip():
                    etat_initial[item.strip()] = 'en_service'
        
        # 4. Traitement tertiaire
        traitement_tertiaire = procedure_data.get('traitement_tertiaire', [])
        if isinstance(traitement_tertiaire, list):
            for item in traitement_tertiaire:
                if isinstance(item, str) and item.strip() and item.strip() not in etat_initial:
                    etat_initial[item.strip()] = 'en_service'
        
        # 5. Filière boue
        filiere_boue = procedure_data.get('filiere_boue', [])
        if isinstance(filiere_boue, list):
            for item in filiere_boue:
                if isinstance(item, str) and item.strip() and item.strip() not in etat_initial:
                    etat_initial[item.strip()] = 'en_service'
        
        return etat_initial
        
    except Exception as e:
        log_erreur(f"Erreur lors de la récupération des ouvrages pour le procédé '{procedure_type}': {str(e)}", exc_info=True)
        return OrderedDict()

def get_stations():
    """
    Load and return the list of stations from stations.json
    """
    try:
        stations = load_json("data/stations.json")
        if not isinstance(stations, list):
            log_avertissement("Le fichier stations.json ne contient pas un tableau, initialisation d'une nouvelle liste")
            return []
        return stations
    except Exception as e:
        log_erreur("Erreur lors du chargement des stations", exc_info=True)
        return []

def get_etats():
    """
    Charge et retourne la liste des états des stations depuis etat_station.json
    
    Returns:
        list: Liste des états des stations avec la structure mise à jour
    """
    try:
        etats = load_json("data/etat_station.json")
        if not isinstance(etats, list):
            log_avertissement("Le fichier etat_station.json ne contient pas un tableau, initialisation d'une nouvelle liste")
            return []
            
        # Vérifier et mettre à jour le format des états si nécessaire
        for etat in etats:
            # Si l'état utilise l'ancien format (clé 'etat'), le convertir au nouveau format
            if 'etat' in etat and 'etat_ouvrages' not in etat:
                etat['etat_ouvrages'] = etat.pop('etat')
                
        return etats
        
    except Exception as e:
        log_erreur(f"Erreur lors du chargement des états de station: {str(e)}", exc_info=True)
        return []

# --- Fonction pour trouver une station ---
def get_station(station_name):
    """
    Find a station by name (case-insensitive)
    
    Args:
        station_name (str): Name of the station to find
        
    Returns:
        dict: Station data if found, None otherwise
    """
    try:
        stations = get_stations()
        for s in stations:
            if s.get("nom", "").lower() == station_name.lower():
                return s
        log_avertissement(f"Station non trouvée: {station_name}")
        return None
    except Exception as e:
        log_erreur(f"Erreur lors de la recherche de la station {station_name}", exc_info=True)
        return None

# --- Récupérer toutes les dates disponibles pour une station ---
def get_dates_for_station(station_id):
    # Convertir station_id en chaîne si ce n'est pas déjà le cas
    station_id = str(station_id)
    etats = get_etats()
    return sorted([e["date"] for e in etats if str(e.get("station_id")) == station_id])

# --- Récupérer l'état d'une station pour une date ---
def get_state_for_date(station_id, date):
    # Convertir station_id en chaîne si ce n'est pas déjà le cas
    station_id = str(station_id)
    etats = get_etats()
    for e in etats:
        if str(e.get("station_id")) == station_id and e.get("date") == date:
            return e.get("etat", {})
    return {}

# --- Dessin du schéma ---
def load_step_config(step_type):
    """
    Charge la configuration d'un type de STEP à partir du fichier types.json
    
    Args:
        step_type (str): Le type de STEP (ex: 'boues_activées', 'SBR', etc.)
        
    Returns:
        dict: Configuration de la STEP ou None si non trouvée
    """
    types = get_types()
    if step_type in types:
        return types[step_type]
    log_avertissement(f"Type de STEP '{step_type}' non trouvé dans la configuration.")
    return None

def get_ouvrage_state(ouvrage_name, etat_actuel):
    """
    Récupère l'état d'un ouvrage en fonction de son nom
    
    Retourne un tuple contenant l'état et la couleur associée :
    - "en_service" (vert) - Par défaut si non spécifié
    - "en_panne" (rouge)
    - "en_maintenance" (orange)
    - "hors_service" (gris)
    - "inexistant" (blanc avec bordure pointillée)
    """
    # Définition des couleurs pour chaque état
    etats_couleurs = {
        'en_service': ('en_service', '#4CAF50'),  # Vert
        'en_panne': ('en_panne', '#F44336'),     # Rouge
        'en_maintenance': ('en_maintenance', '#FF9800'),  # Orange
        'hors_service': ('hors_service', '#9E9E9E'),  # Gris
        'inexistant': ('inexistant', '#FFFFFF')   # Blanc
    }
    
    # État par défaut si non trouvé
    etat_par_defaut = 'en_service'
    
    if not etat_actuel or not isinstance(etat_actuel, dict):
        return etats_couleurs[etat_par_defaut]
    
    # Nettoyer le nom de l'ouvrage pour la comparaison
    clean_ouvrage_name = ouvrage_name.replace("\n", "").strip()
    
    # Recherche directe dans le dictionnaire d'états
    for key, value in etat_actuel.items():
        clean_key = key.replace("\n", "").strip()
        if clean_key == clean_ouvrage_name:
            # Vérifier si l'état est valide
            if value in etats_couleurs:
                return etats_couleurs[value]
            return etats_couleurs[etat_par_defaut]
    
    # Si non trouvé, essayer avec des variations du nom
    # 1. Essayer avec des remplacements de caractères spéciaux
    variations = [
        clean_ouvrage_name,
        clean_ouvrage_name.replace(" ", ""),
        clean_ouvrage_name.replace("-", " "),
        clean_ouvrage_name.replace(" ", "-")
    ]
    
    for var in variations:
        for key, value in etat_actuel.items():
            clean_key = key.replace("\n", "").strip()
            if clean_key.lower() == var.lower():
                if value in etats_couleurs:
                    return etats_couleurs[value]
                return etats_couleurs[etat_par_defaut]
    
    # Si toujours pas trouvé, vérifier si c'est un ouvrage de la filière boue
    if "boues" in clean_ouvrage_name.lower() or "boue" in clean_ouvrage_name.lower():
        for key, value in etat_actuel.items():
            if "boue" in key.lower():
                if value in etats_couleurs:
                    return etats_couleurs[value]
    
    # Si l'état n'est pas reconnu, retourner l'état par défaut
    return etats_couleurs[etat_par_defaut]

def merge_process_with_states(process_config, etat_actuel):
    """
    Fusionne la configuration du procédé avec les états personnalisés.
    
    Args:
        process_config (dict): Configuration du procédé depuis types.json
        etat_actuel (dict): États courants des ouvrages depuis etat_station.json
        
    Returns:
        dict: Configuration fusionnée avec les états mis à jour
    """
    # Vérification des entrées
    if not isinstance(process_config, dict) or not isinstance(etat_actuel, dict):
        log_erreur("Les paramètres doivent être des dictionnaires")
        return process_config
    
    # Créer une copie profonde de la configuration pour éviter de modifier l'original
    config_mise_a_jour = json.loads(json.dumps(process_config))
    
    # Parcourir tous les ouvrages de la configuration
    for filiere, ouvrages in config_mise_a_jour.items():
        if not isinstance(ouvrages, list):
            continue
            
        for ouvrage in ouvrages:
            if not isinstance(ouvrage, dict):
                continue
                
            nom_ouvrage = ouvrage.get('nom')
            if not nom_ouvrage:
                continue
            
            # Mettre à jour l'état de l'ouvrage si présent dans etat_actuel
            if nom_ouvrage in etat_actuel:
                etat = etat_actuel[nom_ouvrage]
                ouvrage['etat'] = etat
                
                # Mettre à jour la couleur en fonction de l'état
                if etat == 'en_panne':
                    ouvrage['couleur'] = '#FF0000'  # Rouge
                elif etat == 'en_maintenance':
                    ouvrage['couleur'] = '#FFA500'  # Orange
                elif etat == 'hors_service':
                    ouvrage['couleur'] = '#808080'  # Gris
                elif etat == 'inexistant':
                    ouvrage['couleur'] = '#FFFFFF'  # Blanc
                    ouvrage['style'] = 'dashed'
                else:  # en_service
                    ouvrage['couleur'] = ouvrage.get('couleur', '#4CAF50')  # Vert par défaut
    
    return config_mise_a_jour

def draw_schema(station, date):
    if not station:
        log_avertissement("Aucune station fournie")
        return None, None

    # Charger les données
    types = get_types()
    etats = get_etats()
    
    # Récupérer l'état actuel de la station
    etat_actuel = None
    for etat in etats:
        if etat["station_id"] == station["id"] and etat["date"] == date:
            etat_actuel = etat["etat"]
            break
    
    # Si pas d'état trouvé, utiliser une structure vide
    if etat_actuel is None:
        etat_actuel = {}
    
    # Charger la configuration du type de procédé
    step_config = load_step_config(station.get('type_procede', ''))
    if not step_config:
        step_config = {}
    
    # Fusionner avec les états personnalisés
    step_config = merge_process_with_states(step_config, etat_actuel)
    
    # Palette de couleurs moderne
    colors = {
        # Couleurs principales
        "fond_page": "#F5F5F5",  # Gris très clair pour le fond
        "fond_bloc": "#FFFFFF",  # Blanc pour les blocs
        "bordure_bloc": "#BDBDBD",  # Gris clair pour les bordures
        "titre_principal": "#2C3E50",  # Bleu foncé pour les titres
        "texte_principal": "#212121",  # Gris très foncé pour le texte principal
        "texte_secondaire": "#757575",  # Gris pour le texte secondaire
        "texte_blanc": "#FFFFFF",   # Blanc pour le texte sur fond sombre
        "texte_noir": "#000000",    # Noir pour le texte sur fond clair
        
        # États des ouvrages
        "en_service": "#4CAF50",       # Vert vif - ouvrage en service
        "hors_service": "#9E9E9E",     # Gris - ouvrage arrêté
        "en_panne": "#F44336",         # Rouge vif - ouvrage en panne
        "en_maintenance": "#FF9800",   # Orange - ouvrage en maintenance
        "inexistant": "#607D8B",        # Bleu-gris - ouvrage non installé
        
        # Éléments d'interface
        "bordure": "#E0E0E0",       # Gris clair pour les bordures
        "fleche_eau": "#42A5F5",    # Bleu clair pour l'eau
        "fleche_boue": "#8D6E63",   # Marron clair pour les boues
        "ombres": (0, 0, 0, 0.1)    # Ombre légère (RGBA sous forme de tuple)
    }

    # Création d'une grille 2x4 (8 carrés) pour la figure
    #plt.style.use('seaborn-v0_8-white')
    #fig = plt.figure(figsize=(20, 14))
    
    # Création d'une grille 2x4 pour organiser le contenu
    #gs = fig.add_gridspec(2, 4, hspace=0.5, wspace=0.3)
    
    # Zone principale pour le schéma (6 premiers carrés)
    #ax = fig.add_subplot(gs[:, :3])  # 3 colonnes sur 2 lignes
    
    # Zone pour la légende (2 carrés en bas à droite)
    #legend_ax = fig.add_subplot(gs[1, 3])  # Dernière colonne, deuxième ligne
    
    # Configuration du fond
    #fig.patch.set_facecolor(colors["fond_page"])
    #ax.set_facecolor(colors["fond_page"])
    #ax.axis('off')
    
    # Titre avec bannière
    nom_station = station.get('nom', '').upper()
    
    # Formater la date correctement (convertir de YYYY-MM-DD à DD/MM/YYYY si nécessaire)
    try:
        # Essayer de parser la date au format YYYY-MM-DD (format ISO)
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%d/%m/%Y')
    except (ValueError, AttributeError) as e:
        # Si le format n'est pas reconnu, utiliser la date telle quelle
        log_avertissement(f"Format de date non reconnu ({date}), utilisation de la date brute")
        formatted_date = date
    
    # Récupérer le type de procédé depuis la station ou utiliser une valeur par défaut
    type_procede = station.get('type_procede', 'inconnu')
    
    # Formater le type de procédé pour l'affichage
    type_procede_affichage = type_procede.replace('_', ' ').title()
    
    # Créer le titre du schéma
    title_text = f"SCHEMA DE PRINCIPE - STEP {nom_station} | Date : {formatted_date} | Type de procédé : {type_procede_affichage}"
    
    # Afficher les informations de débogage
    log_info(f"Nom de la station: {nom_station}")
    log_info(f"Type de procédé: {type_procede}")
    
    # Ajout du titre avec un style moderne
    #fig.suptitle(title_text, 
                #fontsize=14, 
                #fontweight='bold',
                #color='#FFFFFF',  # Blanc pur pour une meilleure lisibilité
                #x=0.5,   # Centrer horizontalement
                #y=0.975,  # Ajuster la position verticale
                #ha='center',
                #va='top',
                #bbox=dict(facecolor='#1976D2',  # Bleu plus clair pour le fond
                         #edgecolor='#0D47A1',   # Bordure légèrement plus foncée
                         #boxstyle='round,pad=0.7',
                         #alpha=0.9))

    # Configuration des positions verticales pour chaque ligne de traitement
    y_positions = {
        "filiere_eau": 7,           # Ligne du haut pour la filière eau
        "filiere_boue": 4,          # Ligne du milieu pour la filière boue
        "traitement_tertiaire": 1   # Ligne du bas pour le traitement tertiaire
    }
    
    # Dimensions par défaut des blocs
    default_width = 2.5
    default_height = 1.2
    spacing = 1.0  # Espacement entre les blocs
    
    # Liste pour stocker tous les blocs
    blocs = []
    
    # Fonction utilitaire pour obtenir le nom d'un ouvrage (gère les chaînes et les dictionnaires)
    def get_ouvrage_name(item):
        if isinstance(item, dict):
            return list(item.keys())[0]
        return item
        
    # Fonction pour normaliser les noms (supprime les sauts de ligne et les espaces superflus)
    def normalize_name(name):
        try:
            if not name:
                return ""
            log_info(f"Normalisation du nom: {name} (type: {type(name)})")
            if isinstance(name, dict):
                log_info(f"Détection d'un dictionnaire: {name}")
                name = list(name.keys())[0]
                log_info(f"Nom extrait du dictionnaire: {name}")
            return ' '.join(str(name).replace('\n', ' ').replace('/', ' ').split())
        except Exception as e:
            log_avertissement(f"Erreur lors de la normalisation de {name} (type: {type(name)}): {str(e)}")
            return str(name) if name else ""
    
    # 1. Positionner les ouvrages de la filière eau (de gauche à droite)
    x_pos = 1
    
    # 1.1 Prétraitement
    if "filiere_eau" in step_config and "pretraitement" in step_config["filiere_eau"]:
        pretraitement = step_config["filiere_eau"]["pretraitement"]
        log_info("\nConfiguration du prétraitement: " + str(pretraitement))
        
        # Vérifier si c'est une liste (comme pour SBR) ou un dictionnaire (comme pour lagunage_naturel)
        if isinstance(pretraitement, list):
            for equip in pretraitement:
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage prétraitement (liste): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    nom_equip = equip.replace("/", "\n")
                    bloc = {
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    }
                    blocs.append(bloc)
                    log_info(f"Création bloc eau (liste): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
                    
        elif isinstance(pretraitement, dict):
            for equip, etat in pretraitement.items():
                # Vérifier si l'ouvrage est actif
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage prétraitement (dict): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":  # Ne pas afficher les ouvrages inexistants
                    nom_equip = equip.replace("/", "\n")
                    bloc = {
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    }
                    blocs.append(bloc)
                    log_info(f"Création bloc eau (dict): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
    
    # 1.2 Traitement primaire
    if "filiere_eau" in step_config and "traitement_primaire" in step_config["filiere_eau"]:
        traitement_primaire = step_config["filiere_eau"]["traitement_primaire"]
        log_info(f"\nConfiguration du traitement primaire: {traitement_primaire}")
        
        # Vérifier si c'est une liste (ancien format) ou un dictionnaire (nouveau format)
        if isinstance(traitement_primaire, list):
            for equip in traitement_primaire:
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage primaire (liste): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    nom_equip = equip.replace("/", "\n")
                    blocs.append({
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    })
                    log_info(f"Création bloc primaire (liste): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
        elif isinstance(traitement_primaire, dict):
            for equip, etat in traitement_primaire.items():
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage primaire (dict): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    nom_equip = equip.replace("/", "\n")
                    blocs.append({
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    })
                    log_info(f"Création bloc primaire (dict): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
    
    # 1.3 Traitement secondaire
    if "filiere_eau" in step_config and "traitement_secondaire" in step_config["filiere_eau"]:
        traitement_secondaire = step_config["filiere_eau"]["traitement_secondaire"]
        log_info(f"\nConfiguration du traitement secondaire: {traitement_secondaire}")
        
        # Vérifier si c'est une liste (ancien format) ou un dictionnaire (nouveau format)
        if isinstance(traitement_secondaire, list):
            for equip in traitement_secondaire:
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage secondaire (liste): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    nom_equip = equip.replace("/", "\n")
                    blocs.append({
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    })
                    log_info(f"Création bloc secondaire (liste): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
                    
        elif isinstance(traitement_secondaire, dict):
            for equip, etat in traitement_secondaire.items():
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage secondaire (dict): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    nom_equip = equip.replace("/", "\n")
                    blocs.append({
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_eau"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_eau",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    })
                    log_info(f"Création bloc secondaire (dict): {nom_equip} à ({x_pos}, {y_positions['filiere_eau']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
    
    # 2. Positionner les ouvrages de la filière boue (en dessous de la filière eau)
    x_pos = 1
    if "filiere_boue" in step_config and step_config["filiere_boue"]:
        filiere_boue = step_config["filiere_boue"]
        log_info("\nConfiguration de la filière boue: " + str(filiere_boue))
        
        # Gérer le cas où filiere_boue est un dictionnaire (comme pour lagunage_naturel)
        if isinstance(filiere_boue, dict):
            for equip, etat in filiere_boue.items():
                # Vérifier si l'ouvrage est actif
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage boue (dict): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":  # Ne pas afficher les ouvrages inexistants
                    nom_equip = equip.replace("/", "\n")
                    bloc = {
                        "nom": nom_equip,
                        "x": x_pos,
                        "y": y_positions["filiere_boue"],
                        "w": default_width,
                        "h": default_height,
                        "type": "filiere_boue",
                        "etat": etat_equip,  # Ajouter l'état au bloc
                        "couleur": couleur_equip  # Ajouter la couleur au bloc
                    }
                    blocs.append(bloc)
                    log_info(f"Création bloc boue (depuis dict): {nom_equip} à ({x_pos}, {y_positions['filiere_boue']}), état: {etat_equip}, couleur: {couleur_equip}")
                    x_pos += default_width + spacing
        
        # Gérer le cas où filiere_boue est une liste (format standard)
        elif isinstance(filiere_boue, list):
            for equip in filiere_boue:
                # Si l'ouvrage est un dictionnaire (format avancé)
                if isinstance(equip, dict):
                    for equip_name, equip_etat in equip.items():
                        etat_equip, couleur_equip = get_ouvrage_state(equip_name, etat_actuel)
                        log_info(f"Ouvrage boue (liste-dict): {equip_name}, état: {etat_equip}, couleur: {couleur_equip}")
                        if etat_equip != "inexistant":
                            nom_equip = equip_name.replace("/", "\n")
                            blocs.append({
                                "nom": nom_equip,
                                "x": x_pos,
                                "y": y_positions["filiere_boue"],
                                "w": default_width,
                                "h": default_height,
                                "type": "filiere_boue",
                                "etat": etat_equip,  # Ajouter l'état au bloc
                                "couleur": couleur_equip  # Ajouter la couleur au bloc
                            })
                            log_info(f"Création bloc boue (depuis liste-dict): {nom_equip} à ({x_pos}, {y_positions['filiere_boue']}), état: {etat_equip}, couleur: {couleur_equip}")
                            x_pos += default_width + spacing
                # Si l'ouvrage est une chaîne (format simple)
                elif isinstance(equip, str):
                    etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                    log_info(f"Ouvrage boue (liste-str): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                    if etat_equip != "inexistant":
                        nom_equip = equip.replace("/", "\n")
                        blocs.append({
                            "nom": nom_equip,
                            "x": x_pos,
                            "y": y_positions["filiere_boue"],
                            "w": default_width,
                            "h": default_height,
                            "type": "filiere_boue",
                            "etat": etat_equip,  # Ajouter l'état au bloc
                            "couleur": couleur_equip  # Ajouter la couleur au bloc
                        })
                        log_info(f"Création bloc boue (depuis liste-str): {nom_equip} à ({x_pos}, {y_positions['filiere_boue']}), état: {etat_equip}, couleur: {couleur_equip}")
                        x_pos += default_width + spacing
    
    # 3. Positionner les ouvrages du traitement tertiaire (en bas)
    x_pos = 1
    if "traitement_tertiaire" in step_config and step_config["traitement_tertiaire"]:
        log_info("\nConfiguration du traitement tertiaire: " + str(step_config["traitement_tertiaire"]))
        
        # Initialiser la liste des ouvrages actifs
        ouvrages_tertiaires_actifs = []
        
        # Vérifier si c'est une liste (ancien format) ou un dictionnaire (nouveau format)
        if isinstance(step_config["traitement_tertiaire"], list):
            for equip in step_config["traitement_tertiaire"]:
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage tertiaire (liste): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    ouvrages_tertiaires_actifs.append(equip)
        
        elif isinstance(step_config["traitement_tertiaire"], dict):
            for equip, etat in step_config["traitement_tertiaire"].items():
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                log_info(f"Ouvrage tertiaire (dict): {equip}, état: {etat_equip}, couleur: {couleur_equip}")
                if etat_equip != "inexistant":
                    ouvrages_tertiaires_actifs.append(equip)
        
        # Si aucun ouvrage tertiaire actif, ne pas afficher cette section
        if not ouvrages_tertiaires_actifs:
            log_info("Aucun ouvrage tertiaire actif à afficher")
            step_config["traitement_tertiaire"] = []
        else:
            log_info(f"Ouvrages tertiaires actifs: {ouvrages_tertiaires_actifs}")
            
            # Dessiner la flèche de liaison si nécessaire
            if "filiere_eau" in step_config and "liaison_traitement_tertiaire" in step_config["filiere_eau"]:
                source_tertiaire = step_config["filiere_eau"]["liaison_traitement_tertiaire"]
                # Vérifier que la source est active
                source_active = get_ouvrage_state(source_tertiaire, etat_actuel) != "inexistant"
                log_info(f"Source tertiaire: {source_tertiaire}, active: {source_active}")
                
                if source_active:
                    # Trouver le bloc source (dernier bloc du traitement secondaire)
                    for b in blocs:
                        # Vérifier si le nom du bloc (avec ou sans sauts de ligne) correspond à la source
                        nom_brut = b["nom"].replace("\n", "").strip()
                        source_tertiaire_clean = source_tertiaire.replace("/", "").replace(" ", "").lower()
                        if source_tertiaire_clean == nom_brut:
                            # Coordonnées du point de départ (bas du bloc source)
                            x1 = b["x"] + b["w"] / 2
                            y1 = b["y"]
                            # Coordonnées du point d'arrivée (haut du premier bloc tertiaire)
                            x2 = x_pos + default_width / 2
                            y2 = y_positions["traitement_tertiaire"] + default_height
                            # Dessiner la flèche
                            #ax.arrow(x1, y1, x2 - x1, y2 - y1, 
                                    #head_width=0.15, head_length=0.2, 
                                    #fc=colors["fleche_eau"], ec=colors["fleche_eau"],
                                    #length_includes_head=True, zorder=2)
                            log_info(f"Flèche dessinée de {source_tertiaire} vers traitement tertiaire")
                            break
            
            # Ajouter uniquement les ouvrages actifs du traitement tertiaire
            for equip in ouvrages_tertiaires_actifs:
                nom_equip = equip.replace("/", "\n")
                etat_equip, couleur_equip = get_ouvrage_state(equip, etat_actuel)
                blocs.append({
                    "nom": nom_equip,
                    "x": x_pos,
                    "y": y_positions["traitement_tertiaire"],
                    "w": default_width,
                    "h": default_height,
                    "type": "traitement_tertiaire",
                    "etat": etat_equip,
                    "couleur": couleur_equip
                })
                log_info(f"Création bloc tertiaire: {nom_equip} à ({x_pos}, {y_positions['traitement_tertiaire']}), état: {etat_equip}, couleur: {couleur_equip}")
                x_pos += default_width + spacing
    
    # Dictionnaire de correspondance des états
    etat_par_defaut = "inexistant"
    correspondance_etats = {
        "Dégrillage": ["Dégrillage grossier", "Dégrillage fin"],
        "Dessablage\nDégraissage": ["Dessablage", "Dégraissage"],
        "Bassin\nd'aération": ["Réacteur biologique"],
        "Clarificateur": ["Décantation secondaire"],
        "Épaississeur": ["Épaississement"],
        "Séchage\nmécanique": ["Séchage mécanique"],
        "Stockage\ndes boues": ["Stockage boues sèches"],
        "Filtration\nsur sable": ["Filtration sur sable"],
        "Désinfection\nUV": ["Désinfection UV"]
    }

    # Dessiner les flèches pour chaque filière
    if "filiere_eau" in step_config and step_config["filiere_eau"]:
        # Liste pour stocker tous les ouvrages actifs dans l'ordre
        all_active_equipment = []
        
        # Fonction pour ajouter un ouvrage à la liste s'il est actif
        def add_equipment(equipment, section_name):
            if isinstance(equipment, dict):
                # Si c'est un dictionnaire, vérifier l'état
                for equip_name, state in equipment.items():
                    if state == "en_service":
                        nom_equip = equip_name.replace("/", "\n")
                        if not any(nom_equip == e.replace("/", "\n") for e in all_active_equipment):
                            all_active_equipment.append(nom_equip)
                            log_info(f"Ajout ouvrage {section_name}: {nom_equip}")
            elif isinstance(equipment, list):
                # Si c'est une liste, tous les ouvrages sont actifs
                for equip_name in equipment:
                    if isinstance(equip_name, str):
                        nom_equip = equip_name.replace("/", "\n")
                        if not any(nom_equip == e.replace("/", "\n") for e in all_active_equipment):
                            all_active_equipment.append(nom_equip)
                            log_info(f"Ajout ouvrage {section_name} (liste): {nom_equip}")
        
        # Traiter le prétraitement
        if "pretraitement" in step_config["filiere_eau"]:
            pretraitement = step_config["filiere_eau"]["pretraitement"]
            add_equipment(pretraitement, "prétraitement")
        
        # Vérifier si le traitement primaire est marqué comme inexistant
        primaire_inexistant = False
        if "traitement_primaire" in step_config["filiere_eau"]:
            traitement_primaire = step_config["filiere_eau"]["traitement_primaire"]
            if isinstance(traitement_primaire, list) and any(isinstance(x, dict) and x.get("Décanteur primaire") == "inexistant" for x in traitement_primaire):
                primaire_inexistant = True
                log_info("Le traitement primaire est marqué comme inexistant, on le saute")
            else:
                add_equipment(traitement_primaire, "primaire")
        
        # Traiter le traitement secondaire
        if "traitement_secondaire" in step_config["filiere_eau"] and step_config["filiere_eau"]["traitement_secondaire"]:
            traitement_secondaire = step_config["filiere_eau"]["traitement_secondaire"]
            add_equipment(traitement_secondaire, "secondaire")
        
        # Si le traitement primaire est inexistant, on s'assure qu'il n'est pas dans la liste des équipements actifs
        if primaire_inexistant:
            all_active_equipment = [e for e in all_active_equipment 
                                 if not any(x in e for x in ["Décanteur primaire", "Décanteur\nprimaire"])]
        
        # Afficher les ouvrages actifs pour le débogage
        log_info(f"Ouvrages actifs: {all_active_equipment}")
        
        # Afficher la liste des ouvrages actifs pour le débogage
        log_info("\nListe des ouvrages actifs:")
        for i, equip in enumerate(all_active_equipment):
            log_info(f"  {i+1}. {equip}")
            
        # Dessiner les flèches entre les ouvrages actifs
        for i in range(len(all_active_equipment) - 1):
            source = all_active_equipment[i].replace("\n", " ").strip()
            target = all_active_equipment[i+1].replace("\n", " ").strip()
            log_info(f"\nTentative de dessin flèche eau: '{source}' -> '{target}'")
            
            # Trouver les blocs source et cible
            bloc1 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == source), None)
            bloc2 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == target), None)
            
            if bloc1 and bloc2:
                # Calculer les coordonnées des centres des blocs
                x1 = bloc1["x"] + bloc1["w"]/2
                y1 = bloc1["y"] + bloc1["h"]/2
                x2 = bloc2["x"] + bloc2["w"]/2
                y2 = bloc2["y"] + bloc2["h"]/2
                
                # Dessiner la flèche
                #ax.annotate("", 
                           #xy=(x2, y2), 
                           #xytext=(x1, y1),
                           #arrowprops=dict(arrowstyle="->",
                                         #color=colors["fleche_eau"],
                                         #linewidth=1.5,
                                         #connectionstyle="arc3,rad=0.2",
                                         #shrinkA=10,
                                         #shrinkB=10))
    
    # Gérer les boues secondaires si spécifié
    if "boues_secondaires" in step_config["filiere_eau"] and step_config["filiere_eau"]["boues_secondaires"] and "source" in step_config["filiere_eau"]["boues_secondaires"]:
        source_boues = step_config["filiere_eau"]["boues_secondaires"]["source"]
        log_info(f"Source des boues secondaires: {source_boues}")
        
        # Vérifier si la source des boues est dans les ouvrages actifs
        source_active = any(source_boues.replace("/", "\n").strip() == e.replace("/", "\n").strip() 
                         for e in all_active_equipment)
        
        if source_active and "filiere_boue" in step_config:
            # Trouver les ouvrages de la filière boue actifs
            boue_equipment = []
            
            if isinstance(step_config["filiere_boue"], dict):
                boue_equipment = [name for name, state in step_config["filiere_boue"].items() 
                                if state == "en_service"]
            elif isinstance(step_config["filiere_boue"], list):
                # Pour les configurations comme SBR où c'est une liste
                boue_equipment = [name for name in step_config["filiere_boue"] 
                                if isinstance(name, str)]
            
            log_info(f"Ouvrages de la filière boue: {boue_equipment}")
            
            if boue_equipment:
                # Nettoyer les noms des ouvrages pour la correspondance
                clean_source = source_boues.replace("\n", " ").strip()
                clean_boues = [e.replace("\n", " ").strip() for e in boue_equipment]
                
                # Ne garder que les ouvrages actifs et présents dans les blocs
                active_boues = []
                for boue in clean_boues:
                    # Vérifier si l'ouvrage boue est dans les blocs actifs
                    if any(b["nom"].replace("\n", " ").strip() == boue for b in blocs):
                        active_boues.append(boue)
                
                log_info(f"Ouvrages boue actifs: {active_boues}")
                
                if active_boues:
                    # Dessiner la flèche de la source vers le premier ouvrage boue
                    log_info(f"Dessin flèche boues: {clean_source} -> {active_boues[0]}")
                    
                    # Trouver les blocs source et cible
                    bloc1 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == clean_source), None)
                    bloc2 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == active_boues[0]), None)
                    
                    if bloc1 and bloc2:
                        # Calculer les coordonnées des centres des blocs
                        x1 = bloc1["x"] + bloc1["w"]/2
                        y1 = bloc1["y"] + bloc1["h"]/2
                        x2 = bloc2["x"] + bloc2["w"]/2
                        y2 = bloc2["y"] + bloc2["h"]/2
                        
                        # Dessiner la flèche
                        #ax.annotate("", 
                                   #xy=(x2, y2), 
                                   #xytext=(x1, y1),
                                   #arrowprops=dict(arrowstyle="->",
                                                 #color=colors["fleche_boue"],
                                                 #linewidth=1.5,
                                                 #connectionstyle="arc3,rad=0.2",
                                                 #shrinkA=10,
                                                 #shrinkB=10))
                    
                    # Dessiner les flèches entre les ouvrages de la filière boue
                    for i in range(len(active_boues) - 1):
                        source = active_boues[i]
                        target = active_boues[i+1]
                        log_info(f"Dessin flèche boue: {source} -> {target}")
                        
                        # Trouver les blocs source et cible
                        bloc1 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == source), None)
                        bloc2 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == target), None)
                        
                        if bloc1 and bloc2:
                            # Calculer les coordonnées des centres des blocs
                            x1 = bloc1["x"] + bloc1["w"]/2
                            y1 = bloc1["y"] + bloc1["h"]/2
                            x2 = bloc2["x"] + bloc2["w"]/2
                            y2 = bloc2["y"] + bloc2["h"]/2
                            
                            # Dessiner la flèche
                            #ax.annotate("", 
                                       #xy=(x2, y2), 
                                       #xytext=(x1, y1),
                                       #arrowprops=dict(arrowstyle="->",
                                                     #color=colors["fleche_boue"],
                                                     #linewidth=1.5,
                                                     #connectionstyle="arc3,rad=0.2",
                                                     #shrinkA=10,
                                                     #shrinkB=10))
        elif "filiere_boue" in step_config and step_config["filiere_boue"]:
            # Pour le type lagunage_naturel qui n'a pas de boues_secondaires définies
            if isinstance(step_config["filiere_boue"], dict):
                boue_equipment = [name for name, state in step_config["filiere_boue"].items() 
                                if state == "en_service"]
                
                if boue_equipment:
                    # Ne garder que les ouvrages présents dans les blocs
                    active_boues = []
                    for boue in boue_equipment:
                        boue_clean = boue.replace("\n", " ").strip()
                        if any(b["nom"].replace("\n", " ").strip() == boue_clean for b in blocs):
                            active_boues.append(boue_clean)
                    
                    log_info(f"Ouvrages boue actifs (lagunage): {active_boues}")
                    
                    # Dessiner les flèches entre les ouvrages de la filière boue
                    for i in range(len(active_boues) - 1):
                        source = active_boues[i]
                        target = active_boues[i+1]
                        log_info(f"Dessin flèche boue (lagunage): {source} -> {target}")
                        
                        # Trouver les blocs source et cible
                        bloc1 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == source), None)
                        bloc2 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == target), None)
                        
                        if bloc1 and bloc2:
                            # Calculer les coordonnées des centres des blocs
                            x1 = bloc1["x"] + bloc1["w"]/2
                            y1 = bloc1["y"] + bloc1["h"]/2
                            x2 = bloc2["x"] + bloc2["w"]/2
                            y2 = bloc2["y"] + bloc2["h"]/2
                            
                            # Dessiner la flèche
                            #ax.annotate("", 
                                       #xy=(x2, y2), 
                                       #xytext=(x1, y1),
                                       #arrowprops=dict(arrowstyle="->",
                                                     #color=colors["fleche_boue"],
                                                     #linewidth=1.5,
                                                     #connectionstyle="arc3,rad=0.2",
                                                     #shrinkA=10,
                                                     #shrinkB=10))
    
    # 4. Flèches de liaison entre les lignes de traitement
    # Par exemple, du clarificateur vers l'épaississeur
    clarif_exists = any(b["nom"].replace("\n", " ").strip() == "Clarificateur" for b in blocs)
    epaississeur_exists = any(b["nom"].replace("\n", " ").strip() == "Épaississeur" for b in blocs)
    
    if clarif_exists and epaississeur_exists:
        log_info("Dessin flèche Clarificateur -> Épaississeur")
        
        # Trouver les blocs source et cible
        bloc1 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == "Clarificateur"), None)
        bloc2 = next((b for b in blocs if b["nom"].replace("\n", " ").strip() == "Épaississeur"), None)
        
        if bloc1 and bloc2:
            # Calculer les coordonnées des centres des blocs avec un décalage vertical
            x1 = bloc1["x"] + bloc1["w"]/2
            y1 = bloc1["y"] + bloc1["h"]/2 - 0.2
            x2 = bloc2["x"] + bloc2["w"]/2
            y2 = bloc2["y"] + bloc2["h"]/2 - 0.2
            
            # Dessiner la flèche
            #ax.annotate("", 
                       #xy=(x2, y2), 
                       #xytext=(x1, y1),
                       #arrowprops=dict(arrowstyle="->",
                                     #color=colors["fleche_boue"],
                                     #linewidth=1.5,
                                     #connectionstyle="arc3,rad=0.2",
                                     #shrinkA=10,
                                     #shrinkB=10))
    
    # Dessiner les blocs avec un style moderne
    for bloc in blocs:
        # Récupérer l'état et la couleur du bloc
        etat = bloc.get("etat", "en_service")  # Par défaut à "en_service" si non spécifié
        couleur = bloc.get("couleur", "#4CAF50")  # Vert par défaut si non spécifié
        
        # Déterminer le style de bordure en fonction de l'état
        if etat == "inexistant":
            line_style = 'dashed'
            line_width = 1.5
        else:
            line_style = 'solid'
            line_width = 2
        
        # Créer le rectangle avec ombre portée pour l'effet 3D
        #shadow = FancyBboxPatch(
            #(bloc["x"] + 0.1, bloc["y"] - 0.1), 
            #bloc["w"], 
            #bloc["h"],
            #boxstyle="round,pad=0.1,rounding_size=0.2",
            #facecolor='#333333',  # Couleur de l'ombre
            #alpha=0.3,  # Transparence de l'ombre
            #zorder=1
        #)
        #ax.add_patch(shadow)
        
        # Créer le rectangle principal
        #rect = FancyBboxPatch(
            #(bloc["x"], bloc["y"]), 
            #bloc["w"], 
            #bloc["h"],
            #boxstyle="round,pad=0.1,rounding_size=0.2",
            #facecolor=couleur,  # Utiliser la couleur spécifiée pour l'état
            #edgecolor='#333333',  # Couleur de la bordure
            #linewidth=line_width,
            #linestyle=line_style,
            #zorder=2
        #)
        #ax.add_patch(rect)
        
        # Ajouter le nom de l'ouvrage avec gestion des retours à la ligne pour les longs noms
        nom_affichage = bloc["nom"]
        
        # Gestion spécifique des noms longs avec retours à la ligne
        if "Epaississement des boues" in nom_affichage:
            nom_affichage = "Epaississement\ndes boues"
        elif "Désinfection UV" in nom_affichage:
            nom_affichage = "Désinfection\nUV"
        elif "Filtration sur sable" in nom_affichage:
            nom_affichage = "Filtration\nsur sable"
        elif "Dessablage/Dégraissage" in nom_affichage:
            nom_affichage = "Dessablage/\nDégraissage"
        elif "Boues activées" in nom_affichage:
            nom_affichage = "Boues\nactivées"
        elif "Décantation secondaire" in nom_affichage:
            nom_affichage = "Décantation\nsecondaire"
            
        #ax.text(
            #bloc["x"] + bloc["w"]/2, 
            #bloc["y"] + bloc["h"]/2, 
            #nom_affichage, 
            #ha='center', 
            #va='center',
            #color='#000000' if etat == "inexistant" else '#FFFFFF',
            #fontsize=8,  # Légèrement plus petit pour mieux s'adapter
            #fontweight='bold',
            #zorder=3
        #)
        
        # Ajouter un indicateur d'état si nécessaire (sauf pour "en_service" et "inexistant")
        if etat not in ["en_service", "inexistant"]:
            etat_texte = etat.replace('_', ' ').title()
            #ax.text(
                #bloc["x"] + bloc["w"]/2,
                #bloc["y"] + bloc["h"] + 0.1, 
                #f"({etat_texte})", 
                #ha='center', 
                #va='bottom',
                #color='#FF0000' if etat == "en_panne" else '#000000',  # Texte rouge pour "en panne"
                #fontsize=8,
                #fontstyle='italic',
                #zorder=3
            #)
    
    # Configurer l'aspect de la figure
    #ax.set_aspect('equal')
    
    # Style moderne pour la légende (à afficher dans l'axe dédié)
    legend_style = {
        'frameon': True,
        'fancybox': True,
        'framealpha': 0.95,
        'shadow': True,
        'borderpad': 1.2,
        'labelspacing': 1.2,
        'handlelength': 2,
        'handleheight': 1.5,
        'fontsize': 10,
        'facecolor': '#FFFFFF',  # Fond blanc
        'edgecolor': '#E0E0E0', # Bordure légère
        'borderaxespad': 0.5,
        'title_fontsize': 11
    }
    
    # Couleurs cohérentes avec le reste du schéma
    colors_etat = {
        'en_service': {'face': '#4CAF50', 'edge': '#2E7D32'},  # Vert
        'en_panne': {'face': '#F44336', 'edge': '#B71C1C'},    # Rouge
        'en_maintenance': {'face': '#FF9800', 'edge': '#E65100'},  # Orange
        'hors_service': {'face': '#9E9E9E', 'edge': '#424242'},  # Gris
    }
    
    # Création des éléments de la légende
    legend_elements = [
        # États des ouvrages
        Patch(facecolor='#4CAF50',  # Vert
              edgecolor='#2E7D32',
              label='En service',
              linewidth=1.5,
              alpha=0.9),
        Patch(facecolor='#F44336',  # Rouge
              edgecolor='#B71C1C',
              label='En panne',
              linewidth=1.5,
              alpha=0.9),
        Patch(facecolor='#FF9800',  # Orange
              edgecolor='#E65100',
              label='En maintenance',
              linewidth=1.5,
              alpha=0.9),
        Patch(facecolor='#9E9E9E',  # Gris
              edgecolor='#424242',
              label='Hors service',
              linewidth=1.5,
              alpha=0.9),
        
        # Ligne bleue pour les flux d'eau
        #plt.Line2D([0], [0], 
                  #color=colors['fleche_eau'], 
                  #lw=2, 
                  #label='Flux eau'),
        # Ligne marron pour les flux de boue
        #plt.Line2D([0], [0], 
                  #color=colors['fleche_boue'], 
                  #lw=2, 
                  #label='Flux boue')
    ]
    
    # Afficher la légende dans l'axe dédié
    #legend_ax.axis('off')
    
    # Créer la légende dans l'axe dédié
    #legend = legend_ax.legend(handles=legend_elements, 
                            #loc='center',
                            #**legend_style)
    
    # Ajouter un titre à la légende
    #legend.set_title("LÉGENDE DES ÉTATS", 
                   #prop={'weight': 'bold', 'size': 12, 'family': 'sans-serif'})
    
    # Ajuster l'espacement
    #plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    
    # Ajouter les étiquettes Eaux usées et Eaux épurées
    if blocs:
        first_bloc = blocs[0]
        # Déplacer plus à droite pour éviter la coupure
        #ax.text(first_bloc["x"] - 0.8, first_bloc["y"] + first_bloc["h"]/2, 
               #"Eaux usées", 
               #ha='right', va='center',
               #fontsize=10, fontweight='bold',
               #color=colors["texte_principal"],
               #bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        
        # Trouver le dernier bloc de la filière eau pour positionner Eaux épurées
        last_water_bloc = None
        for bloc in reversed(blocs):
            if bloc["type"] == "filiere_eau":
                last_water_bloc = bloc
                break
            
        # Ajouter l'étiquette Eaux épurées à droite du dernier bloc de la filière eau
        if last_water_bloc:
            pass
            #ax.text(last_water_bloc["x"] + last_water_bloc["w"] + 0.8, 
                   #last_water_bloc["y"] + last_water_bloc["h"]/2,
                   #"Eaux épurées",
                   #ha='left', va='center',
                   #fontsize=10, fontweight='bold',
                   #color=colors["texte_principal"],
                   #bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    # Ajouter l'étiquette Boues activées si nécessaire
    if "filiere_boue" in step_config and step_config["filiere_boue"]:
        # Gestion des boues primaires et secondaires
        filiere_eau = step_config.get("filiere_eau", {})
        
        # Log de débogage complet
        log_info("=== DÉBUT DEBUG ===")
        log_info(f"Contenu complet de step_config: {json.dumps(step_config, indent=2, ensure_ascii=False, default=str)}")
        log_info(f"Type de filiere_eau: {type(filiere_eau)}")
        log_info(f"Contenu de filiere_eau: {json.dumps(filiere_eau, indent=2, ensure_ascii=False, default=str)}")
        
        # Vérifier la présence et le type de boues_primaires
        if "boues_primaires" in filiere_eau:
            boues_prim = filiere_eau["boues_primaires"]
            log_info(f"Type de boues_primaires: {type(boues_prim)}")
            if isinstance(boues_prim, dict):
                log_info(f"Clés dans boues_primaires: {boues_prim.keys()}")
                if "source" in boues_prim:
                    log_info(f"Type de la source: {type(boues_prim['source'])}")
                    log_info(f"Valeur de la source: {boues_prim['source']}")
        
        # Vérifier la présence et le type de boues_secondaires
        if "boues_secondaires" in filiere_eau:
            boues_sec = filiere_eau["boues_secondaires"]
            log_info(f"Type de boues_secondaires: {type(boues_sec)}")
            if isinstance(boues_sec, dict):
                log_info(f"Clés dans boues_secondaires: {boues_sec.keys()}")
                if "source" in boues_sec:
                    log_info(f"Type de la source: {type(boues_sec['source'])}")
                    log_info(f"Valeur de la source: {boues_sec['source']}")
        
        log_info("=== FIN DEBUG ===")
        
        # Afficher les boues primaires si configuré
        if "boues_primaires" in filiere_eau and filiere_eau["boues_primaires"]:
            boues_prim = filiere_eau["boues_primaires"]
            if isinstance(boues_prim, dict) and "source" in boues_prim and "etiquette" in boues_prim:
                try:
                    source_prim = str(boues_prim["source"])
                    # Rechercher le bloc correspondant en tenant compte des sauts de ligne
                    for b in blocs:
                        if not isinstance(b, dict):
                            continue
                            
                        nom_bloc = b.get("nom")
                        if not isinstance(nom_bloc, str):
                            continue
                            
                        try:
                            nom_brut = nom_bloc.replace("\n", "").strip()
                            source_prim_clean = source_prim.replace("/", "").strip()
                            
                            if source_prim_clean == nom_brut:
                                # Afficher sous l'ouvrage source avec une flèche
                                x_pos = b["x"] + b["w"] / 2
                                y_pos = b["y"] - 0.5  # Position sous l'ouvrage
                                
                                # Dessiner la flèche verticale
                                #ax.annotate(
                                    #"",
                                    #xy=(x_pos, y_pos - 0.2),  # Pointe de la flèche
                                    #xytext=(x_pos, y_pos + 0.1),  # Début de la flèche
                                    #arrowprops=dict(
                                        #arrowstyle="-|>",
                                        #color="#8B4513",  # Marron
                                        #lw=1.5,
                                        #shrinkA=0,
                                        #shrinkB=0
                                    #),
                                    #zorder=1
                                #)
                                
                                # Afficher l'étiquette avec fond marron transparent
                                #ax.text(
                                    #x_pos,
                                    #y_pos - 0.5,  # Position sous la flèche
                                    #boues_prim["etiquette"],
                                    #ha='center',
                                    #va='top',
                                    #fontsize=10,
                                    #fontweight='normal',
                                    #color='white',
                                    #bbox=dict(
                                        #facecolor='#8B4513',  # Marron
                                        #alpha=0.8,  # Transparence
                                        #edgecolor='#5D2906',  # Marron plus foncé pour la bordure
                                        #boxstyle='round,pad=0.3',
                                        #linewidth=0.5
                                    #)
                                #)
                                break
                        except Exception as e:
                            log_avertissement(f"Erreur lors du traitement du bloc primaire {b}: {str(e)}")
                except Exception as e:
                    log_avertissement(f"Erreur lors du traitement des boues primaires: {str(e)}")
        
        # Afficher les boues secondaires si configuré
        if "boues_secondaires" in filiere_eau and filiere_eau["boues_secondaires"]:
            boues_sec = filiere_eau["boues_secondaires"]
            if isinstance(boues_sec, dict) and "source" in boues_sec and "etiquette" in boues_sec:
                try:
                    source_sec = str(boues_sec["source"])
                    # Rechercher le bloc correspondant en tenant compte des sauts de ligne
                    for b in blocs:
                        if not isinstance(b, dict):
                            continue
                            
                        nom_bloc = b.get("nom")
                        if not isinstance(nom_bloc, str):
                            continue
                            
                        try:
                            nom_brut = nom_bloc.replace("\n", "").strip()
                            source_sec_clean = source_sec.replace("/", "").strip()
                            
                            if source_sec_clean == nom_brut:
                                # Afficher sous l'ouvrage source avec une flèche
                                x_pos = b["x"] + b["w"] / 2
                                y_pos = b["y"] - 0.5  # Position sous l'ouvrage
                                
                                # Dessiner la flèche verticale
                                #ax.annotate(
                                    #"",
                                    #xy=(x_pos, y_pos - 0.2),  # Pointe de la flèche
                                    #xytext=(x_pos, y_pos + 0.1),  # Début de la flèche
                                    #arrowprops=dict(
                                        #arrowstyle="-|>",
                                        #color="#8B4513",  # Marron
                                        #lw=1.5,
                                        #shrinkA=0,
                                        #shrinkB=0
                                    #),
                                    #zorder=1
                                #)
                                
                                # Afficher l'étiquette avec fond marron transparent
                                #ax.text(
                                    #x_pos,
                                    #y_pos - 0.5,  # Position sous la flèche
                                    #boues_sec["etiquette"],
                                    #ha='center',
                                    #va='top',
                                    #fontsize=10,
                                    #fontweight='normal',
                                    #color='white',
                                    #bbox=dict(
                                        #facecolor='#8B4513',  # Marron
                                        #alpha=0.8,  # Transparence
                                        #edgecolor='#5D2906',  # Marron plus foncé pour la bordure
                                        #boxstyle='round,pad=0.3',
                                        #linewidth=0.5
                                    #)
                                #)
                                break
                        except Exception as e:
                            log_avertissement(f"Erreur lors du traitement du bloc secondaire {b}: {str(e)}")
                except Exception as e:
                    log_avertissement(f"Erreur lors du traitement des boues secondaires: {str(e)}")
