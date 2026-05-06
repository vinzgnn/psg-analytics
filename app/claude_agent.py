"""
claude_agent.py — Boucle agentique avec l'API Claude (tool use).

Fonctionnement :
  1. On envoie le message de l'utilisateur à Claude avec la liste des tools.
  2. Claude répond soit directement, soit en demandant d'appeler un tool.
  3. Si tool use → on exécute la fonction Python correspondante.
  4. On renvoie le résultat à Claude → il formule la réponse finale.
  5. On répète jusqu'à ce que Claude réponde sans demander de tool.
"""

import os
import json
import anthropic
from dotenv import load_dotenv

from tools import get_standings, get_psg_matches, get_top_scorers, get_psg_summary

load_dotenv()

# --- Client Anthropic ---
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Modèle utilisé ---
MODEL = "claude-haiku-4-5"

# --- Système prompt ---
SYSTEM_PROMPT = """Tu es un assistant expert du Paris Saint-Germain et de la Ligue 1.
Tu as accès à des données en temps réel via des tools BigQuery.
Réponds toujours en français. Sois concis, précis, et cite les chiffres clés.
Si une question ne concerne pas le football ou les données PSG/L1, indique poliment que tu n'es pas en mesure de répondre."""

# --- Définition des tools exposés à Claude ---
# C'est ici qu'on "déclare" les tools à Claude.
# Il ne voit que le nom, la description et le schema JSON des paramètres.
TOOLS = [
    {
        "name": "get_psg_summary",
        "description": "Retourne les KPIs globaux du PSG pour la saison : victoires, nuls, défaites, buts marqués/encaissés, clean sheets, points totaux. À utiliser pour toute question générale sur la saison du PSG.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_standings",
        "description": "Retourne le classement complet de la Ligue 1 avec position, points, bilan V/N/D et différentiel de buts pour chaque équipe. À utiliser pour toute question sur le classement.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_psg_matches",
        "description": "Retourne tous les matchs joués par le PSG cette saison : adversaire, score, résultat (WIN/DRAW/LOSS), points cumulés, clean sheet. À utiliser pour des questions sur des matchs spécifiques ou la progression du PSG.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_top_scorers",
        "description": "Retourne le top 20 des buteurs et passeurs de Ligue 1 avec buts, passes décisives, contributions totales. Indique aussi si le joueur est au PSG. À utiliser pour toute question sur les stats offensives individuelles.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]

# --- Mapping nom du tool → fonction Python ---
TOOL_FUNCTIONS = {
    "get_psg_summary":  get_psg_summary,
    "get_standings":    get_standings,
    "get_psg_matches":  get_psg_matches,
    "get_top_scorers":  get_top_scorers,
}


def run_agent(user_message: str, verbose: bool = True) -> str:
    """
    Exécute la boucle agentique pour un message utilisateur.
    Retourne la réponse finale de Claude sous forme de string.
    """
    messages = [{"role": "user", "content": user_message}]

    if verbose:
        print(f"\n[USER] {user_message}")

    # Boucle agentique : on tourne jusqu'à ce que Claude arrête de demander des tools
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if verbose:
            print(f"[CLAUDE stop_reason] {response.stop_reason}")

        # --- Cas 1 : Claude a fini de répondre ---
        if response.stop_reason == "end_turn":
            # On extrait le texte de la réponse
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                ""
            )
            if verbose:
                print(f"[CLAUDE] {final_text}")
            return final_text

        # --- Cas 2 : Claude demande d'appeler un ou plusieurs tools ---
        if response.stop_reason == "tool_use":
            # On ajoute la réponse de Claude à l'historique (elle contient les tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # On traite chaque demande de tool
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input

                if verbose:
                    print(f"[TOOL CALL] {tool_name}({tool_input})")

                # On exécute la fonction Python correspondante
                if tool_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[tool_name](**tool_input)
                else:
                    result = {"erreur": f"Tool inconnu : {tool_name}"}

                if verbose:
                    preview = str(result)[:200]
                    print(f"[TOOL RESULT] {preview}...")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })

            # On ajoute les résultats des tools à l'historique et on reboucle
            messages.append({"role": "user", "content": tool_results})

        else:
            # Cas inattendu
            break

    return "Erreur : réponse inattendue de l'API Claude."


# --- Test en ligne de commande ---
if __name__ == "__main__":
    questions = [
        "Comment se porte le PSG cette saison ?",
        "Qui sont les meilleurs buteurs PSG en Ligue 1 ?",
        "Quelle est la position du PSG au classement et quel est son écart avec le 2e ?",
    ]

    for q in questions:
        print("\n" + "="*60)
        run_agent(q, verbose=True)
        print("="*60)
