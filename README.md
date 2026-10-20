# enervision
Projet Piscine EADL

EnerVision vend de l’optimisation énergétique à des industriels européens soumis à trois pressions : des prix de l’énergie volatils, un reporting extra-financier qui se durcit, et une demande interne de pilotage fin.

Technos utilisées :

PostgreSQL 16 + TimescaleDB

FastAPI

React + Vite


### Module API
- Se connecte à la BDD TimescaleDB
- Donne accès au front avec des web services permettant de récupérer les prédictions de pics de consommation, l'historique des données et les recommandations
- Gestion de l'authentification

### Module Docs
- Donne accès à la documentation du projet

### Module ETL
- Récupère données de l'API Mock et les stocke dans BDD PostgreSQL
- Se connecte à la BDD PostgreSQL, transforme les données et les stocke dans une BDD TimescalDB

### Module Frontend
- Se connecte à l'API
- Affiche avec dashboard prédictions, historiques des données, recommandations

### Module Infra

### Module ML
- Se connecte à la BDD TimescaleDB
- Création d'un modèle, entraînement avec données BDD TimescaleDB
