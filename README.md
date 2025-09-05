# Générateur de Diagrammes pour Stations d'Épuration (STEP)

## 📋 Description

Application Python pour la génération et la gestion de diagrammes de flux pour les stations d'épuration (STEP).

## 🔄 Architecture et Flux de Données

### Vue d'Ensemble du Pipeline

┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Initialisation├────>│  Menu Principal  ├────>│Gestion des Données│
└────────┬────────┘     └────────┬─────────┘     └────────┬──────────┘
         │                       │                        │
         │                       ▼                        ▼
         │              ┌──────────────────┐     ┌──────────────────┐
         └──────────────┤  Journalisation  │<────┤ Génération       │
                        └────────┬─────────┘     │ des Diagrammes   │
                                 │               └────────┬─────────┘
                                 │                        │
                                 └───────────┬────────────┘
                                             ▼
                                   ┌──────────────────┐
                                   │      Sortie      │
                                   └──────────────────┘

### Composants Principaux

1. **`main.py`**
   - Point d'entrée de l'application
   - Gestion du menu principal
   - Coordination entre les différents modules

2. **`diagramme_flux.py`**
   - Génération des diagrammes de flux
   - Gestion des interactions utilisateur
   - Export des diagrammes

3. **`gen_station.py`**
   - Gestion des opérations CRUD sur les stations
   - Validation des données

4. **`create_station.py`**
   - Création de nouvelles stations
   - Configuration des paramètres initiaux

5. **`utils.py`**
   - Fonctions utilitaires partagées
   - Gestion des erreurs

## 🚀 Fonctionnalités

- Génération de diagrammes de flux interactifs
- Gestion des différentes configurations de stations d'épuration
- Suivi de l'état des ouvrages
- Export des diagrammes au format PNG
- Interface en ligne de commande intuitive

## 🛠️ Prérequis

- Python 3.8+
- Bibliothèques Python (voir `requirements.txt`)

## 🚀 Installation

1. Cloner le dépôt :

   ```bash
   git clone [URL_DU_REPO]
   cd generateur_STEP
   ```

2. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

## 🏃 Utilisation

Exécutez le programme principal :

```bash
python main.py
```

## 📂 Structure du Projet

generateur_STEP/
├── data/                 # Fichiers de données JSON
│   ├── etat_station.json
│   ├── stations.json
│   └── types.json
├── logs/                 # Fichiers de logs
├── create_station.py     # Création de nouvelles stations
├── diagramme_flux.py     # Génération des diagrammes
├── gen_station.py        # Gestion des stations
├── main.py               # Point d'entrée principal
├── migrate_data.py       # Migration des données
└── utils.py             # Utilitaires

## 📝 Guide d'Utilisation

Voir le fichier GUIDE.md pour un guide détaillé.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Auteurs

[Dr Kellouche/kelloucheaeh@gmail.com]
