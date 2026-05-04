"""
PSG Analytics — Collecte des top scoreurs Ligue 1 → BigQuery raw_scorers

Récupère les meilleurs buteurs de Ligue 1 via l'API football-data.org
et les charge dans la table raw_scorers.

Lance-le avec :
    python scripts/collect_scorers.py
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
SCORERS_LIMIT = 100  # max permis par l'API (free tier accepte)

if not API_TOKEN:
    print("❌ FOOTBALL_DATA_API_KEY manquant dans .env")
    sys.exit(1)

HEADERS = {"X-Auth-Token": API_TOKEN}


SCHEMA_RAW_SCORERS = [
    bigquery.SchemaField("season_id", "INT64"),
    bigquery.SchemaField("season_start_date", "DATE"),
    bigquery.SchemaField("season_end_date", "DATE"),
    bigquery.SchemaField("competition_code", "STRING"),
    bigquery.SchemaField("competition_name", "STRING"),
    bigquery.SchemaField("rank", "INT64"),  # position dans le top scoreurs
    bigquery.SchemaField("player_id", "INT64"),
    bigquery.SchemaField("player_name", "STRING"),
    bigquery.SchemaField("player_first_name", "STRING"),
    bigquery.SchemaField("player_last_name", "STRING"),
    bigquery.SchemaField("player_nationality", "STRING"),
    bigquery.SchemaField("player_section", "STRING"),
    bigquery.SchemaField("player_position", "STRING"),
    bigquery.SchemaField("player_date_of_birth", "DATE"),
    bigquery.SchemaField("team_id", "INT64"),
    bigquery.SchemaField("team_name", "STRING"),
    bigquery.SchemaField("team_short_name", "STRING"),
    bigquery.SchemaField("team_tla", "STRING"),
    bigquery.SchemaField("goals", "INT64"),
    bigquery.SchemaField("assists", "INT64"),
    bigquery.SchemaField("penalties", "INT64"),
    bigquery.SchemaField("played_matches", "INT64"),
    bigquery.SchemaField("raw_payload", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
]


def fetch_scorers(limit: int = SCORERS_LIMIT) -> dict:
    url = f"{BASE_URL}/competitions/{LIGUE1_CODE}/scorers"
    response = requests.get(url, headers=HEADERS, params={"limit": limit}, timeout=15)
    response.raise_for_status()
    return response.json()


def transform_scorers(payload: dict) -> pd.DataFrame:
    ingested_at = datetime.now(tz=timezone.utc)
    season = payload.get("season") or {}
    comp = payload.get("competition") or {}

    rows = []
    for rank, scorer in enumerate(payload.get("scorers", []), start=1):
        player = scorer.get("player") or {}
        team = scorer.get("team") or {}
        rows.append({
            "season_id": season.get("id"),
            "season_start_date": season.get("startDate"),
            "season_end_date": season.get("endDate"),
            "competition_code": comp.get("code"),
            "competition_name": comp.get("name"),
            "rank": rank,
            "player_id": player.get("id"),
            "player_name": player.get("name"),
            "player_first_name": player.get("firstName"),
            "player_last_name": player.get("lastName"),
            "player_nationality": player.get("nationality"),
            "player_section": player.get("section"),
            "player_position": player.get("position"),
            "player_date_of_birth": player.get("dateOfBirth"),
            "team_id": team.get("id"),
            "team_name": team.get("name"),
            "team_short_name": team.get("shortName"),
            "team_tla": team.get("tla"),
            "goals": scorer.get("goals"),
            "assists": scorer.get("assists"),
            "penalties": scorer.get("penalties"),
            "played_matches": scorer.get("playedMatches"),
            "raw_payload": json.dumps(scorer, ensure_ascii=False),
            "ingested_at": ingested_at,
        })

    df = pd.DataFrame(rows)
    df["season_start_date"] = pd.to_datetime(df["season_start_date"], errors="coerce").dt.date
    df["season_end_date"] = pd.to_datetime(df["season_end_date"], errors="coerce").dt.date
    df["player_date_of_birth"] = pd.to_datetime(df["player_date_of_birth"], errors="coerce").dt.date
    return df


def main() -> None:
    print("📥 Collecte des top scoreurs Ligue 1")
    print(f"   Endpoint : {BASE_URL}/competitions/{LIGUE1_CODE}/scorers?limit={SCORERS_LIMIT}")

    payload = fetch_scorers()
    df = transform_scorers(payload)
    print(f"   DataFrame construit : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    print("\n🚀 Chargement vers BigQuery (raw_scorers)...")
    load_dataframe(
        df=df,
        table_name="raw_scorers",
        schema=SCHEMA_RAW_SCORERS,
        write_disposition="WRITE_TRUNCATE",
    )
    print("\n✅ raw_scorers mis à jour avec succès.")


if __name__ == "__main__":
    main()
