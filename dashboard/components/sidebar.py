"""Filtros globales persistentes via session_state."""

import streamlit as st
import pandas as pd

from dashboard.config import MATCHES, MATCH_IDS
from dashboard.data.loader import invalidate_cache


def render_filters(aggregated: pd.DataFrame, page: str = "general"):
    """Renderiza filtros en sidebar y devuelve dict con selecciones."""

    st.sidebar.markdown("### Filtros")

    all_labels = [f"{MATCHES[mid]['jornada']} - {MATCHES[mid]['label']}" for mid in MATCH_IDS]
    all_players = sorted(aggregated["player_name"].unique())
    all_profiles = sorted(aggregated["profile"].unique())

    # --- Partidos ---
    if page in ("general", "fisico", "comparativa"):
        selected_labels = st.sidebar.multiselect(
            "Partidos", options=all_labels, default=all_labels,
            key=f"filter_matches_{page}",
        )
        if not selected_labels:
            selected_labels = all_labels
        selected_jornadas = [lbl.split(" - ")[0] for lbl in selected_labels]
        selected_match_ids = [mid for mid in MATCH_IDS
                              if MATCHES[mid]["jornada"] in selected_jornadas]
    elif page == "explorador":
        idx = st.sidebar.selectbox(
            "Partido", options=range(len(all_labels)),
            format_func=lambda i: all_labels[i],
            key="filter_match_explorador",
        )
        selected_match_ids = [MATCH_IDS[idx]]
    else:
        selected_match_ids = MATCH_IDS

    # --- Perfiles ---
    if page in ("general", "comparativa", "fisico"):
        selected_profiles = st.sidebar.multiselect(
            "Posición (perfil)", options=all_profiles, default=all_profiles,
            key=f"filter_profiles_{page}",
        )
        if not selected_profiles:
            selected_profiles = all_profiles
    else:
        selected_profiles = all_profiles

    # --- Jugadores ---
    # Always show full player list (no cascading dependency on profiles).
    # Pages filter by profile AND player independently.
    if page == "individual":
        selected_player = st.sidebar.selectbox(
            "Jugador", options=all_players,
            key="filter_player_individual",
        )
        selected_players = [selected_player]
    elif page in ("comparativa", "fisico", "explorador", "general"):
        label = "Jugadores (2-4)" if page == "comparativa" else "Jugadores"
        selected_players = st.sidebar.multiselect(
            label, options=all_players, default=all_players,
            key=f"filter_players_{page}",
        )
        if not selected_players:
            selected_players = all_players
    else:
        selected_players = all_players

    # --- Min partidos (solo Vista General) ---
    min_matches = 1
    if page == "general":
        min_matches = st.sidebar.slider(
            "Min. partidos jugados",
            min_value=1, max_value=6, value=1,
            key="filter_min_matches",
        )

    # --- Recalcular ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Recalcular datos", key="btn_recalcular"):
        invalidate_cache()
        st.rerun()

    return {
        "match_ids": selected_match_ids,
        "profiles": selected_profiles,
        "players": selected_players,
        "min_matches": min_matches,
    }
