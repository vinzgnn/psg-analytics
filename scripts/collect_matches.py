"""
PSG Analytics — Collecte des matchs Ligue 1 → BigQuery raw_matches

Récupère tous les matchs de la saison en cours via l'API football-data.org
et les charge dans la table raw_matches.

Lance-le avec :
    python scripts/collect_matches.py
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


# Schéma BigQuery — garantit le typage et la cohérence des chargements
SCHEMA_RAW_MATCHES = [
    bigquery.SchemaField("match_id", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("utc_date", "TIMESTAMP"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("matchday", "INT64"),
    bigquery.SchemaField("stage", "STRING"),
    bigquery.SchemaField("season_id", "INT64"),
    bigquery.SchemaField("season_start_date", "DATE"),
    bigquery.SchemaField("season_end_date", "DATE"),
    bigquery.SchemaField("competition_code", "STRING"),
    bigquery.SchemaField("competition_name", "STRING"),
    bigquery.SchemaField("home_team_id", "INT64"),
    bigquery.SchemaField("home_team_name", "STRING"),
    bigquery.SchemaField("home_team_short_name", "STRING"),
    bigquery.SchemaField("home_team_tla", "STRING"),
    bigquery.SchemaField("away_team_id", "INT64"),
    bigquery.SchemaField("away_team_name", "STRING"),
    bigquery.SchemaField("away_team_short_name", "STRING"),
    bigquery.SchemaField("away_team_tla", "STRING"),
    bigquery.SchemaField("home_score_full_time", "INT64"),
    bigquery.SchemaField("away_score_full_time", "INT64"),
    bigquery.SchemaField("home_score_half_time", "INT64"),
    bigquery.SchemaField("away_score_half_time", "INT64"),
    bigquery.SchemaField("winner", "STRING"),
    bigquery.SchemaField("duration", "STRING"),
    bigquery.SchemaField("raw_payload", "STRING"),  # JSON brut pour archivage
    bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
]


def fetch_matches() -> list[dict]:
    """Appelle l'API et retourne la liste brute des matchs."""
    url = f"{BASE_URL}/competitions/{LIGUE1_CODE}/matches"
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get("matches", [])


def transform_matches(raw_matches: list[dict]) -> pd.DataFrame:
    """Aplatit les matchs en DataFrame typé pour BigQuery."""
    ingested_at = datetime.now(tz=timezone.utc)
    rows = []

    for m in raw_matches:
        season = m.get("season") or {}
        comp = m.get("competition") or {}
        home = m.get("homeTeam") or {}
        away = m.get("awayTeam") or {}
        score = m.get("score") or {}
        full_time = score.get("fullTime") or {}
        half_time = score.get("halfTime") or {}

        rows.append({
            "match_id": m["id"],
            "utc_date": m.get("utcDate"),
            "status": m.get("status"),
            "matchday": m.get("matchday"),
            "stage": m.get("stage"),
            "season_id": season.get("id"),
            "season_start_date": season.get("startDate"),
            "season_end_date": season.get("endDate"),
            "competition_code": comp.get("code"),
            "competition_name": comp.get("name"),
            "home_team_id": home.get("id"),
            "home_team_name": home.get("name"),
            "home_team_short_name": home.get("shortName"),
            "home_team_tla": home.get("tla"),
            "away_team_id": away.get("id"),
            "away_team_name": away.get("name"),
            "away_team_short_name": away.get("shortName"),
            "away_team_tla": away.get("tla"),
            "home_score_full_time": full_time.get("home"),
            "away_score_full_time": full_time.get("away"),
            "home_score_half_time": half_time.get("home"),
            "away_score_half_time": half_time.get("away"),
            "winner": score.get("winner"),
            "duration": score.get("duration"),
            "raw_payload": json.dumps(m, ensure_ascii=False),
            "ingested_at": ingested_at,
        })

    df = pd.DataFrame(rows)

    # Conversion explicite des dates (BigQuery est strict sur les types)
    df["utc_date"] = pd.to_datetime(df["utc_date"], utc=True, errors="coerce")
    df["season_start_date"] = pd.to_datetime(df["season_start_date"], errors="coerce").dt.date
    df["season_end_date"] = pd.to_datetime(df["season_end_date"], errors="coerce").dt.date

    return df


def main() -> None:
    print("📥 Collecte des matchs Ligue 1")
    print(f"   Endpoint : {BASE_URL}/competitions/{LIGUE1_CODE}/matches")

    raw = fetch_matches()
    print(f"   {len(raw)} matchs récupérés depuis l'API")

    df = transform_matches(raw)
    print(f"   DataFrame construit : {df.shape[0]} lignes, {df.shape[1]} colonnes")

    print("\n🚀 Chargement vers BigQuery (raw_matches)...")
    load_dataframe(
        df=df,
        table_name="raw_matches",
        schema=SCHEMA_RAW_MATCHES,
        write_disposition="WRITE_TRUNCATE",
    )
    print("\n✅ raw_matches mis à jour avec succès.")


if __name__ == "__main__":
    main()
