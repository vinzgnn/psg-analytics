"""
PSG Analytics — Orchestrateur de collecte

Lance les 3 collecteurs (matchs, classement, scoreurs) dans l'ordre.
À utiliser quotidiennement (manuellement ou via scheduler) pour rafraîchir
toutes les tables raw_*.

Lance-le avec :
    python scripts/collect_all.py
"""

import time

import collect_matches
import collect_scorers
import collect_standings


def main() -> None:
    print("=" * 60)
    print("  PSG Analytics — Pipeline de collecte raw")
    print("=" * 60)

    steps = [
        ("Matchs",      collect_matches.main),
        ("Classement",  collect_standings.main),
        ("Top scoreurs", collect_scorers.main),
    ]

    for i, (label, fn) in enumerate(steps, start=1):
        print(f"\n--- [{i}/{len(steps)}] {label} ---")
        fn()
        # Petite pause pour respecter la limite de 10 req/min du free tier
        if i < len(steps):
            time.sleep(2)

    print("\n" + "=" * 60)
    print("  ✅ Pipeline complet — toutes les tables raw_* sont à jour.")
    print("=" * 60)


if __name__ == "__main__":
    main()
