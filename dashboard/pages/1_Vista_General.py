"""Pagina 1: Vista General del Equipo."""

import streamlit as st

from dashboard.components.charts import (
    dimension_stacked_bar,
    heatmap_jugadores_jornadas,
    ranking_bar,
    team_evolution,
    top5_by_dimension,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.sidebar import render_filters
from dashboard.data.loader import load_aggregated, load_scores

st.title("Vista General del Equipo")
st.info(
    "Esta página muestra un **resumen del rendimiento del equipo**. "
    "Cada jugador recibe una nota de 0 a 1 basada en 6 aspectos de su juego: "
    "progresión, amenaza, movimiento sin balón, defensa, físico y retención del balón."
)

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Ranking General** — Barras horizontales ordenadas de mayor a menor nota global (0 a 1). El color indica la posición del jugador en el campo. Permite identificar de un vistazo quiénes son los jugadores con mejor rendimiento agregado en los 6 partidos analizados.

**Scores por Jugador y Jornada** — Mapa de calor donde cada celda cruza un jugador con una jornada. Verde oscuro indica buen rendimiento, rojo indica rendimiento bajo. Sirve para detectar irregularidades: un jugador con muchas celdas verdes es consistente; columnas enteras en rojo señalan partidos donde todo el equipo rindió mal.

**Evolución Media del Equipo** — Línea que muestra la nota media del equipo partido a partido. Si la línea desciende a lo largo de la temporada, el rendimiento colectivo empeora. Si sube, mejora. Los picos y valles revelan en qué jornadas el equipo estuvo mejor o peor como bloque.

**Desglose por Dimensión y Jornada** — Barras apiladas que muestran cuánto aporta cada dimensión (progresión, amenaza, movimiento sin balón, defensa, físico, retención) a la nota total en cada jornada. Si una dimensión desaparece en un partido concreto, indica que el equipo falló en ese aspecto del juego ese día.

**Top-5 por Dimensión** — Seis subgráficos (uno por dimensión) que muestran los 5 mejores jugadores en cada aspecto. Útil para identificar especialistas: quién es el mejor progresando con balón, quién defiende mejor, quién tiene mayor contribución física, etc.
""")

scores_all = load_scores()
aggregated = load_aggregated()

filters = render_filters(aggregated, page="general")

# Apply filters
agg_filtered = aggregated[
    (aggregated["profile"].isin(filters["profiles"]))
    & (aggregated["n_matches"] >= filters["min_matches"])
    & (aggregated["player_name"].isin(filters["players"]))
].copy()

scores_filtered = scores_all[
    (scores_all["match_id"].isin(filters["match_ids"]))
    & (scores_all["player_name"].isin(agg_filtered["player_name"].tolist()))
].copy()

# --- KPI Row ---
n_players = agg_filtered["player_name"].nunique()
n_matches = len(filters["match_ids"])
avg_score = agg_filtered["composite_score"].mean() if len(agg_filtered) > 0 else 0
best_player = agg_filtered.iloc[0]["player_name"] if len(agg_filtered) > 0 else "-"

render_kpi_row([
    {"label": "Jugadores activos", "value": n_players},
    {"label": "Partidos analizados", "value": n_matches},
    {"label": "Score medio equipo", "value": f"{avg_score:.3f}"},
    {"label": "Mejor jugador", "value": best_player},
])

st.markdown("---")

# --- Row 2: Ranking + Heatmap ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Ranking General")
    fig = ranking_bar(agg_filtered)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Los jugadores están ordenados por su nota global. El color indica su posición en el campo.")

with col2:
    st.markdown("#### Scores por Jugador y Jornada")
    if len(scores_filtered) > 0:
        fig = heatmap_jugadores_jornadas(scores_filtered)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Cada celda muestra la nota del jugador en esa jornada. Verde = buen rendimiento, rojo = bajo rendimiento.")
    else:
        st.info("Sin datos para los filtros seleccionados.")

# --- Row 3: Evolucion + Dimension ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Evolución Media del Equipo")
    if len(scores_filtered) > 0:
        fig = team_evolution(scores_filtered)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Evolución de la nota media del equipo a lo largo de la temporada. Permite ver si el rendimiento colectivo mejora o empeora.")

with col2:
    st.markdown("#### Desglose por Dimensión y Jornada")
    if len(scores_filtered) > 0:
        fig = dimension_stacked_bar(scores_filtered)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Contribución de cada aspecto del juego (dimensión) a la nota total por jornada.")

# --- Row 4: Top-5 por dimension ---
st.markdown("### Top-5 por Dimensión")
st.caption("Los 5 mejores jugadores en cada aspecto del juego. Útil para identificar especialistas en cada área.")
if len(agg_filtered) > 0:
    fig = top5_by_dimension(agg_filtered)
    st.plotly_chart(fig, use_container_width=True)
