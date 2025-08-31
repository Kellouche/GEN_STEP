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

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class DiagrammeFlux:
    """Classe pour générer un diagramme de flux des ouvrages d'une station d'épuration."""
    
    def __init__(self, type_station=None):
        """Initialise le diagramme avec les paramètres par défaut."""
        # Configuration des couleurs pour chaque état
        self.couleurs_etats = {
            'en_service': '#4CAF50',     # Vert
            'en_panne': '#F44336',       # Rouge
            'en_maintenance': '#FF9800', # Orange
            'hors_service': '#9E9E9E',   # Gris
            'inexistant': '#FFFFFF',     # Blanc
            'Nouvel équipement': '#03A9F4'  # Bleu pour les nouveaux équipements
        }
        
        # Configuration de la station
        self.type_station = type_station
        self.filiere_eau = {}
        
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
                    self.filiere_eau = types_config[self.type_station].get('filiere_eau', {})
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
            'shrinkA': 5,
            'shrinkB': 5,
            'connectionstyle': 'arc3,rad=0.0',
        }
        
        # 1. Dessiner les flèches entre les ouvrages d'une même filière
        for filiere, ouvrages in ouvrages_par_filiere.items():
            if len(ouvrages) < 2:
                continue
                
            # Trier les ouvrages de gauche à droite
            ouvrages_tries = sorted(ouvrages, key=lambda x: x['x'])
            
            # Définir le style des flèches en fonction de la filière
            if filiere in filieres_eau_ordre:
                arrow_style = style_fleche_eau
            else:
                # Style pour les boues (flèches courbées en marron)
                arrow_style = {
                    'color': '#8B4513',  # Marron
                    'linestyle': '--',   # Trait pointillé
                    'linewidth': 1.5,
                    'alpha': 0.8,
                    'arrowstyle': '-|>',
                    'shrinkA': 5,
                    'shrinkB': 5,
                    'connectionstyle': 'arc3,rad=0.3',
                }
            
            # Dessiner les flèches entre les ouvrages consécutifs de la même filière
            for i in range(len(ouvrages_tries) - 1):
                source = ouvrages_tries[i]
                cible = ouvrages_tries[i + 1]
                
                # Coordonnées de départ (centre du bord droit du bloc source)
                x1 = source['x'] + source['largeur']
                y1 = source['y'] + source['hauteur'] / 2
                
                # Coordonnées d'arrivée (centre du bord gauche du bloc cible)
                x2 = cible['x']
                y2 = cible['y'] + cible['hauteur'] / 2
                
                # Dessiner la flèche
                ax.annotate(
                    "",
                    xy=(x2, y2),  # Point d'arrivée (pointe de la flèche)
                    xytext=(x1, y1),  # Point de départ
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
            
            # Coordonnées de départ (bas du bloc source)
            x1 = source['x'] + source['largeur'] / 2
            y1 = source['y'] - 0.5
            
            # Coordonnées d'arrivée (haut du bloc cible)
            x2 = cible['x'] + cible['largeur'] / 2
            y2 = cible['y'] + cible['hauteur'] + 0.5
            
            # Dessiner la flèche entre les filières
            ax.annotate(
                "",
                xy=(x2, y2),  # Point d'arrivée (haut du bloc cible)
                xytext=(x1, y1),  # Point de départ (bas du bloc source)
                arrowprops={
                    **style_fleche_eau,
                    'connectionstyle': 'arc3,rad=0.2',  # Légère courbure
                    'shrinkA': 0,  # Pas de réduction à la source
                    'shrinkB': 0,  # Pas de réduction à la cible
                },
                zorder=1
            )
        
        # 3. Dessiner les flèches pour les boues (primaire et secondaire)
        if hasattr(self, 'type_station') and hasattr(self, 'filiere_eau'):
            boues_config = {}
            
            # Vérifier si on a des configurations de boues dans la filière eau
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
                    
                    # Coordonnées de départ (bas du bloc source)
                    x1 = source['x'] + source['largeur'] / 2
                    y1 = source['y'] - 0.5
                    
                    # Coordonnées d'arrivée (haut du bloc destination)
                    x2 = destination['x'] + destination['largeur'] / 2
                    y2 = destination['y'] + destination['hauteur'] + 0.5
                    
                    # Dessiner la flèche courbée en marron
                    ax.annotate(
                        "",
                        xy=(x2, y2),  # Point d'arrivée
                        xytext=(x1, y1),  # Point de départ
                        arrowprops={
                            'arrowstyle': '-|>',
                            'color': '#8B4513',  # Marron
                            'linestyle': '--',   # Trait pointillé
                            'linewidth': 1.5,
                            'alpha': 0.8,
                            'shrinkA': 5,
                            'shrinkB': 5,
                            'connectionstyle': 'arc3,rad=0.3',  # Courbure de la flèche
                        },
                        zorder=1
                    )
                    
                    # Positionner l'étiquette sous l'ouvrage source, décalée vers la gauche
                    label_x = source['x'] - 1.5  # Décalage vers la gauche
                    label_y = source['y'] - 0.8  # Position sous l'ouvrage
                    
                    # Ajouter une flèche de l'étiquette vers le bas de l'ouvrage source
                    ax.annotate(
                        "",
                        xy=(source['x'] + source['largeur']/2, source['y']),  # Point d'arrivée (bas de l'ouvrage)
                        xytext=(label_x + 1.0, label_y + 0.3),  # Point de départ (proche de l'étiquette)
                        arrowprops={
                            'arrowstyle': '->',
                            'color': '#8B4513',
                            'linewidth': 1.0,
                            'alpha': 0.8,
                            'shrinkA': 0,
                            'shrinkB': 5,
                        },
                        zorder=1
                    )
                    
                    # Ajouter l'étiquette
                    ax.text(
                        label_x,
                        label_y,
                        etiquette,
                        color='#8B4513',
                        fontsize=9,
                        fontweight='bold',
                        ha='left',
                        va='top',
                        bbox=dict(
                            facecolor='white', 
                            alpha=0.9, 
                            edgecolor='#8B4513', 
                            boxstyle='round,pad=0.2',
                            linewidth=0.8
                        ),
                        zorder=10
                    )
        
        # 4. Ajouter l'étiquette "Eaux usées" plus haut au-dessus du premier bloc de prétraitement
        if 'pretraitement' in ouvrages_par_filiere and ouvrages_par_filiere['pretraitement']:
            premier_bloc = min(ouvrages_par_filiere['pretraitement'], key=lambda x: x['x'])
            x = premier_bloc['x'] + premier_bloc['largeur'] / 2
            y = premier_bloc['y'] + premier_bloc['hauteur'] + 0.8  # Position plus haute
            
            # Flèche plus longue pointant vers le bas depuis l'ouvrage source
            ax.annotate(
                "",
                xy=(x, premier_bloc['y'] + premier_bloc['hauteur']),  # Point d'arrivée (haut du bloc)
                xytext=(x, y),  # Point de départ (au niveau du texte)
                arrowprops={
                    'arrowstyle': '-|>',
                    'color': '#3498db',  # Bleu
                    'linestyle': '-',
                    'linewidth': 1.5,
                    'alpha': 0.9,
                    'shrinkA': 0,
                    'shrinkB': 0,
                },
                zorder=1
            )
            
            # Texte "Eaux usées" plus haut
            ax.text(
                x, y + 0.3, 'Eaux usées',  # Déplacé plus haut avec +0.3
                color='#3498db',
                fontsize=8,
                ha='center',
                va='bottom',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')
            )
        
        # 5. Ajouter l'étiquette "Eaux épurées" sur le côté droit du dernier bloc du traitement secondaire
        if 'traitement_secondaire' in ouvrages_par_filiere and ouvrages_par_filiere['traitement_secondaire']:
            dernier_bloc = max(ouvrages_par_filiere['traitement_secondaire'], key=lambda x: x['x'])
            
            # Coordonnées de la flèche
            x = dernier_bloc['x'] + dernier_bloc['largeur'] + 1.0  # Augmenté pour allonger la flèche
            y = dernier_bloc['y'] + dernier_bloc['hauteur'] / 2
            
            # Flèche horizontale plus longue partant du bloc vers la droite
            ax.annotate(
                "",
                xy=(x - 0.3, y),  # Point d'arrivée (juste avant le texte)
                xytext=(dernier_bloc['x'] + dernier_bloc['largeur'], y),  # Point de départ (bord droit du bloc)
                arrowprops={
                    'arrowstyle': '-|>',
                    'color': '#3498db',  # Bleu
                    'linestyle': '-',
                    'linewidth': 1.5,
                    'alpha': 0.9,
                    'shrinkA': 0,
                    'shrinkB': 0,
                },
                zorder=1
            )
            
            # Texte "Eaux épurées" à droite de la flèche
            ax.text(
                x, y, 'Eaux épurées',
                color='#3498db',
                fontsize=8,
                ha='left',
                va='center',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2')
            )
        
        # Le reste de la méthode reste inchangé...
        # (conserver le code existant pour les boues, les étiquettes, etc.)
    
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
    
    def generer_diagramme(self, liste_ouvrages: list, titre: str):
        """
        Génère le diagramme de flux avec les ouvrages donnés.
        
        Args:
            liste_ouvrages: Liste des ouvrages formatés
            titre: Titre du diagramme (déjà formaté)
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
        fig, ax = self.dessiner_diagramme(ouvrages_positionnes)
        
        # Ajouter le titre principal avec un espacement amélioré
        plt.suptitle(
            titre,
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
    
    def dessiner_diagramme(self, ouvrages_positionnes: list):
        """
        Dessine le diagramme de flux avec les ouvrages positionnés.
        
        Args:
            ouvrages_positionnes: Liste des ouvrages avec leurs positions
            
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
                label='Nouvel équipement',
                markerfacecolor=self.couleurs_etats['Nouvel équipement'],
                markersize=12,
                markeredgecolor='#333333',
                markeredgewidth=1
            )
        ]
        
        # Ajouter une légende pour les flèches des filières
        legend_elements.extend([
            plt.Line2D(
                [0], [0],
                color='#3498db',
                lw=2,
                label='Filière Eau',
                linestyle='-'
            ),
            plt.Line2D(
                [0], [0],
                color='#8B4513',
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
            etats = json.load(f)
            
        # Recherche des états pour cette station
        etats_station = [e for e in etats if e.get('station_id') == station_id]
        
        if not etats_station:
            log.warning(f"Aucun état trouvé pour la station {station_nom or station_id}")
            return None, None
            
        # Trier par date (la plus récente en premier)
        etats_station.sort(key=lambda x: x.get('date_maj', x.get('date', '')), reverse=True)
        
        return etats_station[0].get('etat_ouvrages', {}), etats_station[0].get('date_maj')
        
    except Exception as e:
        log.error(f"Erreur lors de la récupération de l'état de la station: {e}")
        return None, None

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
    print("\n=== Générateur de diagramme de flux des stations d'épuration ===")
    
    try:
        # Sélection de la station
        station = select_station_interactive()
        if not station:
            log.info("Aucune station sélectionnée. Retour au menu principal.")
            return
        
        print(f"\nStation sélectionnée : {station.get('nom')}")
        
        # Récupérer le type de procédé de la station
        type_procede = station.get('type_procede', 'boues_activées')
        
        # Initialiser le diagramme avec le type de procédé
        diagramme = DiagrammeFlux(type_station=type_procede)
        
        # Récupérer toutes les mises à jour disponibles pour cette station
        try:
            with open('data/etat_station.json', 'r', encoding='utf-8') as f:
                etats = json.load(f)
                mises_a_jour = [e for e in etats if e.get('station_id') == station['id']]
                
                if not mises_a_jour:
                    log.error("Aucune mise à jour trouvée pour cette station.")
                    return
                    
                # Trier les mises à jour par date (la plus récente en premier)
                mises_a_jour.sort(key=lambda x: x.get('date_maj', x.get('date', '')), reverse=True)
                
                # Si une seule mise à jour, on l'utilise directement
                if len(mises_a_jour) == 1:
                    etat_equipements = mises_a_jour[0].get('etat_ouvrages', {})
                    date_maj = mises_a_jour[0].get('date_maj', 'Date inconnue')
                    print(f"\nUne seule mise à jour disponible : {date_maj}")
                else:
                    # Afficher la liste des mises à jour disponibles
                    print("\nPlusieurs mises à jour sont disponibles pour cette station :")
                    for i, maj in enumerate(mises_a_jour, 1):
                        date_maj = maj.get('date_maj', 'Date inconnue')
                        print(f"{i}. {date_maj}")
                    
                    # Demander à l'utilisateur de choisir
                    while True:
                        try:
                            choix = input("\nEntrez le numéro de la mise à jour à visualiser (ou 'q' pour quitter) : ")
                            if choix.lower() == 'q':
                                return
                            choix_idx = int(choix) - 1
                            if 0 <= choix_idx < len(mises_a_jour):
                                break
                            print("Numéro invalide. Veuillez réessayer.")
                        except ValueError:
                            print("Veuillez entrer un numéro valide.")
                    
                    etat_equipements = mises_a_jour[choix_idx].get('etat_ouvrages', {})
                    date_maj = mises_a_jour[choix_idx].get('date_maj', 'Date inconnue')
                    print(f"\nMise à jour sélectionnée : {date_maj}")
                    
                if not etat_equipements:
                    log.error("Aucun équipement trouvé pour cette mise à jour.")
                    return
                
                # Formater la date pour l'affichage
                date_formatee = date_maj  # Par défaut, utiliser la date telle quelle
                try:
                    # Essayer de parser la date avec le format complet (avec l'heure)
                    if ' ' in date_maj:
                        dt = datetime.strptime(date_maj, '%Y-%m-%d %H:%M:%S')
                        date_formatee = dt.strftime('%d/%m/%Y')
                    # Essayer avec juste la date
                    else:
                        dt = datetime.strptime(date_maj, '%Y-%m-%d')
                        date_formatee = dt.strftime('%d/%m/%Y')
                except (ValueError, AttributeError) as e:
                    log.warning(f"Format de date non reconnu : {date_maj}. Utilisation de la date brute. Erreur : {e}")
                
                # Préparer la liste des ouvrages formatée avec l'ID de la station
                print("\nPréparation du diagramme...")
                liste_ouvrages = []
                for i, (nom_ouvrage, etat) in enumerate(etat_equipements.items(), 1):
                    # Créer un dictionnaire pour chaque ouvrage avec les champs requis
                    ouvrage = {
                        'id': i,
                        'nom': nom_ouvrage,
                        'etat': etat,
                        'etat_affiche': etat.replace('_', ' ').capitalize() if etat in ['en_service', 'en_panne', 'en_maintenance', 'hors_service', 'inexistant'] else etat,
                        'station_id': station['id']
                    }
                    liste_ouvrages.append(ouvrage)
                
                # Générer le diagramme
                try:
                    print("Génération du diagramme en cours...")
                    
                    # Créer le titre formaté avec la date formatée
                    nom_station = f"STEP {station.get('nom', 'inconnue')}"
                    type_procede_affichage = type_procede.replace('_', ' ').upper()
                    titre_complet = f"{nom_station} - {type_procede_affichage}\nDernière mise à jour : {date_formatee}"
                    
                    # Générer et afficher le diagramme
                    diagramme.generer_diagramme(liste_ouvrages, titre_complet)
                    print("\nDiagramme généré avec succès !")
                    
                except Exception as e:
                    log.error(f"Erreur lors de la génération du diagramme : {e}")
                    import traceback
                    traceback.print_exc()
                    
        except FileNotFoundError:
            log.error("Le fichier des états des stations est introuvable.")
        except json.JSONDecodeError:
            log.error("Erreur de lecture du fichier JSON des états des stations.")
            
    except Exception as e:
        log.error(f"Une erreur inattendue est survenue : {e}")
        import traceback
        traceback.print_exc()
    
    #input("\nAppuyez sur Entrée pour continuer...")