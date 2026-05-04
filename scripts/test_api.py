"""
PSG Analytics — Test du premier appel à l'API football-data.org

Ce script valide la chaîne :
  .env (token)  →  python-dotenv  →  requests  →  API football-data.org  →  données PSG

Lance-le avec :
    python scripts/test_api.py

Pré-requis :
- Le venv .venv est activé
- Un fichier .env contient FOOTBALL_DATA_API_KEY=<ton_token>
"""

import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------
# 1) Charger les variables d'environnement depuis .env
# ---------------------------------------------------------------
load_dotenv()

API_TOKEN = os.getenv("FOOTBALL_DATA_API_KEY")

if not API_TOKEN or API_TOKEN == "ton_token_ici":
    print("❌ Erreur : FOOTBALL_DATA_API_KEY n'est pas défini dans le fichier .env")
    print("   Vérifie que le fichier .env existe et contient ton token football-data.org.")
    sys.exit(1)

# ---------------------------------------------------------------
# 2) Constantes API
# ---------------------------------------------------------------
BASE_URL = "https://api.football-data.org/v4"
PSG_TEAM_ID = 524        # Paris Saint-Germain FC
LIGUE1_CODE = "FL1"      # Code compétition Ligue 1

HEADERS = {"X-Auth-Token": API_TOKEN}


# ---------------------------------------------------------------
# 3) Fonctions d'appel API
# ---------------------------------------------------------------
def get_team_info(team_id: int) -> dict:
    """Récupère les informations générales d'une équipe."""
    url = f"{BASE_URL}/teams/{team_id}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def get_recent_matches(team_id: int, limit: int = 5) -> list[dict]:
    """Récupère les derniers matchs JOUÉS (status FINISHED) d'une équipe."""
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {"status": "FINISHED", "limit": limit}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("matches", [])


def get_ligue1_standings() -> list[dict]:
    """Récupère le classement actuel de la Ligue 1."""
    url = f"{BASE_URL}/competitions/{LIGUE1_CODE}/standings"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()
    # On récupère uniquement le classement général (TOTAL)
    for table in data.get("standings", []):
        if table.get("type") == "TOTAL":
            return table.get("table", [])
    return []


# ---------------------------------------------------------------
# 4) Affichage lisible des résultats
# ---------------------------------------------------------------
def print_separator(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    print("🔍 Test de l'API football-data.org pour le PSG")
    print(f"   Token chargé : {API_TOKEN[:6]}...{API_TOKEN[-4:]}  (masqué)")

    # --- A. Infos équipe PSG ---
    print_separator("1. Informations sur le PSG")
    team = get_team_info(PSG_TEAM_ID)
    print(f"  Nom         : {team.get('name')}")
    print(f"  Surnom      : {team.get('shortName')}")
    print(f"  Stade       : {team.get('venue')}")
    print(f"  Fondé en    : {team.get('founded')}")
    print(f"  Site web    : {team.get('website')}")
    print(f"  Couleurs    : {team.get('clubColors')}")

    # --- B. 5 derniers matchs ---
    print_separator("2. Les 5 derniers matchs joués")
    matches = get_recent_matches(PSG_TEAM_ID, limit=5)
    if not matches:
        print("  Aucun match récent trouvé.")
    else:
        for m in matches:
            date = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).strftime("%d/%m/%Y")
            home = m["homeTeam"]["shortName"]
            away = m["awayTeam"]["shortName"]
            score_home = m["score"]["fullTime"]["home"]
            score_away = m["score"]["fullTime"]["away"]
            competition = m["competition"]["name"]
            print(f"  {date}  |  {home:>20}  {score_home}-{score_away}  {away:<20}  ({competition})")

    # --- C. Classement Ligue 1 (top 5 + ligne PSG) ---
    print_separator("3. Classement Ligue 1 (top 5)")
    standings = get_ligue1_standings()
    if not standings:
        print("  Classement non disponible.")
    else:
        print(f"  {'Pos':>3}  {'Équipe':<25}  {'J':>3}  {'Pts':>4}  {'BP':>3}  {'BC':>3}  {'Diff':>4}")
        print(f"  {'-'*3}  {'-'*25}  {'-'*3}  {'-'*4}  {'-'*3}  {'-'*3}  {'-'*4}")
        for row in standings[:5]:
            print(
                f"  {row['position']:>3}  "
                f"{row['team']['shortName']:<25}  "
                f"{row['playedGames']:>3}  "
                f"{row['points']:>4}  "
                f"{row['goalsFor']:>3}  "
                f"{row['goalsAgainst']:>3}  "
                f"{row['goalDifference']:>+4}"
            )
        # Ligne PSG si pas dans le top 5
        psg_row = next((r for r in standings if r["team"]["id"] == PSG_TEAM_ID), None)
        if psg_row and psg_row["position"] > 5:
            print("  ...")
            print(
                f"  {psg_row['position']:>3}  "
                f"{psg_row['team']['shortName']:<25}  "
                f"{psg_row['playedGames']:>3}  "
                f"{psg_row['points']:>4}  "
                f"{psg_row['goalsFor']:>3}  "
                f"{psg_row['goalsAgainst']:>3}  "
                f"{psg_row['goalDifference']:>+4}"
            )

    print("\n✅ Test terminé avec succès — l'API répond, le token fonctionne.\n")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"\n❌ Erreur HTTP : {e}")
        print(f"   Réponse : {e.response.text if e.response is not None else 'N/A'}")
        if e.response is not None and e.response.status_code == 403:
            print("   → Vérifie que ton token est correct dans .env")
        if e.response is not None and e.response.status_code == 429:
            print("   → Limite de 10 requêtes/minute dépassée. Attends une minute.")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"\n❌ Erreur réseau : {e}")
        sys.exit(1)
