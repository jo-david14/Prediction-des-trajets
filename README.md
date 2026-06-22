# NYC Taxi Fare Prediction

Prédiction du prix d'une course de taxi à New York via un modèle LightGBM, exposé par une API FastAPI dockerisée et consommé par un dashboard R Shiny.

## Architecture du projet

```
Projet_Machine_Learning/
│
├── Notebooks/
│   ├── 01_Nettoyage_Preparation_Donnees1.ipynb
│   └── 02_Modelisation_Evaluation2.ipynb
│
├── gestion API/
│   ├── main.py
│   ├── lgbm_model2.pkl
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── dashboard_.R
├── NYC_Taxi_Fare_Prediction.pdf
└── README.md
```

## Détail de l'architecture

### 1. Notebooks — Pipeline ML

**`01_Nettoyage_Preparation_Donnees1.ipynb`**
- Chargement du dataset brut NYC Taxi
- Suppression des outliers (coordonnées hors NYC, tarifs négatifs ou aberrants)
- Calcul de la distance entre départ et arrivée via la formule Haversine
- Sectorisation géographique : attribution d'un borough (Manhattan, Queens, Brooklyn, Bronx, Staten Island) à chaque point via des bounding boxes
- Détection des aéroports (JFK, EWR, LaGuardia) sous forme de variables binaires
- Encodage one-hot des boroughs (Manhattan comme référence)

**`02_Modelisation_Evaluation2.ipynb`**
- Séparation train/test
- Entraînement d'un modèle LightGBM (Gradient Boosting)
- Évaluation des performances (RMSE, MAE, R²)
- Export du modèle final : `lgbm_model2.pkl`

---

### 2. API FastAPI — `gestion API/`

**`main.py`**
- Recharge le modèle sérialisé au démarrage
- Reproduit le même feature engineering que le notebook (Haversine, boroughs, aéroports)
- Expose deux routes :
  - `GET /` → health check
  - `POST /predict` → reçoit les paramètres de la course en JSON, retourne le prix estimé, la distance et les boroughs

**`lgbm_model2.pkl`**
- Modèle LightGBM sérialisé avec joblib, prêt pour l'inférence

**`Dockerfile`**
- Image de base : `python:3.10-slim`
- Installation de `libgomp1` (dépendance système de LightGBM)
- Installation des dépendances Python via `requirements.txt`
- Exposition du port 8000
- Démarrage avec Uvicorn

---

### 3. Interface utilisateur — `dashboard_.R`

Application R Shiny qui :
- Présente un formulaire de saisie (coordonnées GPS, heure, mois, année, passagers)
- Envoie une requête `POST` à l'API FastAPI via `httr2`
- Affiche le prix estimé, la distance calculée et les boroughs de départ/arrivée

---

### Flux de données

```
Utilisateur (R Shiny)
      │  POST /predict (JSON)
      ▼
API FastAPI (Docker :8000)
      │  Feature engineering + model.predict()
      ▼
LightGBM (lgbm_model2.pkl)
      │  Prix estimé
      ▼
Réponse JSON → Affichage Shiny
```
