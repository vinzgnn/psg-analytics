"""
PSG Analytics — Test de connexion à BigQuery

Ce script valide la chaîne :
  .env → service account JSON → google-cloud-bigquery → BigQuery

Lance-le avec :
    python scripts/test_bigquery.py

Pré-requis :
- Le venv .venv est activé
- google-cloud-bigquery est installé (pip install -r requirements.txt)
- .env contient :
    GOOGLE_APPLICATION_CREDENTIALS=/Users/vgenin/.gcp/psg-analytics-key.json
    GCP_PROJECT_ID=psg-analytics-2026
    BIGQUERY_DATASET=psg_analytics
"""

import os
import sys

from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

# ---------------------------------------------------------------
# 1) Charger les variables d'environnement
# ---------------------------------------------------------------
load_dotenv()

CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "psg_analytics")

# Validation des variables
if not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
    print(f"❌ GOOGLE_APPLICATION_CREDENTIALS non valide : {CREDENTIALS_PATH}")
    sys.exit(1)

if not PROJECT_ID:
    print("❌ GCP_PROJECT_ID n'est pas défini dans .env")
    sys.exit(1)


def print_separator(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    print("🔍 Test de connexion BigQuery")
    print(f"   Projet     : {PROJECT_ID}")
    print(f"   Dataset    : {DATASET_ID}")
    print(f"   Clé        : {CREDENTIALS_PATH}")

    # -----------------------------------------------------------
    # 2) Initialiser le client BigQuery
    # -----------------------------------------------------------
    # Le client lit automatiquement la variable GOOGLE_APPLICATION_CREDENTIALS
    # qu'on a chargée via python-dotenv.
    client = bigquery.Client(project=PROJECT_ID)
    print(f"\n✅ Client BigQuery initialisé (compte : {client._credentials.service_account_email})")

    # -----------------------------------------------------------
    # 3) Lister les datasets du projet
    # -----------------------------------------------------------
    print_separator("1. Datasets du projet")
    datasets = list(client.list_datasets())
    if not datasets:
        print("  Aucun dataset trouvé dans ce projet.")
    else:
        for ds in datasets:
            print(f"  • {ds.dataset_id}  ({ds.full_dataset_id})")

    # -----------------------------------------------------------
    # 4) Vérifier que le dataset psg_analytics existe
    # -----------------------------------------------------------
    print_separator(f"2. Détails du dataset '{DATASET_ID}'")
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        dataset = client.get_dataset(dataset_ref)
        print(f"  Nom complet : {dataset.full_dataset_id}")
        print(f"  Région      : {dataset.location}")
        print(f"  Créé le     : {dataset.created.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Description : {dataset.description or '(aucune)'}")

        tables = list(client.list_tables(dataset))
        if tables:
            print(f"  Tables ({len(tables)}) :")
            for t in tables:
                print(f"    - {t.table_id}")
        else:
            print("  Tables       : aucune (normal, on les créera à l'étape 11)")
    except GoogleAPIError as e:
        print(f"❌ Impossible de récupérer le dataset : {e}")
        sys.exit(1)

    # -----------------------------------------------------------
    # 5) Mini-requête de test pour valider l'exécution de jobs
    # -----------------------------------------------------------
    print_separator("3. Mini-requête de test")
    query = """
    SELECT
      'Hello from BigQuery' AS message,
      CURRENT_DATETIME('Europe/Paris') AS heure_paris,
      @project_id AS project_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("project_id", "STRING", PROJECT_ID)]
    )
    rows = list(client.query(query, job_config=job_config).result())
    for row in rows:
        print(f"  Message     : {row.message}")
        print(f"  Heure Paris : {row.heure_paris}")
        print(f"  Projet      : {row.project_id}")

    print("\n✅ Connexion BigQuery validée — service account, permissions et exécution OK.\n")


if __name__ == "__main__":
    try:
        main()
    except GoogleAPIError as e:
        print(f"\n❌ Erreur API Google : {e}")
        if "Permission" in str(e) or "denied" in str(e).lower():
            print("   → Le service account n'a peut-être pas les bons rôles.")
            print("     Vérifie qu'il a bien 'BigQuery Data Editor' + 'BigQuery User'.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {type(e).__name__} : {e}")
        sys.exit(1)
