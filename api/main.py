"""
PSG Analytics — API maison
Brique HTTP entre BigQuery et les consommateurs (app Streamlit, etc.).
"""
from fastapi import Depends, FastAPI

from api import queries
from api.auth import verify_api_key

app = FastAPI(
    title="PSG Analytics API",
    description="API REST qui expose les données PSG Analytics stockées dans BigQuery.",
    version="0.1.0",
)


@app.get("/health", tags=["Système"])
def health_check():
    """Endpoint de santé — répond {status: ok} pour vérifier que l'API tourne."""
    return {"status": "ok"}


@app.get("/psg/summary", tags=["PSG"])
def psg_summary(_: str = Depends(verify_api_key)):
    """Résumé KPI du PSG : V/N/D, buts, clean sheets, points totaux."""
    return queries.get_psg_summary()


@app.get("/standings", tags=["Ligue 1"])
def standings(_: str = Depends(verify_api_key)):
    """Classement complet de la Ligue 1 (18 équipes, triées par position)."""
    return queries.get_standings()


@app.get("/matches", tags=["PSG"])
def psg_matches(_: str = Depends(verify_api_key)):
    """Tous les matchs du PSG terminés cette saison."""
    return queries.get_psg_matches()


@app.get("/top-scorers", tags=["Ligue 1"])
def top_scorers(_: str = Depends(verify_api_key)):
    """Top 20 buteurs / passeurs de Ligue 1, avec flag joueurs PSG."""
    return queries.get_top_scorers()
