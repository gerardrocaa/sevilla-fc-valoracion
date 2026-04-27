"""Pagina 7: Fatiga y Riesgo de Lesion."""

import streamlit as st

from dashboard.config import INFERENCE_GLOSSARY, MATCHES, COLUMN_LABELS, RISK_COLORS, RISK_LABELS, label
from dashboard.components.charts_inference import (
    fatigue_cumulative_bar,
    fatigue_evolution_lines,
    psv99_trend_lines,
    risk_factors_bar,
    risk_semaphore_chart,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import load_fatigue, load_fatigue_stats, load_risk

st.title("Fatiga y Riesgo de Lesión")
st.info(
    "Análisis de fatiga acumulada y riesgo de lesión basado en datos físicos de tracking. "
    "La fatiga combina caída de velocidad máxima, reducción de HSR y acumulación de carga. "
    "El riesgo evalúa ACWR, picos de carga y cambios en PSV-99."
)

with st.expander("Glosario de términos"):
    for term, desc in INFERENCE_GLOSSARY.items():
        if term in ("ACWR", "Índice de fatiga", "Riesgo de lesión", "IC 95%"):
            st.markdown(f"- **{term}**: {desc}")

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Evolución del Índice de Fatiga** — Líneas que muestran el índice de fatiga (0 = fresco, 1 = fatigado) de cada jugador partido a partido. Una tendencia ascendente sostenida indica acumulación de fatiga a lo largo de la temporada. Picos repentinos pueden señalar partidos de alta exigencia o recuperación insuficiente entre jornadas.

**Tendencia PSV-99** — Líneas que muestran la velocidad máxima de sprint (PSV-99) por partido. Caídas sostenidas en esta métrica son un indicador de fatiga neuromuscular: el jugador pierde capacidad explosiva. Si la PSV-99 cae mientras la fatiga sube, la señal de alarma es clara.

**Carga Acumulada Total** — Barras horizontales que suman la carga total (distancia + HSR + sprint) de cada jugador a lo largo de los 6 partidos. Jugadores con barras más largas han acumulado más desgaste físico. Junto con el índice de fatiga, ayuda a priorizar quién necesita descanso.

**Semáforo de Riesgo** — Barras coloreadas según el nivel de riesgo de lesión: verde (bajo, < 0,33), amarillo (medio, 0,33-0,66) y rojo (alto, > 0,66). Se basa en ACWR, cambios en PSV-99, picos de carga y variabilidad. Los jugadores en amarillo o rojo son candidatos a rotación o gestión de minutos.

**Factores de Riesgo** — Barras horizontales que desglosan los componentes del riesgo para un jugador concreto: ACWR, cambio de PSV-99, cambio de carga y ratio de sprint. Las barras en rojo indican valores en zona de riesgo. Permite entender qué factor específico está elevando el riesgo de ese jugador.
""")

# --- Load data ---
fatigue_df = load_fatigue()
fatigue_stats = load_fatigue_stats()
risk_df = load_risk()

# --- Tabs ---
tab_fatiga, tab_riesgo = st.tabs(["Fatiga", "Riesgo de Lesión"])

# ===================== TAB FATIGA =====================
with tab_fatiga:
    if fatigue_df.empty:
        st.warning("Sin datos de fatiga disponibles.")
    else:
        # Player filter
        all_players = sorted(fatigue_df["dyn_name"].unique())
        selected_players = st.multiselect(
            "Jugadores", options=all_players, default=all_players,
            key="fatigue_players",
        )
        if not selected_players:
            selected_players = all_players

        filtered = fatigue_df[fatigue_df["dyn_name"].isin(selected_players)]

        # KPIs
        avg_fatigue = filtered["fatigue_index"].mean()
        max_fatigue_player = filtered.loc[filtered["fatigue_index"].idxmax(), "dyn_name"] if not filtered.empty else "-"
        max_load = filtered["cumulative_load"].max() if "cumulative_load" in filtered.columns else 0
        n_players = filtered["dyn_name"].nunique()

        render_kpi_row([
            {"label": "Jugadores", "value": n_players},
            {"label": "Fatiga media", "value": f"{avg_fatigue:.3f}"},
            {"label": "Más fatigado", "value": max_fatigue_player},
            {"label": "Carga máx. acumulada", "value": f"{max_load:,.0f} m"},
        ])

        st.markdown("---")

        # Row 1: Fatigue lines + PSV-99 trend
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Evolución del Índice de Fatiga")
            fig = fatigue_evolution_lines(filtered, selected_players)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Evolución del índice de fatiga (0 = fresco, 1 = fatigado) "
                "partido a partido. Tendencias ascendentes indican acumulación de fatiga."
            )

        with col2:
            st.markdown("#### Tendencia PSV-99")
            fig = psv99_trend_lines(filtered, selected_players)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Velocidad máxima de sprint (PSV-99) por partido. "
                "Caídas sostenidas pueden indicar fatiga neuromuscular."
            )

        # Row 2: Cumulative load
        st.markdown("#### Carga Acumulada Total")
        fig = fatigue_cumulative_bar(filtered, selected_players)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Suma total de distancia + HSR + sprint a lo largo de los 6 partidos.")

        # Fatigue stats table
        if not fatigue_stats.empty:
            st.markdown("### Modelo de Fatiga (Regresión Lineal)")
            st.caption(
                "Regresión del índice de fatiga vs jornada. "
                "Pendiente positiva = fatiga creciente. R² indica ajuste del modelo."
            )
            stats_display = fatigue_stats[fatigue_stats["dyn_name"].isin(selected_players)].copy()
            stats_display = stats_display.rename(columns={
                "dyn_name": "Jugador", "r2": "R²", "slope": "Pendiente",
                "p_value": "p-valor", "ci_lower": "IC inferior",
                "ci_upper": "IC superior", "n_matches": "Partidos",
            })
            st.dataframe(
                stats_display, use_container_width=True, hide_index=True,
                column_config={
                    "R²": st.column_config.NumberColumn(format="%.4f"),
                    "Pendiente": st.column_config.NumberColumn(format="%.4f"),
                    "p-valor": st.column_config.NumberColumn(format="%.4f"),
                    "IC inferior": st.column_config.NumberColumn(format="%.4f"),
                    "IC superior": st.column_config.NumberColumn(format="%.4f"),
                },
            )


# ===================== TAB RIESGO =====================
with tab_riesgo:
    if risk_df.empty:
        st.warning("Sin datos de riesgo disponibles.")
    else:
        # Separate players with enough data from those without
        risk_evaluated = risk_df[risk_df["risk_level"] != "sin_datos"].copy()
        risk_no_data = risk_df[risk_df["risk_level"] == "sin_datos"].copy()

        n_bajo = (risk_evaluated["risk_level"] == "bajo").sum()
        n_medio = (risk_evaluated["risk_level"] == "medio").sum()
        n_alto = (risk_evaluated["risk_level"] == "alto").sum()
        n_evaluated = len(risk_evaluated)

        render_kpi_row([
            {"label": "Jugadores evaluados", "value": n_evaluated},
            {"label": "Riesgo bajo", "value": n_bajo},
            {"label": "Riesgo medio", "value": n_medio},
            {"label": "Riesgo alto", "value": n_alto},
        ])

        if not risk_no_data.empty:
            st.caption(f"{len(risk_no_data)} jugadores excluidos por tener solo 1 partido (sin datos comparativos).")

        st.markdown("---")

        if risk_evaluated.empty:
            st.info("Ningún jugador tiene suficientes partidos para evaluar riesgo.")
        else:
            # Semaphore chart
            st.markdown("#### Semáforo de Riesgo")
            fig = risk_semaphore_chart(risk_evaluated)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Verde = riesgo bajo (< 0.33), amarillo = medio (0.33 - 0.66), rojo = alto (> 0.66). "
                "Basado en ACWR, cambios en PSV-99, picos de carga y variabilidad."
            )

            # Player detail
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Detalle por Jugador")
                selected_player = st.selectbox(
                    "Seleccionar jugador",
                    options=sorted(risk_evaluated["dyn_name"].unique()),
                    key="risk_player_detail",
                )

            with col2:
                st.markdown("#### Factores de Riesgo")
                fig = risk_factors_bar(risk_evaluated, selected_player)
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Valores en zona de riesgo se muestran en rojo.")

        # Risk table (show all, including sin_datos)
        st.markdown("### Tabla de Riesgo")
        risk_display = risk_df.copy()
        risk_display["risk_level"] = risk_display["risk_level"].map(
            {"bajo": "Bajo", "medio": "Medio", "alto": "Alto", "sin_datos": "Sin datos"}
        )
        risk_display = risk_display.rename(columns={
            "dyn_name": "Jugador", "risk_level": "Nivel",
            "risk_score": "Score", "acwr": "ACWR",
            "sprint_ratio": "Sprint (%)", "psv99_change_pct": "Cambio PSV-99 (%)",
            "load_change_pct": "Cambio carga (%)", "risk_factors": "Factores",
            "n_matches": "Partidos",
        })
        risk_display = risk_display.sort_values("Score", ascending=False, na_position="last")
        st.dataframe(
            risk_display, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.3f"),
                "ACWR": st.column_config.NumberColumn(format="%.3f"),
                "Sprint (%)": st.column_config.NumberColumn(format="%.1f"),
                "Cambio PSV-99 (%)": st.column_config.NumberColumn(format="%.1f"),
                "Cambio carga (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
