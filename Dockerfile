# =============================================================
# PSG Analytics API — Dockerfile
# =============================================================
# Build : docker build -t psg-analytics-api .
# Run   : voir README Phase 6 pour les commandes complètes
# =============================================================

FROM python:3.13-slim

# Empêche Python de bufferiser stdout/stderr (logs visibles en temps réel)
ENV PYTHONUNBUFFERED=1

# Cloud Run injecte la variable PORT (défaut 8080)
ENV PORT=8080

WORKDIR /app

# --- Dépendances (couche cachée séparément du code) ----------
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# --- Code de l'API ------------------------------------------
COPY api/ ./api/

# --- Exposition du port et démarrage ------------------------
EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
