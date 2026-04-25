"""Pagina 3: Comparativa de Jugadores."""

import streamlit as st

from dashboard.config import DIM_COLS, DIM_LABELS, PROFILE_COLORS, COLUMN_LABELS
from dashboard.components.charts import (
    boxplot_consistency,
    evolution_lines,
    grouped_dimension_bars,
    radar_chart,
    scatter_configurable,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.sidebar import render_filters
from dashboard.data.loader import load_aggregated, load_scores

st.title("Comparativa de Jugadores")
st.info(
    "Compara el rendimiento de varios jugadores lado a lado. "
    "Selecciona al menos 2 jugadores en el panel lateral para ver sus diferencias en las 6 dimensiones."
)

scores_all = load_scores()
aggregated = load_aggregated()

filters = render_filters(aggregated, page="comparativa")
players = filters["players"]

if len(players) < 2:
    st.warning("Selecciona al menos 2 jugadores en el panel lateral.")
    st.stop()

agg_filtered = aggregated[aggregated["player_name"].isin(players)].copy()
scores_filtered = scores_all[scores_all["player_name"].isin(players)].copy()

# --- Cards resumen ---
kpis = []
for _, row in agg_filtered.iterrows():
    kpis.append({
        "label": f"{row['player_name']} ({row['profile']})",
        "value": f"{row['composite_score']:.3f}",
        "delta": f"{int(row['n_matches'])} partidos",
    })
# Limit to 4
render_kpi_row(kpis[:4])

st.markdown("---")

# --- Radar + Scatter ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Radar Superpuesto")
    st.caption("Compara visualmente el perfil de cada jugador. Las áreas más grandes indican mejor rendimiento en esa dimensión.")
    fig = radar_chart(agg_filtered)
    # Override names to use player_name
    for i, (_, row) in enumerate(agg_filtered.iterrows()):
        if i < len(fig.data):
            fig.data[i].name = row["player_name"]
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Scatter Configurable")
    st.caption("Cada punto es un jugador. Posición arriba-derecha = mejor en ambos ejes. Elige qué métricas comparar.")
    scatter_options = ["composite_score", "total_minutes", "cv", "n_matches"] + DIM_COLS
    scatter_labels = {
        "composite_score": "Score Compuesto",
        "total_minutes": "Minutos Totales",
        "cv": "Coef. Variación",
        "n_matches": "Partidos",
        **DIM_LABELS,
    }
    c1, c2 = st.columns(2)
    with c1:
        x_col = st.selectbox("Eje X", scatter_options,
                             format_func=lambda x: scatter_labels.get(x, x),
                             index=1, key="scatter_x")
    with c2:
        y_col = st.selectbox("Eje Y", scatter_options,
                             format_func=lambda x: scatter_labels.get(x, x),
                             index=0, key="scatter_y")

    fig = scatter_configurable(agg_filtered, x_col, y_col)
    st.plotly_chart(fig, use_container_width=True)

# --- Barras agrupadas D1-D6 ---
st.markdown("### Comparación por Dimensión")
fig = grouped_dimension_bars(agg_filtered, players)
st.plotly_chart(fig, use_container_width=True)

# --- Boxplot + Evolution ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Consistencia")
    st.caption("La caja muestra la variabilidad del rendimiento: cajas pequeñas = jugador consistente; cajas grandes = rendimiento irregular.")
    if len(scores_filtered) > 0:
        fig = boxplot_consistency(scores_filtered, players)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Evolución")
    st.caption("Cómo evolucionó la nota de cada jugador a lo largo de los partidos analizados.")
    if len(scores_filtered) > 0:
        fig = evolution_lines(scores_filtered, players)
        st.plotly_chart(fig, use_container_width=True)

# --- Tabla ranking ---
st.markdown("### Ranking Completo")
st.caption("Tabla con todas las métricas de los jugadores seleccionados. CV = consistencia (más bajo = más estable).")
display_cols = ["player_name", "profile", "n_matches", "total_minutes",
                "composite_score", "std_dev", "cv"] + DIM_COLS
available_cols = [c for c in display_cols if c in agg_filtered.columns]
st.dataframe(
    agg_filtered[available_cols].sort_values("composite_score", ascending=False).rename(columns=COLUMN_LABELS),
    use_container_width=True,
    hide_index=True,
)
