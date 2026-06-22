from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd

app = FastAPI(title="NYC Taxi Fare Prediction")

# Charger le modèle
model = joblib.load("lgbm_model2.pkl")

# ─── Définir les bornes (comme dans ton notebook) ───────────────────────────
NYC_BOROUGHS = {
    'manhattan': {'min_lng': -74.0479, 'min_lat': 40.6829, 'max_lng': -73.9067, 'max_lat': 40.8820},
    'queens':    {'min_lng': -73.9630, 'min_lat': 40.5431, 'max_lng': -73.7004, 'max_lat': 40.8007},
    'brooklyn':  {'min_lng': -74.0421, 'min_lat': 40.5707, 'max_lng': -73.8334, 'max_lat': 40.7395},
    'bronx':     {'min_lng': -73.9339, 'min_lat': 40.7855, 'max_lng': -73.7654, 'max_lat': 40.9176},
    'staten_island': {'min_lng': -74.2558, 'min_lat': 40.4960, 'max_lng': -74.0522, 'max_lat': 40.6490},
}

NYC_AIRPORTS = {
    'JFK':       {'min_lng': -73.8352, 'min_lat': 40.6195, 'max_lng': -73.7401, 'max_lat': 40.6659},
    'EWR':       {'min_lng': -74.1925, 'min_lat': 40.6700, 'max_lng': -74.1531, 'max_lat': 40.7081},
    'LaGuardia': {'min_lng': -73.8895, 'min_lat': 40.7664, 'max_lng': -73.8550, 'max_lat': 40.7931},
}

# ─── Fonctions de feature engineering (copiées de ton notebook) ─────────────
def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    d_phi = np.radians(lat2 - lat1)
    d_lam = np.radians(lon2 - lon1)
    a = np.sin(d_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lam/2)**2
    return r * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def get_borough(lat, lng):
    for name, b in NYC_BOROUGHS.items():
        if b['min_lat'] <= lat <= b['max_lat'] and b['min_lng'] <= lng <= b['max_lng']:
            return name
    return 'others'

def is_airport(lat, lng, airport):
    a = NYC_AIRPORTS[airport]
    return int(a['min_lat'] <= lat <= a['max_lat'] and a['min_lng'] <= lng <= a['max_lng'])

# ─── Données d'entrée de l'utilisateur ───────────────────────────────────────
class TripInput(BaseModel):
    pickup_longitude: float
    pickup_latitude: float
    dropoff_longitude: float
    dropoff_latitude: float
    passenger_count: int
    pickup_hour: int
    pickup_month: int
    pickup_year: int
    pickup_day_of_week: int   # 0=Lundi, 6=Dimanche

# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "API NYC Taxi Fare — /predict pour prédire, /docs pour tester"}

@app.post("/predict")
def predict(trip: TripInput):
    # 1. Feature engineering (comme dans le notebook)
    distance = haversine_distance(
        trip.pickup_latitude, trip.pickup_longitude,
        trip.dropoff_latitude, trip.dropoff_longitude
    )

    pickup_borough  = get_borough(trip.pickup_latitude,  trip.pickup_longitude)
    dropoff_borough = get_borough(trip.dropoff_latitude, trip.dropoff_longitude)

    # 2. Construire le DataFrame avec les mêmes colonnes que X_train
    row = {
        "passenger_count":       trip.passenger_count,
        "pickup_hour":           trip.pickup_hour,
        "pickup_month":          trip.pickup_month,
        "pickup_year":           trip.pickup_year,
        "pickup_day_of_week":    trip.pickup_day_of_week,
        "distance_km":           distance,
        "is_pickup_JFK":         is_airport(trip.pickup_latitude,  trip.pickup_longitude,  "JFK"),
        "is_dropoff_JFK":        is_airport(trip.dropoff_latitude, trip.dropoff_longitude, "JFK"),
        "is_pickup_EWR":         is_airport(trip.pickup_latitude,  trip.pickup_longitude,  "EWR"),
        "is_dropoff_EWR":        is_airport(trip.dropoff_latitude, trip.dropoff_longitude, "EWR"),
        "is_pickup_la_guardia":  is_airport(trip.pickup_latitude,  trip.pickup_longitude,  "LaGuardia"),
        "is_dropoff_la_guardia": is_airport(trip.dropoff_latitude, trip.dropoff_longitude, "LaGuardia"),
        # One-hot borough (drop_first=True → manhattan est la référence)
        "pickup_borough_bronx":         int(pickup_borough == "bronx"),
        "pickup_borough_brooklyn":      int(pickup_borough == "brooklyn"),
        "pickup_borough_others":        int(pickup_borough == "others"),
        "pickup_borough_queens":        int(pickup_borough == "queens"),
        "pickup_borough_staten_island": int(pickup_borough == "staten_island"),
        "dropoff_borough_bronx":        int(dropoff_borough == "bronx"),
        "dropoff_borough_brooklyn":     int(dropoff_borough == "brooklyn"),
        "dropoff_borough_others":       int(dropoff_borough == "others"),
        "dropoff_borough_queens":       int(dropoff_borough == "queens"),
        "dropoff_borough_staten_island":int(dropoff_borough == "staten_island"),
    }

    X = pd.DataFrame([row])

    # 3. Prédiction
    prediction = model.predict(X)[0]

    return {
        "predicted_fare_usd": round(float(prediction), 2),
        "distance_km": round(distance, 3),
        "pickup_borough": pickup_borough,
        "dropoff_borough": dropoff_borough,
    }