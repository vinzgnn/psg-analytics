"""
tools.py — Fonctions BigQuery exposées à l'agent Claude.
Chaque fonction interroge un mart dbt et retourne un dict Python.

Authentification GCP :
  - En local     : via GOOGLE_APPLICATION_CREDENTIALS (fichier JSON) dans .env
  - Streamlit Cloud : via st.secrets["gcp_service_account"] (dict JSON injecté)
"""

import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

PROJECT  = os.getenv("GCP_PROJECT_ID", "psg-analytics-2026")
DATASET  = os.getenv("BIGQUERY_DATASET", "psg_analytics")


def _client() -> bigquery.Client:
    """
    Crée un client BigQuery authentifié.
    Priorité : st.secrets (Streamlit Cloud) > GOOGLE_APPLICATION_CREDENTIALS (local).
    """
    try:
        # Sur Streamlit Cloud, les secrets sont injectés via st.secrets
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]),
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            return bigquery.Client(project=PROJECT, credentials=creds)
    except Exception:
        pass

    # En local : on utilise GOOGLE_APPLICATION_CREDENTIALS via l'env
    return bigquery.Client(project=PROJECT)


def get_standings() -> dict:
    """
    Retourne le classement complet de la Ligue 1 (mart_classement).
    Colonnes réelles : position, team_name, points, won, draw, lost,
                       goals_for, goals_against, goal_difference, is_psg.
    """
    sql = f"""
        SELECT
            position,
            team_name,
            played_games,
            won,
            draw,
            lost,
            points,
            goals_for,
            goals_against,
            goal_difference,
            is_psg
        FROM `{PROJECT}.{DATASET}.mart_classement`
        ORDER BY position
    """
    rows = _client().query(sql).result()
    return {"classement": [dict(r) for r in rows]}


def get_psg_matches() -> dict:
    """
    Retourne tous les matchs du PSG (mart_psg_matches).
    Colonnes réelles : matchday, opponent_name, psg_side, psg_score,
                       opponent_score, psg_result, psg_points_cumul.
    """
    sql = f"""
        SELECT
            matchday,
            match_date,
            opponent_name,
            psg_side,
            psg_score,
            opponent_score,
            psg_result,
            psg_points,
            psg_points_cumul,
            is_clean_sheet
        FROM `{PROJECT}.{DATASET}.mart_psg_matches`
        WHERE is_finished = TRUE
        ORDER BY matchday
    """
    rows = _client().query(sql).result()
    return {"matchs": [dict(r) for r in rows]}


def get_top_scorers() -> dict:
    """
    Retourne les meilleurs buteurs/passeurs de Ligue 1 (mart_top_scorers).
    Colonnes réelles : rank, player_name, team_name, goals, assists,
                       goal_contributions, is_psg_player.
    """
    sql = f"""
        SELECT
            rank,
            player_name,
            team_name,
            goals,
            assists,
            goal_contributions,
            penalties,
            played_matches,
            is_psg_player
        FROM `{PROJECT}.{DATASET}.mart_top_scorers`
        ORDER BY rank
        LIMIT 20
    """
    rows = _client().query(sql).result()
    return {"top_scorers": [dict(r) for r in rows]}


def get_psg_summary() -> dict:
    """
    Retourne un résumé KPI du PSG : bilan V/N/D, buts, clean sheets, points.
    Calculé directement depuis mart_psg_matches (matchs terminés uniquement).
    """
    sql = f"""
        SELECT
            COUNT(*)                            AS matchs_joues,
            COUNTIF(psg_result = 'WIN')         AS victoires,
            COUNTIF(psg_result = 'DRAW')        AS nuls,
            COUNTIF(psg_result = 'LOSS')        AS defaites,
            SUM(psg_score)                      AS buts_marques,
            SUM(opponent_score)                 AS buts_encaisses,
            SUM(psg_score) - SUM(opponent_score) AS diff_buts,
            COUNTIF(is_clean_sheet = TRUE)      AS clean_sheets,
            MAX(psg_points_cumul)               AS points_totaux
        FROM `{PROJECT}.{DATASET}.mart_psg_matches`
        WHERE is_finished = TRUE
    """
    rows = list(_client().query(sql).result())
    return {"resume_psg": dict(rows[0])}


# --- Test rapide en ligne de commande ---
if __name__ == "__main__":
    import json

    print("=== Résumé PSG ===")
    print(json.dumps(get_psg_summary(), indent=2, default=str))

    print("\n=== Classement (5 premiers) ===")
    result = get_standings()
    result["classement"] = result["classement"][:5]
    print(json.dumps(result, indent=2, default=str))
