"""Pagina 4: Dashboard de Rendimiento Fisico."""

import streamlit as st

from dashboard.config import PHYS_TO_DYN, PHYSICAL_GLOSSARY, MATCHES, COLUMN_LABELS, label
from dashboard.components.charts import (
    evolution_lines,
    physical_bar,
    physical_heatmap,
    physical_scatter,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.sidebar import render_filters
from dashboard.data.loader import load_aggregated, load_physical_raw

st.title("Datos Físicos")
st.info(
    "Datos de rendimiento físico obtenidos por tracking de vídeo (SkillCorner). "
    "Incluyen distancia recorrida, sprints, velocidad máxima, aceleraciones y agilidad."
)

with st.expander("¿Qué significan estas métricas?"):
    for term, desc in PHYSICAL_GLOSSARY.items():
        st.markdown(f"- **{term}**: {desc}")

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Comparación por Métrica** — Barras horizontales que muestran el valor de la métrica física seleccionada para cada jugador. Las barras más largas indican mayor rendimiento en esa métrica. Cambiar entre M/min, HSR, Sprint o PSV-99 permite ver quién lidera en cada aspecto físico.

**Heatmap Físico** — Mapa de calor que cruza jugadores con varias métricas físicas normalizadas de 0 a 1. Colores más intensos significan valores más altos respecto al grupo. Permite identificar perfiles físicos de un vistazo: un jugador con toda la fila intensa es un atleta completo; uno con solo una columna intensa es especialista.

**Intensidad vs Alta Velocidad** — Scatter que cruza metros por minuto (eje X) con distancia a alta velocidad HSR (eje Y). Los jugadores arriba a la derecha combinan alta intensidad general con mucha carrera a alta velocidad. Los que están abajo a la derecha corren mucho pero a ritmo bajo. Los de arriba a la izquierda hacen menos volumen pero con picos de velocidad.

**Sprint vs Agilidad** — Scatter que cruza distancia de sprint (eje X) con cambios de dirección (eje Y). Un jugador arriba a la derecha es explosivo y ágil: sprinta mucho y cambia de dirección frecuentemente. Este perfil es típico de extremos y laterales ofensivos. Centrales y mediocentros suelen aparecer más abajo a la izquierda.
""")

aggregated = load_aggregated()
physical = load_physical_raw()

# --- Metric groups (sidebar, justo debajo de la navegación) ---
METRIC_GROUPS = {
    "Volumen": ["Distance", "M/min", "Running Distance"],
    "HSR": ["HSR Distance", "HSR Distance P90", "HSR Count", "HSR Count P90"],
    "Sprint": ["Sprint Distance", "Sprint Distance P90", "Sprint Count", "Sprint Count P90", "PSV-99"],
    "Aceleración": ["High Acceleration Count", "High Acceleration Count P90",
                     "High Deceleration Count", "High Deceleration Count P90"],
    "Agilidad": ["Change of Direction Count"],
}

st.sidebar.markdown("#### Métricas físicas")
raw_p90 = st.sidebar.toggle("Mostrar P90", value=True, key="toggle_p90")
metric_group = st.sidebar.selectbox(
    "Grupo de métricas",
    options=list(METRIC_GROUPS.keys()),
    key="metric_group",
)

selected_metrics = METRIC_GROUPS[metric_group]
if raw_p90:
    selected_metrics = [m for m in selected_metrics if "P90" in m] or selected_metrics
selected_metrics = [m for m in selected_metrics if m in physical.columns]

# --- Filtros generales ---
filters = render_filters(aggregated, page="fisico")

# Only players with physical data
players_with_phys = physical["dyn_name"].dropna().unique().tolist()
selected_players = [p for p in filters["players"] if p in players_with_phys]

# Filter by matches
phys_filtered = physical[
    (physical["match_id"].isin(filters["match_ids"]))
    & (physical["dyn_name"].isin(selected_players))
].copy()

# --- Availability notice ---
n_with_data = len(selected_players)
n_total = len(filters["players"])
if n_with_data < n_total:
    st.info(f"{n_with_data} de {n_total} jugadores seleccionados tienen datos físicos.")

if phys_filtered.empty:
    st.warning("Sin datos físicos para los filtros seleccionados.")
    st.stop()

# --- KPI Row ---
mmin_mean = phys_filtered["M/min"].mean() if "M/min" in phys_filtered.columns else 0
psv99_max = phys_filtered["PSV-99"].max() if "PSV-99" in phys_filtered.columns else 0
hsr_p90_mean = phys_filtered["HSR Distance P90"].mean() if "HSR Distance P90" in phys_filtered.columns else 0

render_kpi_row([
    {"label": "Jugadores con datos", "value": n_with_data},
    {"label": "Media M/min", "value": f"{mmin_mean:.1f}"},
    {"label": "Max PSV-99", "value": f"{psv99_max:.1f}"},
    {"label": "Media HSR P90", "value": f"{hsr_p90_mean:.0f}"},
])

st.markdown("---")

# --- Row 1: Bar + Heatmap ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Comparación por Métrica")
    metric_to_show = st.selectbox(
        "Métrica para barras",
        options=selected_metrics,
        format_func=label,
        key="bar_metric",
    )
    fig = physical_bar(phys_filtered, metric_to_show, selected_players)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Comparación de la métrica seleccionada entre jugadores. Barras más largas = mayor valor.")

with col2:
    st.markdown("#### Heatmap Físico")
    fig = physical_heatmap(phys_filtered, selected_metrics, selected_players)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Colores más intensos = valores más altos respecto al grupo. Los valores están normalizados para facilitar la comparación.")

# --- Row 2: Scatters ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Intensidad vs Alta Velocidad")
    x_m = "M/min" if "M/min" in phys_filtered.columns else (selected_metrics[0] if selected_metrics else None)
    y_m = "HSR Distance" if "HSR Distance" in phys_filtered.columns else (selected_metrics[-1] if selected_metrics else None)
    if x_m and y_m:
        fig = physical_scatter(phys_filtered, x_m, y_m, selected_players)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Cada punto es un jugador. Arriba-derecha = mayor intensidad y más carrera a alta velocidad.")

with col2:
    st.markdown("#### Sprint vs Agilidad")
    x_m2 = "Sprint Distance" if "Sprint Distance" in phys_filtered.columns else None
    y_m2 = "Change of Direction Count" if "Change of Direction Count" in phys_filtered.columns else None
    if x_m2 and y_m2:
        fig = physical_scatter(phys_filtered, x_m2, y_m2, selected_players)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Arriba-derecha = jugador que combina distancia de sprint con cambios de dirección frecuentes.")

# --- Raw data table ---
st.markdown("### Datos Crudos")
st.caption("Valores originales sin procesar. Útil para análisis detallado o exportación.")
display_cols = ["dyn_name", "match_id"] + [m for m in selected_metrics if m in phys_filtered.columns]
phys_display = phys_filtered[display_cols].copy()
phys_display["match_id"] = phys_display["match_id"].map(
    lambda x: f"{MATCHES[x]['jornada']} {MATCHES[x]['label']}" if x in MATCHES else str(x)
)
phys_display = phys_display.rename(columns=COLUMN_LABELS)
st.dataframe(
    phys_display,
    use_container_width=True,
    hide_index=True,
    column_config={label(col): st.column_config.NumberColumn(format="%.1f") for col in selected_metrics if label(col) in phys_display.columns},
)
