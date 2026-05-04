"""
PSG Analytics — Helpers BigQuery

Module réutilisable contenant :
- get_bq_client() : retourne un client BigQuery authentifié
- load_dataframe() : charge un DataFrame pandas dans une table BigQuery
- TABLE_REF() : renvoie l'identifiant complet d'une table (project.dataset.table)
"""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# Charger .env dès l'import du module
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "psg_analytics")

if not PROJECT_ID:
    raise RuntimeError(
        "GCP_PROJECT_ID n'est pas défini dans .env. "
        "Vérifie ton fichier .env à la racine du projet."
    )


def get_bq_client() -> bigquery.Client:
    """
    Retourne un client BigQuery authentifié via la variable
    GOOGLE_APPLICATION_CREDENTIALS chargée depuis .env.
    """
    return bigquery.Client(project=PROJECT_ID)


def table_ref(table_name: str) -> str:
    """Retourne l'identifiant complet d'une table : project.dataset.table"""
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    schema: Optional[list[bigquery.SchemaField]] = None,
    write_disposition: str = "WRITE_TRUNCATE",
    client: Optional[bigquery.Client] = None,
) -> bigquery.LoadJob:
    """
    Charge un DataFrame pandas dans une table BigQuery.

    Args:
        df: DataFrame à charger
        table_name: nom court de la table (ex. "raw_matches")
        schema: schéma BigQuery (typage explicite des colonnes). Recommandé
                pour la couche raw afin de garantir la cohérence inter-runs.
        write_disposition:
            - "WRITE_TRUNCATE" (défaut) : remplace tout le contenu de la table
            - "WRITE_APPEND" : ajoute les nouvelles lignes
            - "WRITE_EMPTY" : échoue si la table existe déjà
        client: client BigQuery (créé automatiquement si None)

    Returns:
        Le job BigQuery (utile pour récupérer le nombre de lignes chargées).
    """
    client = client or get_bq_client()
    full_table = table_ref(table_name)

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
        schema=schema,
    )

    job = client.load_table_from_dataframe(df, full_table, job_config=job_config)
    job.result()  # bloque jusqu'à la fin du chargement

    table = client.get_table(full_table)
    print(
        f"  → {len(df):>4} lignes chargées dans {full_table}  "
        f"(total table : {table.num_rows} lignes)"
    )
    return job
