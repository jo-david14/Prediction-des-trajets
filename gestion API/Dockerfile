# 1. Utiliser une image Python officielle légère
FROM python:3.10-slim

# 2. Définir le dossier de travail dans le conteneur
WORKDIR /app

# 3. Installer les dépendances système nécessaires pour LightGBM
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copier le fichier des dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier le reste du code du projet et le modèle
COPY main.py .
COPY lgbm_model2.pkl .

# 6. Exposer le port sur lequel FastAPI va tourner
EXPOSE 8000

# 7. Commande pour lancer l'API avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]