# Guide Complet d'Utilisation - Générateur de Diagrammes STEP

## Table des Matières

1. [Introduction](#introduction)
2. [Prise en Main Rapide](#prise-en-main-rapide)
3. [Fonctionnalités Avancées](#fonctionnalités-avancées)
4. [Gestion des Stations](#gestion-des-stations)
5. [Génération de Diagrammes](#génération-de-diagrammes)
6. [Bonnes Pratiques](#bonnes-pratiques)
7. [Dépannage](#dépannage)
8. [FAQ](#faq)

## Introduction

Bienvenue dans le Générateur de Diagrammes pour Stations d'Épuration. Cet outil puissant vous permet de concevoir, visualiser et documenter des schémas de procédés pour des stations d'épuration de toute taille et complexité.

### À qui s'adresse ce guide ?

- Ingénieurs en assainissement
- Techniciens de station d'épuration
- Bureaux d'études
- Enseignants et étudiants

## Prise en Main Rapide

### Prérequis

- Python 3.8 ou supérieur
- Bibliothèques listées dans `requirements.txt`
- Environnement graphique (pour la visualisation)

### Installation

```bash
# Téléchargement
git clone (https://github.com/Kellouche/GEN_STEP)
cd generateur_STEP

# Configuration de l'environnement
python -m venv venv
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installation des dépendances
pip install -r requirements.txt
```

### Premier Lancement

1. Démarrer l'application :

   ```bash
   python main.py
   ```

2. Suivre les instructions à l'écran
3. Pour obtenir de l'aide à tout moment, appuyez sur 'h' ou '?'

## Fonctionnalités Avancées

### Gestion des Configurations

- Création de modèles personnalisés
- Import/Export des configurations
- Historique des modifications

### Personnalisation des Diagrammes

- Choix des couleurs et styles
- Ajout de légendes personnalisées
- Contrôle de la densité d'information

## Gestion des Stations

### Création d'une Nouvelle Station

1. Sélectionnez l'option "Créer une station"
2. Entrez les informations de base :
   - Nom de la station
   - Localisation
   - Capacité de traitement
3. Ajoutez les ouvrages nécessaires
4. Validez la configuration

## Génération de Diagrammes

### Options d'Export

- PNG haute résolution
- PDF vectoriel
- Fichiers source modifiables

### Exemple de Commande d'Export

```bash
python main.py --export --station "NomStation" --format png --output mon_diagramme.png
```

## Bonnes Pratiques

### Organisation des Données

- Utilisez des noms clairs et cohérents
- Créez des sauvegardes régulières
- Documentez les configurations complexes

### Performances

- Pour les grandes stations, utilisez l'export PDF
- Limitez le nombre d'éléments affichés
- Utilisez les modèles prédéfinis

## Dépannage

### Problèmes Courants

1. **Le diagramme ne s'affiche pas**
   - Vérifiez les dépendances
   - Consultez les logs

2. **Problème d'affichage**
   - Mettez à jour matplotlib
   - Vérifiez l'encodage des fichiers

## FAQ

### Comment mettre à jour ?

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Puis-je automatiser la génération ?

Oui, utilisez le mode batch :

```bash
python main.py --batch --config mon_config.json
```

## Support

Pour toute question, contactez [kelloucheaeh@gmail.com].
