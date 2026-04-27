"""Pagina 5: Explorador de Eventos (Dynamic Events)."""

import streamlit as st
import pandas as pd

from dashboard.config import (
    MATCHES, MATCH_IDS, EVENT_GLOSSARY, COLUMN_LABELS,
    EVENT_TYPE_ES, EVENT_SUBTYPE_ES, PHASE_ES, PRESSURE_ES,
)
from dashboard.components.charts import (
    event_subtype_bars,
    phase_donut,
    pressure_histogram,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.components.pitch import pitch_heatmap
from dashboard.components.sidebar import render_filters
from dashboard.data.loader import load_aggregated, load_dynamic

st.title("Explorador de Eventos")
st.info(
    "Explora las acciones individuales de cada jugador durante los partidos. "
    "Un **evento** es cada acción registrada: un pase, un regate, una presión al rival, un desmarque, etc."
)

with st.expander("¿Qué significan estos términos?"):
    for term, desc in EVENT_GLOSSARY.items():
        st.markdown(f"- **{term}**: {desc}")

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Heatmap en Campo** — Mapa de calor sobre el terreno de juego que muestra las zonas donde el jugador realizó más acciones. Las zonas rojas indican alta concentración de eventos. Permite verificar si un jugador actúa donde se espera según su posición o si se desplaza a zonas atípicas.

**Distribución de Presión** — Barras agrupadas que muestran cuántas acciones se realizaron bajo cada nivel de presión rival (baja, media, alta, muy alta). Un jugador con muchas acciones bajo presión alta es valiente con balón y capaz de tomar decisiones en contextos exigentes. Si la mayoría de sus acciones son bajo presión baja, recibe el balón en situaciones cómodas.

**Desglose por Fase** — Gráfico de dona que muestra la proporción de acciones según la fase de juego: build-up (construcción desde atrás), create (creación de peligro) y direct (juego directo). Un centrocampista debería tener mucho build-up; un delantero, más create y direct.

**Frecuencia de Subtipos** — Barras horizontales con los tipos de acción más frecuentes: pressing, overlap, support, recovery press, etc. Permite entender el rol táctico real del jugador más allá de su posición nominal. Si un delantero tiene mucho pressing, contribuye defensivamente; si un defensa tiene muchos overlaps, se proyecta al ataque.
""")

aggregated = load_aggregated()
dynamic_sev = load_dynamic()

filters = render_filters(aggregated, page="explorador")

# --- Apply filters ---
df = dynamic_sev[dynamic_sev["match_id"].isin(filters["match_ids"])].copy()

if filters["players"]:
    df = df[df["player_name"].isin(filters["players"])]

# --- Extra filters in sidebar ---
st.sidebar.markdown("---")

event_types = sorted(df["event_type"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Tipo de evento",
    options=event_types,
    default=event_types,
    format_func=lambda x: EVENT_TYPE_ES.get(x, x),
    key="filter_event_type",
)
df = df[df["event_type"].isin(selected_types)]

if "event_subtype" in df.columns:
    subtypes = sorted(df["event_subtype"].dropna().unique().tolist())
    selected_subtypes = st.sidebar.multiselect(
        "Subtipo",
        options=subtypes,
        default=subtypes,
        format_func=lambda x: EVENT_SUBTYPE_ES.get(x, x),
        key="filter_event_subtype",
    )
    df = df[df["event_subtype"].isin(selected_subtypes) | df["event_subtype"].isna()]

# Phase filter
if "team_in_possession_phase_type" in df.columns:
    phases = sorted(df["team_in_possession_phase_type"].dropna().unique().tolist())
    if phases:
        selected_phases = st.sidebar.multiselect(
            "Fase TIP",
            options=phases,
            default=phases,
            format_func=lambda x: PHASE_ES.get(x, x),
            key="filter_phase_tip",
        )
        df = df[df["team_in_possession_phase_type"].isin(selected_phases) | df["team_in_possession_phase_type"].isna()]

# Pressure filter
if "overall_pressure_start" in df.columns:
    pressure_levels = ["no_pressure", "low_pressure", "medium_pressure",
                        "high_pressure", "very_high_pressure"]
    available_pressures = [p for p in pressure_levels if p in df["overall_pressure_start"].values]
    if available_pressures:
        selected_pressures = st.sidebar.multiselect(
            "Nivel de presión",
            options=available_pressures,
            default=available_pressures,
            format_func=lambda x: PRESSURE_ES.get(x, x),
            key="filter_pressure",
        )
        df = df[df["overall_pressure_start"].isin(selected_pressures) | df["overall_pressure_start"].isna()]

if df.empty:
    st.warning("Sin eventos para los filtros seleccionados.")
    st.stop()

# --- KPI Row ---
n_events = len(df)
xthreat_mean = df["player_targeted_xthreat"].mean() if "player_targeted_xthreat" in df.columns else 0
line_breaks = 0
for col in ["first_line_break", "second_last_line_break", "last_line_break"]:
    if col in df.columns:
        line_breaks += (df[col] == True).sum()

render_kpi_row([
    {"label": "Eventos filtrados", "value": f"{n_events:,}"},
    {"label": "xThreat medio", "value": f"{xthreat_mean:.4f}" if pd.notna(xthreat_mean) else "N/A"},
    {"label": "Roturas de línea", "value": int(line_breaks)},
    {"label": "Jugadores", "value": df["player_name"].nunique()},
])

st.markdown("---")

# --- Row 1: Pitch heatmap + Pressure ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Heatmap en Campo")
    if "x_start" in df.columns:
        match_label = MATCHES[filters["match_ids"][0]]["label"] if len(filters["match_ids"]) == 1 else "Todos"
        fig = pitch_heatmap(df, title=f"Ubicaciones - {match_label}")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Zonas calientes (rojo) = donde el jugador realizó más acciones. Útil para ver su radio de acción.")
    else:
        st.info("Sin coordenadas posicionales.")

with col2:
    st.markdown("#### Distribución de Presión")
    fig = pressure_histogram(df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Cuántas acciones se realizaron bajo cada nivel de presión rival. Más acciones bajo presión alta = jugador valiente con balón.")

# --- Row 2: Phase donut + Subtype bars ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Desglose por Fase")
    fig = phase_donut(df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Proporción de acciones por fase: build_up (construcción desde atrás), create (creación de peligro), direct (juego directo).")

with col2:
    st.markdown("#### Frecuencia de Subtipos")
    fig = event_subtype_bars(df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Los tipos de acción más frecuentes: pressing (presión), overlap (desmarque por fuera), support (apoyo), etc.")

# --- Events table ---
st.markdown("### Eventos Filtrados")
display_cols = ["player_name", "event_type", "event_subtype", "match_id"]
optional_cols = ["x_start", "y_start", "x_end", "y_end",
                 "overall_pressure_start", "team_in_possession_phase_type",
                 "player_targeted_xthreat", "lead_to_shot", "lead_to_goal"]
for c in optional_cols:
    if c in df.columns:
        display_cols.append(c)

events_display = df[display_cols].head(500).copy()
events_display["match_id"] = events_display["match_id"].map(
    lambda x: f"{MATCHES[x]['jornada']} {MATCHES[x]['label']}" if x in MATCHES else str(x)
)
events_display["event_type"] = events_display["event_type"].map(lambda x: EVENT_TYPE_ES.get(x, x) if pd.notna(x) else x)
if "event_subtype" in events_display.columns:
    events_display["event_subtype"] = events_display["event_subtype"].map(lambda x: EVENT_SUBTYPE_ES.get(x, x) if pd.notna(x) else x)
if "team_in_possession_phase_type" in events_display.columns:
    events_display["team_in_possession_phase_type"] = events_display["team_in_possession_phase_type"].map(lambda x: PHASE_ES.get(x, x) if pd.notna(x) else x)
if "overall_pressure_start" in events_display.columns:
    events_display["overall_pressure_start"] = events_display["overall_pressure_start"].map(lambda x: PRESSURE_ES.get(x, x) if pd.notna(x) else x)
events_display = events_display.rename(columns=COLUMN_LABELS)

st.dataframe(
    events_display,
    use_container_width=True,
    hide_index=True,
    height=400,
)
st.caption(f"Mostrando {min(500, len(df))} de {len(df)} eventos.")
