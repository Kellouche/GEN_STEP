#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import logging
from datetime import datetime

# Importer les utilitaires
from utils import get_stations_list, update_stations_cache
from gen_station import get_ouvrages_procede  # Ajout de l'import manquant

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class DiagrammeFlux:
    """Classe pour générer un diagramme de flux des ouvrages d'une station d'épuration."""
    
    def __init__(self, type_station=None):
        """Initialise le diagramme avec les paramètres par défaut."""
        # Configuration des couleurs pour chaque état
        self.couleurs_etats = {
            'en_service': '#4CAF50',           # Vert
            'en_panne': '#F44336',             # Rouge
            'en_dysfonctionnement': '#FFC107',   # Ambre
            'en_maintenance': '#FF9800',       # Orange
            'hors_service': '#9E9E9E',         # Gris
            'inexistant': '#FFFFFF',           # Blanc
            'arret_volontaire': '#B22222',    # Rouge brique
            'surcharge_sature': '#9C27B0',    # Violet
            'nouvel_ouvrage': '#03A9F4'        # Bleu
        }
        
        # Configuration de la station
        self.type_station = type_station
        self.filiere_eau = {}
        self.filiere_boue = []  # Ajout de l'attribut
        
        # Charger la configuration des types si un type de station est fourni
        if self.type_station:
            self._charger_configuration_types()
        
        # Configuration des dimensions (augmentation de la taille des blocs)
        self.largeur_bloc = 6.0  # Augmenté de 4.0 à 6.0
        self.hauteur_bloc = 1.8  # Légèrement augmenté pour les textes sur plusieurs lignes
        self.espacement = 2.0    
        self.marge_gauche = 2.0  # Augmenté pour mieux centrer
        self.marge_haut = 1.5    # Augmenté de 1.0 à 1.5
        
        # Configuration de la police
        self.police_titre = {
            'fontsize': 10,       # Augmenté de 9 à 10
            'fontweight': 'bold',
            'color': '#333333',
            'ha': 'center',
            'va': 'center',
            'wrap': True
        }
        
        self.police_etat = {
            'fontsize': 9,        # Augmenté de 8 à 9
            'color': '#555555',
            'ha': 'center',
            'va': 'center',
            'style': 'italic'
        }
        
    def _charger_configuration_types(self):
        """Charge la configuration des types depuis le fichier types.json"""
        try:
            with open('data/types.json', 'r', encoding='utf-8') as f:
                types_config = json.load(f)
                if self.type_station in types_config:
                    config_station = types_config[self.type_station]
                    self.filiere_eau = config_station.get('filiere_eau', {})
                    self.filiere_boue = config_station.get('filiere_boue', [])
                    print(f"[DEBUG] Configuration chargée - filiere_eau: {self.filiere_eau}")
                    print(f"[DEBUG] Configuration chargée - filiere_boue: {self.filiere_boue}")
        except Exception as e:
            log.error(f"Erreur lors du chargement de la configuration des types : {e}")
    
    def parser_ouvrages(self, liste_ouvrages: list) -> list:
        """
        Parse la liste des ouvrages pour extraire le nom et l'état.
        
        Args:
            liste_ouvrages: Liste des chaînes au format "Numéro. Nom de l'ouvrage - État"
            ou des dictionnaires contenant déjà les informations structurées
            
        Returns:
            Liste de dictionnaires avec 'id', 'nom' et 'etat' pour chaque ouvrage,
            ainsi que tous les champs supplémentaires présents dans l'entrée
        """
        ouvrages = []
        for i, item in enumerate(liste_ouvrages):
            if isinstance(item, dict):
                # Si l'item est déjà un dictionnaire, l'utiliser directement
                # en s'assurant qu'il a les champs requis
                ouvrage = item.copy()
                if 'id' not in ouvrage:
                    ouvrage['id'] = i + 1
                if 'nom' not in ouvrage or 'etat' not in ouvrage:
                    continue  # Ignorer les entrées invalides
                ouvrages.append(ouvrage)
            elif isinstance(item, str):
                # Traitement du format de chaîne de caractères
                if ' - ' in item:
                    # Supprimer le numéro et l'espace du début si présent
                    ligne = item
                    if ligne[0].isdigit() and '. ' in ligne:
                        ligne = ligne.split('. ', 1)[1]
                    
                    # Séparer le nom et l'état
                    parties = ligne.split(' - ', 1)
                    if len(parties) == 2:
                        nom, etat = parties
                        ouvrages.append({
                            'id': i + 1,
                            'nom': nom.strip(),
                            'etat': etat.strip()
                        })
        return ouvrages
    
    def classer_par_filiere(self, ouvrages: list) -> dict:
        """
        Répartit les ouvrages dans les différentes filières (eau, boue, etc.).
        
        Args:
            ouvrages: Liste des ouvrages à classer
            
        Returns:
            Dictionnaire des ouvrages classés par filière
        """
        filieres = {
            'pretraitement': [],
            'traitement_primaire': [],
            'traitement_secondaire': [],
            'traitement_tertiaire': [],
            'rejet': [],
            'traitement_boues': [],
            'stockage': [],
            'valorisation': [],
            'epandage': [],
            'mise_en_decharge': [],
            'incineration': [],
            'autre': []
        }
        
        # Dictionnaire de correspondance entre les noms d'ouvrages et leurs filières
        correspondance_ouvrages = {
            # Prétraitement
            'Dégrillage': 'pretraitement',
            'Dégrillage fin': 'pretraitement',
            'Dessablage/Dégraissage': 'pretraitement',
            
            # Traitement primaire
            'Décanteur primaire': 'traitement_primaire',
            'Décanteur lamellaire': 'traitement_primaire',
            
            # Traitement secondaire
            'Bassins d\'aération': 'traitement_secondaire',
            'Bassins à boues activées': 'traitement_secondaire',
            'Bassins plantés de roseaux': 'traitement_secondaire',
            'Lagune aérée': 'traitement_secondaire',
            'Clarificateur': 'traitement_secondaire',
            'Décanteur secondaire': 'traitement_secondaire',
            
            # Traitement tertiaire
            'Filtration sur sable': 'traitement_tertiaire',
            'Désinfection UV': 'traitement_tertiaire',
            
            # Traitement des boues
            'Épaississement des boues': 'traitement_boues',
            'Épaississement gravitaire': 'traitement_boues',
            'Déshydratation mécanique': 'traitement_boues',
            'Lits de séchage': 'traitement_boues',
            'Séchage naturel sur lit de séchage': 'traitement_boues',
            
            # Autres
            'Stockage': 'stockage',
            'Valorisation': 'valorisation',
            'Épandage': 'epandage',
            'Mise en décharge': 'mise_en_decharge',
            'Incinération': 'incineration',
            'Rejet': 'rejet'
        }
        
        # Dictionnaire pour les types de boues
        type_boues = {
            'Décanteur primaire': 'boues_primaires',
            'Décanteur secondaire': 'boues_secondaires'
        }
        
        for ouvrage in ouvrages:
            nom = ouvrage['nom']
            
            # Vérifier si l'ouvrage est dans la correspondance
            if nom in correspondance_ouvrages:
                filiere = correspondance_ouvrages[nom]
                
                # Ajouter le type de boues si nécessaire
                if nom in type_boues:
                    ouvrage['type'] = type_boues[nom]
                
                filieres[filiere].append(ouvrage)
            else:
                # Si l'ouvrage n'est pas reconnu, on le met dans une filière par défaut
                filieres['autre'].append(ouvrage)
        
        return filieres
    
    def calculer_positions(self, filieres: dict) -> list:
        """
        Calcule les positions des blocs dans le diagramme.
        
        Args:
            filieres: Dictionnaire des ouvrages classés par filière
            
        Returns:
            Liste des ouvrages avec leurs positions mises à jour
        """
        ouvrages_positionnes = []
        
        # Définir l'ordre des filières (de haut en bas)
        ordre_filieres = [
            'pretraitement',
            'traitement_primaire',
            'traitement_secondaire',
            'traitement_tertiaire',
            'rejet',
            'traitement_boues',
            'stockage',
            'valorisation',
            'epandage',
            'mise_en_decharge',
            'incineration',
            'autre'
        ]
        
        # Espacement entre les lignes de filières
        espacement_lignes = 3.0
        
        # Position Y initiale (première ligne en haut)
        y = 0
        
        # Pour chaque filière dans l'ordre défini
        for filiere in ordre_filieres:
            if filiere not in filieres or not filieres[filiere]:
                continue
                
            # Trier les ouvrages de la filière de gauche à droite
            ouvrages_filiere = filieres[filiere]
            
            # Position X initiale pour cette ligne (marge gauche)
            x = self.marge_gauche
            
            # Pour chaque ouvrage de la filière
            for ouvrage in ouvrages_filiere:
                # Mettre à jour les coordonnées
                ouvrage['x'] = x
                ouvrage['y'] = y
                ouvrage['largeur'] = self.largeur_bloc
                ouvrage['hauteur'] = self.hauteur_bloc
                ouvrage['filiere'] = filiere  # S'assurer que la filière est bien définie
                
                # Ajouter à la liste des ouvrages positionnés
                ouvrages_positionnes.append(ouvrage)
                
                # Décaler vers la droite pour le prochain ouvrage
                x += self.largeur_bloc + self.espacement
            
            # Ajouter le titre de la filière à gauche de la ligne
            if ouvrages_filiere:
                plt.text(
                    self.marge_gauche / 2,  # Position X (à gauche des ouvrages)
                    y + self.hauteur_bloc / 2,  # Centré verticalement sur la ligne
                    filiere.replace('_', ' ').title(),
                    ha='right',
                    va='center',
                    fontsize=10,
                    fontweight='bold',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.3')
                )
            
            # Passer à la ligne suivante (en descendant)
            y -= (self.hauteur_bloc + espacement_lignes)
        
        return ouvrages_positionnes

    def get_boues_info(self, ouvrages_positionnes):
        """
        Récupère les informations sur les boues à partir des ouvrages positionnés.
        
        Args:
            ouvrages_positionnes: Liste des ouvrages avec leurs positions
            
        Returns:
            dict: Dictionnaire contenant les informations sur les boues
        """
        boues_info = {
            'boues_primaires': None,
            'boues_secondaires': None
        }
        
        for ouvrage in ouvrages_positionnes:
            if 'boues_primaires' in ouvrage.get('type', ''):
                boues_info['boues_primaires'] = {
                    'x': ouvrage['x'],
                    'y': ouvrage['y'] - 0.5,
                    'label': 'Boues primaires',
                    'color': '#8B4513'  # Marron
                }
            elif 'boues_secondaires' in ouvrage.get('type', ''):
                boues_info['boues_secondaires'] = {
                    'x': ouvrage['x'],
                    'y': ouvrage['y'] - 0.5,
                    'label': 'Boues secondaires',
                    'color': '#8B4513'  # Marron
                }
                
        return boues_info

    def dessiner_fleches(self, ax, ouvrages_positionnes: list):
        """
        Dessine des flèches entre les ouvrages selon un flux logique.
        
        Args:
            ax: Axes matplotlib où dessiner
            ouvrages_positionnes: Liste des ouvrages avec leurs positions
        """
        if not ouvrages_positionnes:
            return
        
        # Dictionnaire pour stocker les positions des ouvrages par nom
        ouvrages_par_nom = {}
        for ouvrage in ouvrages_positionnes:
            if 'nom' in ouvrage:
                ouvrages_par_nom[ouvrage['nom']] = {
                    'x': ouvrage['x'] + ouvrage['largeur'] / 2,
                    'y': ouvrage['y'] + ouvrage['hauteur'] / 2,
                    'largeur': ouvrage['largeur'],
                    'hauteur': ouvrage['hauteur'],
                    'filiere': ouvrage.get('filiere', 'autre')
                }
        
        # Trier les ouvrages par filière
        ouvrages_par_filiere = {}
        for ouvrage in ouvrages_positionnes:
            filiere = ouvrage.get('filiere', 'autre')
            if filiere not in ouvrages_par_filiere:
                ouvrages_par_filiere[filiere] = []
            ouvrages_par_filiere[filiere].append(ouvrage)
        
        # Définir les filières d'eau (trait continu bleu) dans l'ordre du flux
        filieres_eau_ordre = [
            'pretraitement',
            'traitement_primaire',
            'traitement_secondaire', 
            'traitement_tertiaire',
            'rejet'
        ]
        
        # Style des flèches pour l'eau
        style_fleche_eau = {
            'color': '#3498db',  # Bleu
            'linestyle': '-',    # Trait continu
            'linewidth': 1.5,
            'alpha': 0.9,
            'arrowstyle': '-|>',
            'shrinkA': 0,  # Désactiver le retrait au point de départ
            'shrinkB': 0,  # Désactiver le retrait au point d'arrivée
            'connectionstyle': 'arc3,rad=0.0',  # Ligne droite sans courbure
        }
        
        # Style des flèches pour les boues
        style_fleche_boues = {
            'color': '#8B4513',  # Marron
            'linestyle': '--',   # Trait pointillé
            'linewidth': 1.5,
            'alpha': 0.8,
            'arrowstyle': '-|>',
            'shrinkA': 5,
            'shrinkB': 5,
            'connectionstyle': 'arc3,rad=0.3',  # Courbure de la flèche
        }
        
        # 1. Dessiner les flèches entre les ouvrages d'une même filière
        for filiere, ouvrages in ouvrages_par_filiere.items():
            if len(ouvrages) < 2:
                continue
                
            # Trier les ouvrages de gauche à droite
            ouvrages_tries = sorted(ouvrages, key=lambda x: x['x'])
            
            # Ne pas dessiner de flèches pour la filière boue
            if 'boue' in filiere.lower():
                continue
                
            # Pour les ouvrages sur la même ligne, flèche horizontale
            for i in range(len(ouvrages_tries) - 1):
                source = ouvrages_tries[i]
                cible = ouvrages_tries[i + 1]
                
                # Coordonnées de départ (bord droit du bloc source)
                x1 = source['x'] + source['largeur']
                y1 = source['y'] + source['hauteur'] / 2
                
                # Coordonnées d'arrivée (bord gauche du bloc cible)
                x2 = cible['x']
                y2 = cible['y'] + cible['hauteur'] / 2
                
                # Style de flèche en fonction de la filière
                if 'boue' in filiere.lower():
                    arrow_style = style_fleche_boues
                else:
                    arrow_style = style_fleche_eau
                
                # Dessiner la flèche
                ax.annotate(
                    "",
                    xy=(x2, y2),     # Point d'arrivée (pointe de la flèche)
                    xytext=(x1, y1), # Point de départ
                    arrowprops=arrow_style,
                    zorder=1  # Placer les flèches en arrière-plan
                )
        
        # 2. Dessiner les flèches entre les différentes filières d'eau
        for i in range(len(filieres_eau_ordre) - 1):
            filiere_courante = filieres_eau_ordre[i]
            filiere_suivante = filieres_eau_ordre[i + 1]
            
            # Vérifier que les deux filières existent
            if filiere_courante not in ouvrages_par_filiere or filiere_suivante not in ouvrages_par_filiere:
                continue
                
            # Prendre le dernier ouvrage de la filière courante (le plus à droite)
            derniers_ouvrages_courants = sorted(ouvrages_par_filiere[filiere_courante], key=lambda x: x['x'], reverse=True)
            if not derniers_ouvrages_courants:
                continue
            source = derniers_ouvrages_courants[0]
            
            # Prendre le premier ouvrage de la filière suivante (le plus à gauche)
            premiers_ouvrages_suivants = sorted(ouvrages_par_filiere[filiere_suivante], key=lambda x: x['x'])
            if not premiers_ouvrages_suivants:
                continue
            cible = premiers_ouvrages_suivants[0]
            
            # Coordonnées de départ (bord droit du bloc source)
            x1 = source['x'] + source['largeur']
            y1 = source['y'] + source['hauteur'] / 2
            
            # Coordonnées d'arrivée (centre du bord gauche du bloc cible)
            x2 = cible['x']
            y2 = cible['y'] + cible['hauteur'] / 2
            
            # Dessiner la flèche entre les filières
            ax.annotate(
                "",
                xy=(x2, y2),  # Point d'arrivée (haut du bloc cible)
                xytext=(x1, y1),  # Point de départ (bas du bloc source)
                arrowprops={
                    **style_fleche_eau,
                    'connectionstyle': 'arc3,rad=0.15',  # Légère courbure
                    'shrinkA': 0,  # Pas de réduction à la source
                    'shrinkB': 0,  # Pas de réduction à la cible
                },
                zorder=1
            )
        
        # 3. Dessiner les flèches pour les boues (primaire et secondaire)
        if hasattr(self, 'type_station') and hasattr(self, 'filiere_eau'):
            print(f"\n[DEBUG] Contenu de filiere_eau:")
            for key, value in self.filiere_eau.items():
                print(f"  {key}: {value}")
                
            # 3.1 Flèches des décanteurs vers l'épaississement
            boues_config = {}
            
            # Récupérer les configurations de boues si elles existent
            if hasattr(self.filiere_eau, 'get'):
                if 'boues_primaires' in self.filiere_eau:
                    boues_config['boues_primaires'] = self.filiere_eau['boues_primaires']
                if 'boues_secondaires' in self.filiere_eau:
                    boues_config['boues_secondaires'] = self.filiere_eau['boues_secondaires']
            
            # Dessiner les flèches pour chaque type de boues
            for boue_type, config in boues_config.items():
                source_nom = config.get('source')
                destination_nom = config.get('destination')
                etiquette = config.get('etiquette', 'Boues')
                
                if source_nom in ouvrages_par_nom and destination_nom in ouvrages_par_nom:
                    source = ouvrages_par_nom[source_nom]
                    destination = ouvrages_par_nom[destination_nom]
                    
                    # Coordonnées de départ (centre du bord inférieur du bloc source)
                    x1 = source['x'] + source['largeur'] / 2
                    y1 = source['y']  # Bord inférieur
                    
                    # Coordonnées d'arrivée (haut du bloc destination)
                    x2 = destination['x'] + destination['largeur'] / 2
                    # Ajuster y2 pour arriver exactement sur le bord supérieur du bloc de destination
                    y2 = destination['y'] + destination['hauteur']
                    
                    # Dessiner la flèche
                    ax.annotate(
                        "",
                        xy=(x2, y2),
                        xytext=(x1, y1),
                        arrowprops=style_fleche_boues,
                        zorder=1
                    )
                    
                    # Ajouter l'étiquette
                    label_x = source['x'] + source['largeur'] / 2
                    label_y = source['y'] - 0.8
                    
                    ax.text(
                        label_x, label_y,
                        etiquette,
                        ha='center', va='top',
                        fontsize=9,
                        bbox=dict(
                            facecolor='#8B4513',
                            alpha=0.8,
                            boxstyle='round,pad=0.3',
                            edgecolor='#5D2906',
                            linewidth=0.8
                        ),
                        color='white',
                        zorder=10
                    )
            # 3.2 Flèches pour la filière boue
            if hasattr(self, 'filiere_boue') and len(self.filiere_boue) > 1:
                print(f"\n[DEBUG] Filière boue: {self.filiere_boue}")
                
                # Le premier élément est la source (épaississement)
                source_nom = self.filiere_boue[0]
                print(f"[DEBUG] Source principale: {source_nom}")
                
                if source_nom in ouvrages_par_nom:
                    source = ouvrages_par_nom[source_nom]
                    x1 = source['x'] + source['largeur'] / 2
                    y1 = source['y']  # Bord inférieur
                    
                    # Pour chaque destination (sauf la source)
                    for dest_nom in self.filiere_boue[1:]:
                        if dest_nom in ouvrages_par_nom:
                            dest = ouvrages_par_nom[dest_nom]
                            x2 = dest['x'] + dest['largeur'] / 2
                            # Ajuster y2 pour arriver exactement sur le bord inférieur du bloc de destination
                            y2 = dest['y']  # Bord inférieur de la destination
                            
                            print(f"[DEBUG] Source: {source_nom} (x1={x1:.2f}, y1={y1:.2f})")
                            print(f"[DEBUG] Destination: {dest_nom} (x2={x2:.2f}, y2={y2:.2f})")
                            
                            # Dessiner la flèche avec une courbure réduite
                            ax.annotate(
                                "",
                                xy=(x2, y2),  # Point d'arrivée exact sur le bord inférieur
                                xytext=(x1, y1),  # Point de départ (bas du bloc source)
                                arrowprops={
                                    'arrowstyle': '->',
                                    'color': '#8B4513',  # Marron
                                    'linewidth': 1.5,
                                    'alpha': 0.8,
                                    'shrinkA': 0,  # Pas de réduction au point de départ
                                    'shrinkB': 0,  # Pas de réduction au point d'arrivée
                                    'connectionstyle': 'arc3,rad=0.15'  # Courbure très réduite (0.1 au lieu de 0.2)
                                },
                                zorder=1
                            )
                else:
                    print(f"[DEBUG] Erreur: {source_nom} non trouvé dans ouvrages_par_nom")
            else:
                print("[DEBUG] Moins de 2 ouvrages dans la filière boue")        
            
    def _formater_nom_ouvrage(self, nom: str) -> str:
        """
        Formate le nom d'un ouvrage pour un affichage optimal sur plusieurs lignes.
        
        Args:
            nom: Le nom de l'ouvrage à formater
            
        Returns:
            Le nom formaté avec des retours à la ligne
        """
        # Remplacer les tirets et barres obliques par des retours à la ligne
        separators = [' - ', ' / ', ' /', '/ ', ' -', '- ']
        for sep in separators:
            nom = nom.replace(sep, '\n')
        
        # Diviser les lignes trop longues
        lignes = []
        for ligne in nom.split('\n'):
            if len(ligne) > 20:  # Si la ligne est trop longue
                mots = ligne.split()
                nouvelle_ligne = mots[0]
                
                for mot in mots[1:]:
                    if len(nouvelle_ligne) + len(mot) < 15:  # Limite de 15 caractères par ligne
                        nouvelle_ligne += ' ' + mot
                    else:
                        lignes.append(nouvelle_ligne)
                        nouvelle_ligne = mot
                
                if nouvelle_ligne:
                    lignes.append(nouvelle_ligne)
            else:
                lignes.append(ligne)
        
        return '\n'.join(lignes)
    
    def generer_diagramme(self, liste_ouvrages: list, titre: str, destination: str = None):
        """
        Génère le diagramme de flux avec les ouvrages donnés.
        
        Args:
            liste_ouvrages: Liste des ouvrages à afficher
            titre: Titre du diagramme (déjà formaté avec la date)
            destination: Destination finale des eaux épurées (ex: "Rejet", "Réutilisation") (optionnel)
        """
        # Fermer toutes les figures existantes pour éviter les figures indésirées
        plt.close('all')
        
        # Afficher le titre pour le débogage
        print(f"[DEBUG] Titre reçu dans generer_diagramme : {titre}")
        
        # Préparer les données
        ouvrages = self.parser_ouvrages(liste_ouvrages)
        filieres = self.classer_par_filiere(ouvrages)
        ouvrages_positionnes = self.calculer_positions(filieres)
        
        # Créer et afficher le diagramme
        fig, ax = self.dessiner_diagramme(ouvrages_positionnes, destination)
        
        # Diviser le titre en lignes pour un meilleur affichage
        lignes_titre = titre.split('\n')
        
        # Ajouter le titre principal avec un espacement amélioré
        plt.suptitle(
            '\n'.join(lignes_titre),
            fontsize=14,
            fontweight='bold',
            y=0.99,  # Ajuster légèrement vers le haut
            verticalalignment='top',
            horizontalalignment='center',
            linespacing=1.5  # Espacement des lignes pour une meilleure lisibilité
        )
        
        # Ajuster l'espacement pour éviter que le titre ne soit coupé
        plt.subplots_adjust(top=0.85)
        
        # Afficher la figure
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Réserver de l'espace pour le titre
        plt.show()
    
    def dessiner_diagramme(self, ouvrages_positionnes: list, destination: str = None):
        """
        Dessine le diagramme de flux avec les ouvrages positionnés.
        
        Args:
            ouvrages_positionnes: Liste des ouvrages avec leurs positions
            destination: Destination finale des eaux épurées (optionnel)
            
        Returns:
            tuple: Figure et axes matplotlib
        """
        # Créer une seule figure avec un numéro spécifique
        fig = plt.figure(1, figsize=(20, 12), dpi=100)
        plt.clf()  # Efface la figure existante
        ax = fig.add_subplot(111)
        
        # Déterminer les limites automatiquement
        if ouvrages_positionnes:
            x_vals = [o['x'] for o in ouvrages_positionnes]
            y_vals = [o['y'] for o in ouvrages_positionnes]
            
            # Ajouter des marges
            x_margin = 1.0
            y_margin = 1.0
            x_min = min(x_vals) - x_margin
            x_max = max(x_vals) + self.largeur_bloc + x_margin
            y_min = min(y_vals) - y_margin
            y_max = max(y_vals) + self.hauteur_bloc + y_margin
        else:
            x_min, x_max = 0, 20
            y_min, y_max = -20, 2

        # Dessiner chaque ouvrage
        for ouvrage in ouvrages_positionnes:
            # Récupérer la couleur en fonction de l'état
            etat = ouvrage['etat']
            couleur = self.couleurs_etats.get(etat, '#FFFFFF')
            
            # Dessiner le rectangle de l'ouvrage avec des coins arrondis
            rect = patches.FancyBboxPatch(
                (ouvrage['x'], ouvrage['y']), 
                ouvrage['largeur'], 
                ouvrage['hauteur'],
                boxstyle="round,pad=0.1,rounding_size=0.2",
                linewidth=1.5,
                edgecolor='#333333',
                facecolor=couleur,
                alpha=0.95,
                zorder=2
            )
            ax.add_patch(rect)
            
            # Formater le nom de l'ouvrage
            nom_formate = self._formater_nom_ouvrage(ouvrage['nom'])
            
            # Afficher le nom de l'ouvrage
            text = ax.text(
                ouvrage['x'] + ouvrage['largeur']/2,
                ouvrage['y'] + ouvrage['hauteur']/2,
                nom_formate,
                ha='center',
                va='center',
                fontsize=9,
                wrap=True,
                bbox=dict(
                    facecolor='white',
                    alpha=0.7,
                    boxstyle='round,pad=0.5',
                    edgecolor='none'
                )
            )
        
        # Dessiner les flèches entre les ouvrages
        self.dessiner_fleches(ax, ouvrages_positionnes)
        
        # Trier les ouvrages par position x pour déterminer le premier et le dernier
        ouvrages_tries = sorted(ouvrages_positionnes, key=lambda o: o['x'])
        
        if ouvrages_tries:
            # Ajouter 'Eaux usées' au-dessus du premier ouvrage
            premier_ouvrage = ouvrages_tries[0]
            x_label = premier_ouvrage['x'] + premier_ouvrage['largeur']/2
            y_label = premier_ouvrage['y'] + premier_ouvrage['hauteur'] + 2.0
            
            # Flèche verticale vers le bas
            ax.annotate(
                "",
                xy=(x_label, premier_ouvrage['y'] + premier_ouvrage['hauteur'] + 0.1),
                xytext=(x_label, y_label - 0.5),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5, shrinkA=0, shrinkB=0),
                zorder=1
            )
            
            # Étiquette 'Eaux usées'
            ax.text(
                x_label, y_label,
                'Eaux usées',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold',
                color='black',
                bbox=dict(facecolor='white', alpha=0.0, boxstyle='round,pad=0.5', linewidth=0)
            )
            
            # Trouver le dernier ouvrage du traitement secondaire
            dernier_ouvrage_secondaire = None
            for ouvrage in reversed(ouvrages_tries):
                if any(nom in ouvrage['nom'] for nom in ['Décanteur secondaire', 'Clarificateur', 'Bassin aération']):
                    dernier_ouvrage_secondaire = ouvrage
                    break
            
            # Si on a trouvé un ouvrage du traitement secondaire, on l'utilise
            # Sinon, on prend le dernier ouvrage
            dernier_ouvrage = dernier_ouvrage_secondaire if dernier_ouvrage_secondaire else ouvrages_tries[-1]
            
            # Ajouter 'Eaux épurées' après le dernier ouvrage
            x_label = dernier_ouvrage['x'] + dernier_ouvrage['largeur'] + 3.0  # Augmenté de 2.0 à 5.0 pour correspondre aux 'Eaux usées'
            y_label = dernier_ouvrage['y'] + dernier_ouvrage['hauteur']/2
            
            # Flèche horizontale vers la droite
            ax.annotate(
                "",
                xy=(x_label - 1.5, y_label),
                xytext=(dernier_ouvrage['x'] + dernier_ouvrage['largeur'] + 0.1, y_label),
                arrowprops=dict(arrowstyle='->', color='blue', lw=1.5, shrinkA=0, shrinkB=0),
                zorder=1
            )
            
        # Styles pour les différentes destinations
        styles_destination = {
            'Rejet': {'color': '#1f77b4', 'icon': '🌊', 'style': 'normal'},  # Bleu avec icône vague
            'Réutilisation': {'color': '#2ca02c', 'icon': '♻️', 'style': 'italic'},  # Vert avec icône recyclage
            'Irrigation': {'color': '#8c564b', 'icon': '🌱', 'style': 'normal'},  # Marron avec icône plante
        }

        # Déterminer le style à utiliser
        style = styles_destination.get(destination, {'color': '#666666', 'icon': '➡️', 'style': 'normal'})

        # Afficher l'étiquette 'Eaux épurées'
        ax.text(
            x_label - 1, y_label,
            'Eaux épurées',
            ha='left',
            va='center',
            fontsize=10,
            fontweight='bold',
            color='blue',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2.0),
            zorder=5
        )

        # Afficher la destination avec style
        if destination:
            ax.text(
                x_label + 2.5,  # Décalé à droite de 'Eaux épurées'
                y_label,
                f"{style['icon']} {destination}",
                ha='left',
                va='center',
                fontsize=10,
                fontweight='bold',
                color=style['color'],
                fontstyle=style['style'],
                bbox=dict(
                    facecolor='white',
                    alpha=0.9,
                    edgecolor=style['color'],
                    boxstyle='round,pad=0.3',
                    linewidth=1
                ),
                zorder=5
            )    
        
        # Ajouter la légende
        self.ajouter_legende(ax)
        
        # Configurer l'aspect du graphique
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axis('off')
        
        # Ajuster le layout pour laisser de l'espace pour le titre et la légende
        plt.tight_layout(rect=[0, 0.05, 1, 0.97])
        
        # Afficher en plein écran
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
        
        # Ne pas afficher la figure ici, laisser la méthode appelante gérer l'affichage
        return fig, ax
    
    def ajouter_legende(self, ax):
        """
        Ajoute une légende pour les états des ouvrages dans le coin supérieur droit.
        """
        # Créer les éléments de la légende
        legend_elements = [
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='En service',
                markerfacecolor=self.couleurs_etats['en_service'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='En panne',
                markerfacecolor=self.couleurs_etats['en_panne'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='En dysfonctionnement',
                markerfacecolor=self.couleurs_etats['en_dysfonctionnement'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='En maintenance',
                markerfacecolor=self.couleurs_etats['en_maintenance'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='Hors service',
                markerfacecolor=self.couleurs_etats['hors_service'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='Inexistant',
                markerfacecolor=self.couleurs_etats['inexistant'],
                markersize=12,
                markeredgecolor='#000000',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='Arrêt volontaire',
                markerfacecolor=self.couleurs_etats['arret_volontaire'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='Surchargé / Saturé',
                markerfacecolor=self.couleurs_etats['surcharge_sature'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            ),
            plt.Line2D(
                [0], [0],
                marker='s',
                color='w',
                label='Nouvel ouvrage',
                markerfacecolor=self.couleurs_etats['nouvel_ouvrage'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            )
        ]
        
        # Ajouter une légende pour les flèches des filières
        legend_elements.extend([
            plt.Line2D(
                [0], [0],
                color='#3498db',  # Bleu
                lw=2,
                label='Filière Eau',
                linestyle='-'
            ),
            plt.Line2D(
                [0], [0],
                color='#8B4513',  # Marron
                lw=2,
                label='Filière Boues',
                linestyle='--'
            )
        ])
        
        # Créer la légende avec un fond blanc et une bordure
        legend = ax.legend(
            handles=legend_elements,
            title="Légende",
            title_fontsize=10,
            fontsize=9,
            loc='upper left',
            bbox_to_anchor=(1.02, 1),  # Décalage vers la droite (x=1.02) et en haut (y=1)
            borderaxespad=0.5,
            frameon=True,
            framealpha=0.9,
            edgecolor='#dddddd',
            facecolor='white'
        )
        
        # Ajuster la position du titre de la légende
        legend.get_title().set_fontweight('bold')
        legend.get_title().set_fontsize(10)
        
        # Ajouter un cadre arrondi à la légende
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5', rounding_size=0.5)
        frame.set_linewidth(1.2)
        
        # Ajouter une ombre portée à la légende
        from matplotlib.patches import FancyBboxPatch
        
        # Créer un rectangle avec des coins arrondis pour l'ombre
        shadow = FancyBboxPatch(
            (legend.get_bbox_to_anchor().x0 + 0.02, legend.get_bbox_to_anchor().y0 - 0.02),
            legend.get_bbox_to_anchor().width,
            legend.get_bbox_to_anchor().height,
            transform=ax.transAxes,
            facecolor='black',
            alpha=0.1,
            zorder=-1,
            boxstyle='round,pad=0.5,rounding_size=0.5',
            edgecolor='none'  # Pas de bordure pour l'ombre
        )
        ax.add_patch(shadow)
    
def get_station_etat(station_id, station_nom=None):
    """
    Récupère l'état d'une station à partir de son ID.
    
    Args:
        station_id (str): ID de la station
        station_nom (str, optional): Nom de la station pour les logs
        
    Returns:
        tuple: (etat_equipements, date_maj) ou (None, None) en cas d'erreur
    """
    try:
        if not os.path.exists('data/etat_station.json'):
            log.error("Le fichier etat_station.json n'existe pas.")
            return None, None
            
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats_data = json.load(f)

        if not isinstance(etats_data, dict):
            log.error("Le fichier etat_station.json n'est pas un dictionnaire.")
            return None, None

        # Récupérer les états pour la station spécifiée
        etats_station = etats_data.get(station_id, [])
        
        if not etats_station:
            log.warning(f"Aucun état trouvé pour la station {station_nom or station_id}")
            return None, None
            
        # Trier par date (la plus récente en premier)
        etats_station.sort(key=lambda x: x.get('date_maj', x.get('date', '')), reverse=True)
        
        dernier_etat = etats_station[0]
        return dernier_etat.get('etat_ouvrages', {}), dernier_etat.get('date_maj')
        
    except Exception as e:
        log.error(f"Erreur lors de la récupération de l'état de la station: {e}")
        return None, None

def get_toutes_les_mises_a_jour(station_id):
    """
    Récupère toutes les mises à jour disponibles pour une station donnée.
    
    Args:
        station_id (str): ID de la station
        
    Returns:
        list: Liste des mises à jour triées par date (la plus récente en premier)
    """
    try:
        with open('data/etat_station.json', 'r', encoding='utf-8') as f:
            etats_data = json.load(f)

        if not isinstance(etats_data, dict):
            log.error("Le fichier etat_station.json n'est pas un dictionnaire.")
            return []
            
        # Récupérer les mises à jour pour la station spécifiée
        mises_a_jour = etats_data.get(station_id, [])
        
        # S'assurer que c'est toujours une liste
        if isinstance(mises_a_jour, dict):
            mises_a_jour = [mises_a_jour]

        # Trier par date (la plus récente en premier)
        if mises_a_jour:
            mises_a_jour.sort(key=lambda x: x.get('date_maj', ''), reverse=True)
        
        return mises_a_jour
        
    except FileNotFoundError:
        log.error("Fichier etat_station.json introuvable")
        return []
    except json.JSONDecodeError:
        log.error("Erreur de lecture du fichier etat_station.json")
        return []
    except Exception as e:
        log.error(f"Erreur lors de la récupération des mises à jour: {e}")
        return []

def select_station_interactive():
    """Permet à l'utilisateur de sélectionner une station de manière interactive."""
    try:
        stations = get_stations_list()
        
        if not stations:
            log.error("Aucune station trouvée dans le fichier stations.json")
            return None
        
        print("\n=== Liste des stations disponibles ===")
        for i, station in enumerate(stations, 1):
            print(f"{i}. {station.get('nom', 'Nom inconnu')} (ID: {station.get('id', 'N/A')})")
        
        while True:
            try:
                choix = input("\nEntrez le numéro de la station (ou 'q' pour quitter) : ").strip()
                if choix.lower() == 'q':
                    return None
                
                choix = int(choix) - 1
                if 0 <= choix < len(stations):
                    return stations[choix]
                print(f"Veuillez entrer un nombre entre 1 et {len(stations)}")
            except ValueError:
                print("Veuillez entrer un numéro valide.")
    except Exception as e:
        log.error(f"Erreur lors de la sélection de la station: {e}")
        return None

def generer_diagramme_station():
    """Fonction principale pour générer le diagramme d'une station sélectionnée."""
    try:
        # Sélectionner une station de manière interactive
        station = select_station_interactive()
        if not station:
            print("\033[1;33m❌ Aucune station sélectionnée. Retour au menu principal.\033[0m")
            return

        # Récupérer les informations de la station
        nom_station = station.get('nom', 'Station inconnue')
        type_procede = station.get('type_procede', 'Inconnu')
        
        # Afficher l'en-tête
        print(f"\n\033[1;34mGÉNÉRATION DU DIAGRAMME\033[0m")
        print("-" * 40)
        print(f"Station: {nom_station}")
        print(f"Type de procédé: {type_procede}")
        
        # Vérifier si le type de procédé est valide
        if not type_procede or type_procede == 'Inconnu':
            raise ValueError("Le type de procédé n'est pas défini pour cette station.")
        
        # Récupérer toutes les mises à jour disponibles pour cette station
        mises_a_jour = get_toutes_les_mises_a_jour(station['id'])
        
        if not mises_a_jour:
            print("\033[1;33m⚠️  Aucune mise à jour trouvée pour cette station.\033[0m")
            return
        
        # Si une seule mise à jour, on l'utilise directement
        if len(mises_a_jour) == 1:
            etat_ouvrages = mises_a_jour[0].get('etat_ouvrages', {})
            date_maj = mises_a_jour[0].get('date_maj', 'Date inconnue')
        else:
            # Afficher la liste des mises à jour disponibles
            print("\n\033[1mMises à jour disponibles :\033[0m")
            for i, maj in enumerate(mises_a_jour, 1):
                date_maj = maj.get('date_maj', 'Date inconnue')
                print(f"{i}. {date_maj}")
            
            # Demander à l'utilisateur de choisir
            while True:
                try:
                    choix = input("\nEntrez le numéro de la mise à jour à afficher (ou 'q' pour quitter) : ").strip()
                    if choix.lower() == 'q':
                        return
                    
                    choix = int(choix) - 1
                    if 0 <= choix < len(mises_a_jour):
                        break
                        
                    print("\033[1;31m❌ Numéro invalide. Veuillez réessayer.\033[0m")
                except ValueError:
                    print("\033[1;31m❌ Veuillez entrer un numéro valide.\033[0m")
            
            etat_ouvrages = mises_a_jour[choix].get('etat_ouvrages', {})
            date_maj = mises_a_jour[choix].get('date_maj', 'Date inconnue')
        
        # Récupérer la liste des ouvrages pour ce type de procédé
        try:
            # Charger les données des types de procédés
            with open('data/types.json', 'r', encoding='utf-8') as f:
                types_data = json.load(f)
            
            # Récupérer les ouvrages sous forme de dictionnaire d'états
            etats_ouvrages = get_ouvrages_procede(type_procede, types_data)
            if not etats_ouvrages:
                raise ValueError(f"Aucun ouvrage trouvé pour le type de procédé: {type_procede}")
            
            # Mettre à jour les états avec les valeurs actuelles
            for nom_ouvrage, etat in etat_ouvrages.items():
                if nom_ouvrage in etats_ouvrages:
                    etats_ouvrages[nom_ouvrage] = etat
            
            # Convertir le dictionnaire d'états en liste d'ouvrages formatée
            ouvrages = [{
                'id': i + 1,
                'nom': nom,
                'etat': etat,
                'etat_affiche': etat.replace('_', ' ').capitalize() if etat in ['en_service', 'en_panne', 'en_maintenance', 'hors_service', 'inexistant'] else etat
            } for i, (nom, etat) in enumerate(etats_ouvrages.items())]
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des ouvrages: {str(e)}")
        
        # Créer le titre du diagramme avec la date de mise à jour
        type_procede_formate = type_procede.replace('_', ' ').upper()
        
        # Formater la date pour l'affichage
        if date_maj and date_maj != "Date inconnue":
            try:
                # Extraire la date du format "YYYY-MM-DD HH:MM:SS"
                date_part = date_maj.split(' ')[0]  # Prendre uniquement la partie date
                date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                date_formatee = date_obj.strftime('%d/%m/%Y')
                
                # Créer le titre avec la date formatée
                titre = f"STEP {nom_station} | Type de procédé : {type_procede_formate}\nMise à jour du {date_formatee}"
                print(f"[DEBUG] Date formatée pour le titre : {date_formatee}")
            except Exception as e:
                print(f"\033[1;33m⚠️  Erreur de format de date: {e}. Utilisation de la date brute: {date_maj}\033[0m")
                titre = f"STEP {nom_station} | Type de procédé : {type_procede_formate}\nMise à jour du {date_maj}"
        else:
            titre = f"STEP {nom_station} | Type de procédé : {type_procede_formate}\nDate de mise à jour inconnue"
        
        print(f"[DEBUG] Titre complet : {titre}")
        
        # Créer une instance du diagramme et générer le diagramme
        try:
            diagramme = DiagrammeFlux(type_station=type_procede)
            diagramme.generer_diagramme(ouvrages, titre, destination="Rejet")
            print("\n\033[1;32m✅ Diagramme généré avec succès !\033[0m")
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du diagramme: {str(e)}")
        
    except KeyboardInterrupt:
        print("\n\033[1;33m❌ Opération annulée par l'utilisateur.\033[0m")
    except Exception as e:
        print(f"\n\033[1;31m❌ Erreur: {str(e)}\033[0m")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour continuer...")