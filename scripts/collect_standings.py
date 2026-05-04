"""
PSG Analytics — Collecte du classement Ligue 1 → BigQuery raw_standings

Récupère le classement actuel de la Ligue 1 (vues TOTAL, HOME, AWAY)
via l'API football-data.org et le charge dans la table raw_standings.

Lance-le avec :
    python scripts/collect_standings.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv
from google.cloud import bigquery

from bq_helpers import load_dataframe

load_dotenv()

API_TOKEN = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
LIGUE1_CODE = "FL1"

if not API_TOKEN:
    print("❌ FOOTBALL_DATA_API_KEY manquant dans .env")
    sys.exit(1)

HEADERS = {"X-Auth-Token": API_TOKEN}


SCHEMA_RAW_STANDINGS = [
    bigquery.SchemaField("season_id", "INT64"),
    bigquery.SchemaField("season_start_date", "DATE"),
    bigquery.SchemaField("season_end_date", "DATE"),
    bigquery.SchemaField("competition_code", "STRING"),
    bigquery.SchemaField("competition_name", "STRING"),
    bigquery.SchemaField("standings_type", "STRING"),  # TOTAL / HOME / AWAY
    bigquery.SchemaField("position", "INT64"),
    bigquery.SchemaField("team_id", "INT64"),
    bigquery.SchemaField("team_name", "STRING"),
    bigquery.SchemaField("team_short_name", "STRING"),
    bigquery.SchemaField("team_tla", "STRING"),
    bigquery.SchemaField("played_games", "INT64"),
    bigquery.SchemaField("form", "STRING"),
    bigquery.SchemaField("won", "INT64"),
    bigquery.SchemaField("draw", "INT64"),
    bigquery.SchemaField("lost", "INT64"),
    bigquery.SchemaField("points", "INT64"),
    bigquery.SchemaField("goals_for", "INT64"),
    bigquery.SchemaField("goals_against", "INT64"),
    bigquery.SchemaField("goal_difference", "INT64"),
    bigquery.SchemaField("raw_payload", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
]


def fetch_standings() -> dict:
    url = f"{BASE_URL}/competitions/{LIGUE1_CODE}/standings"
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.json()


def transform_standings(payload: dict) -> pd.DataFrame:
    ingested_at = datetime.now(tz=timezone.utc)
    season = payload.get("season") or {}
    comp = payload.get("competition") or {}

    rows = []
    for table in payload.get("standings", []):
        st_type = table.get("type")  # TOTAL, HOME, AWAY
        for row in table.get("table", []):
            team = row.get("team") or {}
            rows.append({
                "season_id": season.get("id"),
                "season_start_date": season.get("startDate"),
                "season_end_date": season.get("endDate"),
                "competition_code": comp.get("code"),
                "competition_name": comp.get("name"),
                "standings_type": st_type,
                "position": row.get("position"),
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "team_short_name": team.get("shortName"),
                "team_tla": team.get("tla"),
                "played_games": row.get("playedGames"),
                "form": row.get("form"),
                "won": row.get("won"),
                "draw": row.get("draw"),
                "lost": row.get("lost"),
                "points": row.get("points"),
                "goals_for": row.get("goalsFor"),
                "goals_against": row.get("goalsAgainst"),
                "goal_difference": row.get("goalDifference"),
                "raw_payload": json.dumps(row, ensure_ascii=False),
                "ingested_at": ingested_at,
            })

    df = pd.DataFrame(rows)
    df["season_start_date"] = pd.to_datetime(df["season_start_date"], errors="coerce").dt.date
    df["season_end_date"] = pd.to_datetime(df["season_end_date"], errors="coerce").dt.date
    return df


def main() -> None:
    print("📥 Collecte du classement Ligue 1")
    print(f"   Endpoint : {BASE_URL}/competitions/{LIGUE1_CODE}/standings")

    payload = fetch_standings()
    df = transform_standings(payload)
    print(f"   DataFrame construit : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    print(f"   Vues incluses : {sorted(df['standings_type'].unique())}")

    print("\n🚀 Chargement vers BigQuery (raw_standings)...")
    load_dataframe(
        df=df,
        table_name="raw_standings",
        schema=SCHEMA_RAW_STANDINGS,
        write_disposition="WRITE_TRUNCATE",
    )
    print("\n✅ raw_standings mis à jour avec succès.")


if __name__ == "__main__":
    main()
