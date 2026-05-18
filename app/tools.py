"""
tools.py — Fonctions exposées à l'agent Claude.
Chaque fonction appelle l'API maison FastAPI (PSG Analytics API) via HTTP.

Authentification API :
  - En local         : API_URL + API_KEY depuis .env
  - Streamlit Cloud  : API_URL + API_KEY depuis st.secrets
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def _get_api_config() -> tuple[str, str]:
    """
    Retourne (api_url, api_key) selon l'environnement d'exécution.
    Priorité : st.secrets (Streamlit Cloud) > variables d'env (local).
    """
    try:
        import streamlit as st
        if "api_url" in st.secrets and "api_key" in st.secrets:
            return st.secrets["api_url"], st.secrets["api_key"]
    except Exception:
        pass

    api_url = os.getenv("API_URL", "http://localhost:8000")
    api_key = os.getenv("API_KEY", "")
    return api_url, api_key


def _get(endpoint: str) -> dict:
    """
    Effectue un GET authentifié vers l'API et retourne le JSON.
    Lève une RuntimeError si la réponse n'est pas 200.
    """
    api_url, api_key = _get_api_config()
    url = f"{api_url.rstrip('/')}{endpoint}"
    headers = {"X-API-Key": api_key}

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        raise RuntimeError(
            f"Erreur API {response.status_code} sur {endpoint} : {response.text}"
        )

    return response.json()


def get_standings() -> dict:
    """
    Retourne le classement complet de la Ligue 1.
    """
    return _get("/standings")


def get_psg_matches() -> dict:
    """
    Retourne tous les matchs du PSG terminés cette saison.
    """
    return _get("/matches")


def get_top_scorers() -> dict:
    """
    Retourne le top 20 des buteurs/passeurs de Ligue 1, avec flag joueurs PSG.
    """
    return _get("/top-scorers")


def get_psg_summary() -> dict:
    """
    Retourne le résumé KPI du PSG : V/N/D, buts, clean sheets, points.
    """
    return _get("/psg/summary")


# --- Test rapide en ligne de commande ---
if __name__ == "__main__":
    import json

    print("=== Résumé PSG ===")
    print(json.dumps(get_psg_summary(), indent=2, default=str))

    print("\n=== Classement (5 premiers) ===")
    result = get_standings()
    result["classement"] = result["classement"][:5]
    print(json.dumps(result, indent=2, default=str))
