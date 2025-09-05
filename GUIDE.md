# Guide Complet d'Utilisation - Générateur de Diagrammes STEP

## Table des Matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Menu Principal](#menu-principal)
4. [Gestion des Stations](#gestion-des-stations)
   - [Créer une nouvelle station](#créer-une-nouvelle-station)
   - [Lister les stations](#lister-les-stations)
   - [Modifier une station](#modifier-une-station)
   - [Supprimer une station](#supprimer-une-station)
5. [Gestion des Ouvrages](#gestion-des-ouvrages)
   - [Ajouter un ouvrage](#ajouter-un-ouvrage)
   - [Modifier l'état d'un ouvrage](#modifier-létat-dun-ouvrage)
6. [Génération de Diagrammes](#génération-de-diagrammes)
7. [Export des Données](#export-des-données)
8. [Dépannage](#dépannage)
9. [FAQ](#faq-foire-aux-questions)

## Introduction

Générateur de Diagrammes pour Stations d'Épuration (STEP) est un outil puissant conçu pour les professionnels du traitement des eaux usées. Cette application permet de modéliser, visualiser et documenter facilement les schémas de procédés des stations d'épuration, qu'elles soient de petite ou grande capacité.

### À qui s'adresse cet outil ?

- **Ingénieurs en assainissement** : Pour concevoir et documenter les installations
- **Exploitants de stations d'épuration** : Pour visualiser et suivre l'état des ouvrages
- **Bureaux d'études** : Pour modéliser des solutions de traitement des eaux usées
- **Enseignants et étudiants** : Pour l'apprentissage des procédés d'épuration
- **Services techniques des collectivités** : Pour la gestion du patrimoine d'assainissement

### Fonctionnalités clés

- Création et gestion de fiches stations complètes
- Visualisation interactive des schémas de procédés
- Suivi en temps réel de l'état des équipements
- Génération de rapports et d'exportations multiples
- Interface intuitive et personnalisable

## Installation

### Prérequis

- Python 3.8 ou supérieur
- Bibliothèques listées dans `requirements.txt`
- Environnement graphique (pour la visualisation)

### Procédure d'installation

```bash
# Téléchargement
git clone https://github.com/Kellouche/GEN_STEP.git
cd generateur_STEP

# Configuration de l'environnement
python -m venv venv
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installation des dépendances
pip install -r requirements.txt
```

## Menu Principal

Au lancement, le programme affiche un menu avec les options suivantes :

1. ➕ Créer une nouvelle station
2. 📊 Afficher le diagramme de flux d'une station
3. 🔄 Mettre à jour l'état des ouvrages
4. 📋 Lister toutes les stations
5. 🗑️ Supprimer une station
6. ❌ Quitter

## Gestion des Stations

### Créer une nouvelle station

1. Sélectionnez l'option "1. Créer une nouvelle station"
2. Suivez les invites pour saisir :
   - Nom de la station
   - Type de procédé
   - Localisation
   - Capacité de traitement
3. Le système génère automatiquement un identifiant unique

### Lister les stations

1. Sélectionnez l'option "4. Lister toutes les stations"
2. Un tableau s'affiche avec :
   - ID de la station
   - Nom
   - Type de procédé
   - Date de création
   - Dernière mise à jour

### Modifier une station

1. Sélectionnez l'option "4. Lister toutes les stations"
2. Notez l'ID de la station à modifier
3. Utilisez l'option de modification appropriée
4. Suivez les invites pour mettre à jour les informations

### Supprimer une station

1. Sélectionnez l'option "5. Supprimer une station"
2. Entrez l'ID de la station à supprimer
3. Confirmez la suppression

## Gestion des Ouvrages

### Ajouter un ouvrage

1. Sélectionnez la station cible
2. Choisissez l'option d'ajout d'ouvrage
3. Sélectionnez le type d'ouvrage dans la liste
4. Saisissez les spécifications requises

### Modifier l'état d'un ouvrage

1. Sélectionnez l'option "3. Mettre à jour l'état des ouvrages"
2. Choisissez la station concernée
3. Sélectionnez l'ouvrage à modifier
4. Choisissez le nouvel état parmi :
   - En service
   - En panne
   - En maintenance
   - Hors service
   - Nouvel ouvrage

## Génération de Diagrammes

1. Sélectionnez l'option "2. Afficher le diagramme de flux"
2. Choisissez la station à visualiser
3. Le diagramme s'affiche avec les ouvrages et leurs états actuels
4. Options disponibles :
   - Zoom avant/arrière
   - Déplacement
   - Export en image

## Export des Données

### Exporter un diagramme

```bash
python main.py --export --station ID_DE_LA_STATION --format png --output mon_diagramme.png
```

### Options d'export disponibles

- Format : PNG, PDF, SVG
- Résolution (pour les images matricielles)
- Inclure/masquer la légende

## Dépannage

### Problèmes courants

- **Les modifications ne sont pas sauvegardées** :
  - Vérifiez les permissions d'écriture
  - Assurez-vous d'avoir assez d'espace disque
  - Consultez les logs d'erreur

- **Le diagramme ne s'affiche pas** :
  - Vérifiez l'installation de matplotlib
  - Assurez-vous qu'un environnement graphique est disponible

## FAQ (Foire Aux Questions)

### Gestion des Données

#### Quels types de données puis-je importer ?

L'application supporte l'import de données au format JSON. Vous pouvez importer :

- Des configurations de stations existantes
- Des états d'ouvrages
- Des modèles de procédés prédéfinis

#### Comment sauvegarder mes données ?

Toutes les modifications sont automatiquement enregistrées dans le fichier `data/etat_station.json`. Pour une sauvegarde sécurisée :

1. Copiez le fichier [etat_station.json](cci:7://file:///d:/IA%20Water%20Data%20Analysis/generateur_STEP/d:/IA%20Water%20Data%20Analysis/generateur_STEP/data/etat_station.json:0:0-0:0)
2. Stockez-le dans un emplacement sécurisé
3. Renommez-le avec la date (ex: `etat_station_2025-09-05.json`)

### Gestion des Procédés

#### Quels types de procédés sont supportés ?

L'application prend en charge plusieurs types de procédés d'épuration :

- Boues activées
- Lagunage
- Filtres plantés de roseaux
- MBR (Bioréacteur à membranes)
- SBR (Réacteur séquentiel)

#### Puis-je créer un procédé personnalisé ?

Oui, vous pouvez créer des procédés personnalisés en :

1. Modifiant le fichier `types.json` dans le dossier `data/`
2. Suivant la structure existante
3. En redémarrant l'application

### Gerer des Ouvrages

#### Comment ajouter un nouvel ouvrage ?

1. Allez dans "Gestion des Ouvrages"
2. Sélectionnez "Ajouter un ouvrage"
3. Choisissez le type d'ouvrage dans la liste
4. Remplissez les champs requis

#### Quels états sont disponibles pour un ouvrage ?

- En service
- En panne
- En maintenance
- Hors service
- Nouvel ouvrage

### Générer de Diagrammes

#### Comment personnaliser l'apparence d'un diagramme ?

Vous pouvez personnaliser :

- Les couleurs des ouvrages
- La taille du texte
- L'échelle du diagramme
- L'affichage des légendes

#### Puis-je exporter un diagramme pour un rapport ?

Oui, utilisez la commande :

```bash
python main.py --export --station ID_STATION --format pdf --output rapport.pdf
## Support

Pour toute question ou problème, contactez [kelloucheaeh@gmail.com] ou ouvrez une issue sur (https://github.com/Kellouche/GEN_STEP/issues).
