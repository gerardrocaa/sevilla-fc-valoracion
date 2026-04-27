"""Pagina 2: Perfil Individual del Jugador."""

import streamlit as st
import pandas as pd

from dashboard.config import DIM_COLS, DIM_LABELS, PROFILE_COLORS, MATCHES, PROFILE_DESCRIPTIONS, DIM_DESCRIPTIONS, KPI_HELP, COLUMN_LABELS
from dashboard.components.charts import (
    evolution_lines,
    radar_chart,
    radar_vs_team,
    grouped_dimension_bars,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.pitch import pitch_heatmap
from dashboard.components.sidebar import render_filters
from dashboard.data.loader import load_aggregated, load_scores, load_dynamic

st.title("Perfil Individual")
st.info(
    "Perfil detallado de un jugador. Muestra sus fortalezas y debilidades "
    "en 6 dimensiones, su evolución a lo largo de la temporada y cómo se compara con la media del equipo."
)

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Radar por Partido** — Cada polígono representa el perfil del jugador en un partido concreto. Las 6 puntas corresponden a las 6 dimensiones de rendimiento. Un polígono grande y equilibrado indica un jugador completo ese día; uno deformado señala fortalezas y debilidades claras. Superponer varios partidos revela si el jugador mantiene su perfil o varía mucho.

**vs Media del Equipo** — Compara el perfil del jugador (rojo) con la media de toda la plantilla (gris). Las dimensiones donde el jugador sobresale por fuera del gris son sus fortalezas relativas al equipo. Donde queda por dentro, está por debajo de la media.

**Evolución Temporal** — Línea que muestra cómo varía la nota del jugador partido a partido. Una línea ascendente indica mejora progresiva. Caídas bruscas pueden señalar fatiga, lesión o un rival especialmente exigente. La estabilidad de la línea refleja la consistencia del jugador.

**Dimensiones vs Media Equipo** — Barras agrupadas que comparan las 6 dimensiones del jugador con la media del equipo, una junto a otra. Es la versión numérica exacta del radar: permite cuantificar cuánto por encima o por debajo de la media está en cada aspecto.

**Heatmap Posicional** — Mapa de calor sobre el campo de fútbol que muestra dónde realizó más acciones el jugador. Las zonas rojas indican alta actividad. Permite verificar si el jugador ocupa las zonas esperadas según su posición o si tiende a desplazarse a otras áreas.
""")

scores_all = load_scores()
aggregated = load_aggregated()

filters = render_filters(aggregated, page="individual")
player = filters["players"][0] if filters["players"] else None

if not player:
    st.warning("Selecciona un jugador en el panel lateral.")
    st.stop()

# Player data
p_agg = aggregated[aggregated["player_name"] == player]
if p_agg.empty:
    st.warning(f"No hay datos agregados para {player}.")
    st.stop()

p_agg = p_agg.iloc[0]
p_scores = scores_all[scores_all["player_name"] == player].copy()

# --- Header ---
profile = p_agg["profile"]
color = PROFILE_COLORS.get(profile, "#999")
profile_desc = PROFILE_DESCRIPTIONS.get(profile, profile)
st.markdown(
    f"### {player} "
    f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;'
    f'font-size:0.85rem;">{profile} — {profile_desc}</span>',
    unsafe_allow_html=True,
)

# --- KPI ---
best_dim = max(DIM_COLS, key=lambda d: p_agg.get(d, 0) if pd.notna(p_agg.get(d, 0)) else 0)
render_kpi_row([
    {"label": "Score Compuesto", "value": f"{p_agg['composite_score']:.4f}"},
    {"label": "Partidos", "value": int(p_agg["n_matches"])},
    {"label": "Minutos totales", "value": int(p_agg["total_minutes"])},
    {"label": "Mejor dimension", "value": DIM_LABELS[best_dim]},
])

with st.expander("¿Qué significan estos indicadores?"):
    st.markdown(f"- **Score Compuesto**: {KPI_HELP['Score Compuesto']}")
    st.markdown(f"- **Mejor dimensión**: {KPI_HELP['Mejor dimension']}")
    st.markdown(f"- **Posición ({profile})**: {profile_desc}")

st.markdown("---")

# --- Radar charts ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Radar por Partido")
    st.caption("El radar muestra las 6 dimensiones del jugador. Cuanto más se extiende hacia fuera, mejor es en ese aspecto.")
    # Multiselect for matches to show in radar
    available_matches = p_scores["match_label"].unique().tolist()
    selected_matches = st.multiselect(
        "Partidos en radar",
        options=available_matches,
        default=available_matches,
        key="radar_matches",
    )
    radar_data = p_scores[p_scores["match_label"].isin(selected_matches)]
    if len(radar_data) > 0:
        fig = radar_chart(radar_data)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### vs Media del Equipo")
    st.caption("Compara el perfil del jugador (rojo) con la media del equipo (gris). Las áreas donde el jugador sobresale se extienden más.")
    team_avg = aggregated[DIM_COLS].mean()
    fig = radar_vs_team(p_agg, team_avg, player_name=player)
    st.plotly_chart(fig, use_container_width=True)

# --- Evolution ---
st.markdown("### Evolución Temporal")
st.caption("Cómo ha variado la nota del jugador partido a partido. Permite detectar mejoras, bajones o irregularidad.")
dim_option = st.selectbox(
    "Dimension",
    options=["composite_score"] + DIM_COLS,
    format_func=lambda x: "Score Compuesto" if x == "composite_score" else DIM_LABELS.get(x, x),
    key="evo_dim",
)
fig = evolution_lines(scores_all, [player], col=dim_option)
st.plotly_chart(fig, use_container_width=True)

# --- Dimension bars + heatmap posicional ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Dimensiones vs Media Equipo")
    st.caption("Barras agrupadas: compara la nota del jugador en cada dimensión con la media del equipo.")
    fig = grouped_dimension_bars(
        pd.concat([
            aggregated[aggregated["player_name"] == player],
            pd.DataFrame([{
                "player_name": "Media equipo",
                "profile": "DM",
                **{d: aggregated[d].mean() for d in DIM_COLS},
            }]),
        ]),
        [player, "Media equipo"],
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Heatmap Posicional")
    st.caption("Zonas del campo donde el jugador realizó más acciones. Rojo = mayor actividad.")
    dynamic_sev = load_dynamic()
    player_events = dynamic_sev[dynamic_sev["player_name"] == player]
    if len(player_events) > 0 and "x_start" in player_events.columns:
        fig = pitch_heatmap(player_events, title=f"Posiciones - {player}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos posicionales para este jugador.")

# --- Detail table ---
st.markdown("### Detalle por Partido")
detail_cols = ["jornada", "match_label", "minutes_played", "profile"] + DIM_COLS + ["composite_score"]
available_cols = [c for c in detail_cols if c in p_scores.columns]
st.dataframe(
    p_scores[available_cols].sort_values("jornada").rename(columns=COLUMN_LABELS),
    use_container_width=True,
    hide_index=True,
)
