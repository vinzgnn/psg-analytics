"""
queries.py — Logique BigQuery de l'API PSG Analytics.

Chaque fonction interroge un mart dbt et retourne un dict.
Aucune dépendance HTTP : ces fonctions peuvent être appelées depuis
l'API FastAPI, un script CLI, un notebook, etc.

Authentification GCP :
  - En local       : GOOGLE_APPLICATION_CREDENTIALS dans .env
  - Sur Cloud Run  : credentials automatiques du service account
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT = os.getenv("GCP_PROJECT_ID", "psg-analytics-2026")
DATASET = os.getenv("BIGQUERY_DATASET", "psg_analytics")


def _client() -> bigquery.Client:
    """Client BigQuery — utilise les Application Default Credentials (ADC)."""
    return bigquery.Client(project=PROJECT)


def get_psg_summary() -> dict:
    """Résumé KPI du PSG : V/N/D, buts, clean sheets, points totaux."""
    sql = f"""
        SELECT
            COUNT(*)                             AS matchs_joues,
            COUNTIF(psg_result = 'WIN')          AS victoires,
            COUNTIF(psg_result = 'DRAW')         AS nuls,
            COUNTIF(psg_result = 'LOSS')         AS defaites,
            SUM(psg_score)                       AS buts_marques,
            SUM(opponent_score)                  AS buts_encaisses,
            SUM(psg_score) - SUM(opponent_score) AS diff_buts,
            COUNTIF(is_clean_sheet = TRUE)       AS clean_sheets,
            MAX(psg_points_cumul)                AS points_totaux
        FROM `{PROJECT}.{DATASET}.mart_psg_matches`
        WHERE is_finished = TRUE
    """
    rows = list(_client().query(sql).result())
    return {"resume_psg": dict(rows[0])}


def get_standings() -> dict:
    """Classement complet de la Ligue 1 (18 équipes, triées par position)."""
    sql = f"""
        SELECT
            position, team_name, played_games, won, draw, lost,
            points, goals_for, goals_against, goal_difference, is_psg
        FROM `{PROJECT}.{DATASET}.mart_classement`
        ORDER BY position
    """
    rows = _client().query(sql).result()
    return {"classement": [dict(r) for r in rows]}


def get_psg_matches() -> dict:
    """Tous les matchs du PSG terminés cette saison."""
    sql = f"""
        SELECT
            matchday, match_date, opponent_name, psg_side,
            psg_score, opponent_score, psg_result,
            psg_points, psg_points_cumul, is_clean_sheet
        FROM `{PROJECT}.{DATASET}.mart_psg_matches`
        WHERE is_finished = TRUE
        ORDER BY matchday
    """
    rows = _client().query(sql).result()
    return {"matchs": [dict(r) for r in rows]}


def get_top_scorers() -> dict:
    """Top 20 buteurs / passeurs de Ligue 1, avec flag joueurs PSG."""
    sql = f"""
        SELECT
            rank, player_name, team_name, goals, assists,
            goal_contributions, penalties, played_matches, is_psg_player
        FROM `{PROJECT}.{DATASET}.mart_top_scorers`
        ORDER BY rank
        LIMIT 20
    """
    rows = _client().query(sql).result()
    return {"top_scorers": [dict(r) for r in rows]}
