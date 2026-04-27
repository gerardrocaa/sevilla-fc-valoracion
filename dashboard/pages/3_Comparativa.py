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

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Radar Superpuesto** — Varios polígonos superpuestos, uno por jugador seleccionado. Permite ver de un vistazo quién domina en qué dimensiones. El jugador con el polígono más grande tiene mejor rendimiento general; las diferencias de forma revelan perfiles complementarios o redundantes.

**Scatter Configurable** — Cada punto es un jugador. Los ejes se pueden configurar libremente. La posición arriba a la derecha es la mejor en ambas métricas. Útil para cruzar variables como minutos jugados vs rendimiento, o dimensión física vs defensiva, y detectar outliers.

**Comparación por Dimensión** — Barras agrupadas que muestran las 6 dimensiones de cada jugador lado a lado. Permite comparar numéricamente en qué dimensiones uno supera al otro. Ideal para decidir entre dos jugadores que compiten por un puesto.

**Consistencia** — Diagrama de caja (boxplot) que muestra la dispersión de notas de cada jugador a lo largo de los partidos. Una caja pequeña indica un jugador predecible y estable. Una caja grande con bigotes largos indica alta variabilidad: puede brillar un día y desaparecer al siguiente.

**Evolución** — Líneas superpuestas que muestran la trayectoria de cada jugador partido a partido. Permite ver si sus rendimientos se mueven en paralelo (afectados por el mismo contexto de equipo) o de forma independiente. Los cruces de líneas señalan cambios de jerarquía entre jornadas.
""")

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
