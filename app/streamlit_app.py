"""
streamlit_app.py — Interface chat Streamlit pour l'assistant PSG.
Utilise la boucle agentique de claude_agent.py.
"""

import os
import json
import streamlit as st
import anthropic
from dotenv import load_dotenv

from tools import get_standings, get_psg_matches, get_top_scorers, get_psg_summary

load_dotenv()

# --- Config page ---
st.set_page_config(
    page_title="Assistant PSG",
    page_icon="⚽",
    layout="centered",
)

# --- Constantes ---
MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = """Tu es un assistant expert du Paris Saint-Germain et de la Ligue 1.
Tu as accès à des données en temps réel via des tools BigQuery.
Réponds toujours en français. Sois concis, précis, et cite les chiffres clés.
Si une question ne concerne pas le football ou les données PSG/L1, indique poliment que tu n'es pas en mesure de répondre."""

TOOLS = [
    {
        "name": "get_psg_summary",
        "description": "Retourne les KPIs globaux du PSG pour la saison : victoires, nuls, défaites, buts marqués/encaissés, clean sheets, points totaux.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_standings",
        "description": "Retourne le classement complet de la Ligue 1 avec position, points, bilan V/N/D et différentiel de buts.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_psg_matches",
        "description": "Retourne tous les matchs joués par le PSG cette saison : adversaire, score, résultat, points cumulés, clean sheet.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_top_scorers",
        "description": "Retourne le top 20 des buteurs et passeurs de Ligue 1 avec buts, passes décisives, contributions totales.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

TOOL_FUNCTIONS = {
    "get_psg_summary":  get_psg_summary,
    "get_standings":    get_standings,
    "get_psg_matches":  get_psg_matches,
    "get_top_scorers":  get_top_scorers,
}

EXEMPLES = [
    "Comment se porte le PSG cette saison ?",
    "Qui sont les meilleurs buteurs PSG ?",
    "Quelle est la position du PSG et l'écart avec le 2e ?",
    "Combien de clean sheets a fait le PSG ?",
    "Qui est le meilleur buteur de Ligue 1 ?",
]


def run_agent(user_message: str) -> str:
    """Boucle agentique — identique à claude_agent.py mais sans verbose."""
    api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = api_client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (block.text for block in response.content if hasattr(block, "text")),
                "Désolé, je n'ai pas pu générer de réponse."
            )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                fn = TOOL_FUNCTIONS.get(block.name)
                result = fn(**block.input) if fn else {"erreur": f"Tool inconnu : {block.name}"}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            messages.append({"role": "user", "content": tool_results})
        else:
            return "Erreur : réponse inattendue de l'API."


# --- Interface ---
st.title("⚽ Assistant PSG")
st.caption("Posez vos questions sur le PSG et la Ligue 1 — données BigQuery en temps réel.")

# Initialisation de l'historique de conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "⚽"):
        st.markdown(msg["content"])

# Exemples cliquables (affichés seulement si pas encore de conversation)
if not st.session_state.messages:
    st.markdown("**Exemples de questions :**")
    cols = st.columns(len(EXEMPLES))
    for col, exemple in zip(cols, EXEMPLES):
        if col.button(exemple, use_container_width=True):
            st.session_state["pending_question"] = exemple
            st.rerun()

# Traitement d'une question cliquée
if "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="⚽"):
        with st.spinner("Analyse en cours…"):
            response = run_agent(user_input)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Zone de saisie
if user_input := st.chat_input("Posez votre question sur le PSG…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="⚽"):
        with st.spinner("Analyse en cours…"):
            response = run_agent(user_input)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
