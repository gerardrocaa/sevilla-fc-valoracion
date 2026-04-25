"""Pagina 9: Escenarios What-If.

Simulaciones Monte Carlo para anticipar impacto de cambios tacticos,
rotaciones y ausencias de jugadores.
"""

import streamlit as st

from dashboard.config import (
    BLOCK_LABELS,
    DIM_LABELS,
    FORMATION_TEMPLATES,
    WHATIF_DEFAULT_ITERATIONS,
    WHATIF_GLOSSARY,
    WHATIF_SCENARIO_DESCRIPTIONS,
    label,
)
from dashboard.components.charts_whatif import (
    absence_comparison_bar,
    absence_distribution_box,
    block_grouped_bar,
    block_per_match_heatmap,
    block_radar,
    cumulative_load_projection,
    fatigue_projection_dual,
    formation_comparison_bar,
    formation_comparison_radar,
    formation_pitch_diagram,
    redistribution_table_chart,
    rotation_risk_comparison,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import (
    load_aggregated,
    load_dynamic,
    load_fatigue,
    load_fatigue_stats,
    load_physical_raw,
    load_risk,
    load_scores,
)
from dashboard.data.whatif import (
    build_default_lineup,
    simulate_defensive_block,
    simulate_formation_comparison,
    simulate_player_absence,
    simulate_rotation,
)

st.title("Escenarios What-If")
st.info(
    "Simulaciones Monte Carlo para responder preguntas tacticas y de gestion de plantilla. "
    "Cada escenario usa bootstrap sobre datos reales (6 partidos) para generar intervalos de confianza. "
    "Los resultados muestran el rango probable, no predicciones puntuales."
)

with st.expander("Glosario de terminos"):
    for term, desc in WHATIF_GLOSSARY.items():
        st.markdown(f"- **{term}**: {desc}")

# --- Load data ---
scores_all = load_scores()
aggregated = load_aggregated()
dynamic_sev = load_dynamic()
physical = load_physical_raw()
fatigue_df = load_fatigue()
fatigue_stats = load_fatigue_stats()
risk_df = load_risk()

# --- Tabs ---
tab_ausencia, tab_bloque, tab_rotacion, tab_formacion = st.tabs([
    "Ausencia de Jugador",
    "Bloque Defensivo",
    "Rotacion Fisica",
    "Formacion Alternativa",
])

# ===================== TAB 1: AUSENCIA DE JUGADOR =====================
with tab_ausencia:
    st.markdown(f"#### {WHATIF_SCENARIO_DESCRIPTIONS['ausencia']['titulo']}")
    st.caption(WHATIF_SCENARIO_DESCRIPTIONS["ausencia"]["descripcion"])

    all_players = sorted(aggregated["player_name"].unique())
    absent_player = st.selectbox(
        "Jugador a excluir",
        options=all_players,
        key="whatif_absent_player",
    )

    n_iter = st.slider(
        "Iteraciones Monte Carlo", 100, 5000, WHATIF_DEFAULT_ITERATIONS,
        step=100, key="whatif_absent_iter",
    )

    if st.button("Simular ausencia", key="btn_absence"):
        with st.spinner("Simulando..."):
            result = simulate_player_absence(
                scores_all, dynamic_sev, aggregated,
                absent_player, n_iterations=n_iter,
            )

        # KPIs
        absent_data = result.get("absent_data", {})
        contribution = result.get("contribution", {})
        render_kpi_row([
            {"label": "Jugador excluido", "value": absent_player},
            {"label": "Score compuesto", "value": f"{absent_data.get('composite_score', 0):.3f}"},
            {"label": "Minutos totales", "value": f"{absent_data.get('total_minutes', 0):.0f}"},
            {"label": "Pares posicionales", "value": len(result.get("peers", []))},
        ])

        st.markdown("---")

        # Graficos
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Impacto en metricas de equipo")
            fig = absence_comparison_bar(result["baseline"], result["simulated"])
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Barras verdes = con jugador. Barras rojas = sin jugador. Error bars = P25-P75.")

        with col2:
            st.markdown("##### Redistribucion de contribucion")
            fig = redistribution_table_chart(result.get("redistribution", []))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Peso proporcional al composite_score de cada par posicional.")

        # Contribucion del ausente
        if contribution:
            st.markdown("##### Contribucion media por partido del jugador ausente")
            contrib_cols = st.columns(4)
            metric_map = {
                "xthreat_mean": ("xThreat medio", f"{contribution.get('xthreat_mean', 0):.3f}"),
                "pressing_mean": ("Pressing/partido", f"{contribution.get('pressing_mean', 0):.1f}"),
                "runs_mean": ("Carreras s/balon", f"{contribution.get('runs_mean', 0):.1f}"),
                "events_mean": ("Eventos/partido", f"{contribution.get('events_mean', 0):.0f}"),
            }
            for col, (key, (lbl, val)) in zip(contrib_cols, metric_map.items()):
                col.metric(lbl, val)

        # Supuestos
        with st.expander("Supuestos y limitaciones"):
            for s in result.get("supuestos", []):
                st.markdown(f"- {s}")


# ===================== TAB 2: BLOQUE DEFENSIVO =====================
with tab_bloque:
    st.markdown(f"#### {WHATIF_SCENARIO_DESCRIPTIONS['bloque']['titulo']}")
    st.caption(WHATIF_SCENARIO_DESCRIPTIONS["bloque"]["descripcion"])

    available_blocks = ["high_block", "medium_block", "low_block"]
    selected_blocks = st.multiselect(
        "Tipos de bloque a comparar",
        options=available_blocks,
        default=available_blocks,
        format_func=lambda x: BLOCK_LABELS.get(x, x),
        key="whatif_blocks",
    )

    n_iter_block = st.slider(
        "Iteraciones Monte Carlo", 100, 5000, WHATIF_DEFAULT_ITERATIONS,
        step=100, key="whatif_block_iter",
    )

    if selected_blocks and st.button("Comparar bloques", key="btn_block"):
        with st.spinner("Analizando bloques defensivos..."):
            result = simulate_defensive_block(dynamic_sev, selected_blocks, n_iter_block)

        summaries = result["summaries"]
        block_counts = result["block_counts"]

        # KPIs
        kpi_data = []
        for bt in selected_blocks:
            s = summaries.get(bt, {})
            n_ev = s.get("n_events_total", 0)
            kpi_data.append({"label": BLOCK_LABELS.get(bt, bt), "value": f"{n_ev} eventos"})
        kpi_data.append({"label": "Total engagements", "value": block_counts.get("total", 0)})
        render_kpi_row(kpi_data)

        st.markdown("---")

        # Graficos
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Comparativa de metricas")
            fig = block_grouped_bar(summaries)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Error bars = P25-P75 del bootstrap a nivel de partido.")

        with col2:
            st.markdown("##### Perfil radar por bloque")
            fig = block_radar(summaries)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Distribucion por partido")
        fig = block_per_match_heatmap(result["per_match_data"])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Numero de eventos defensivos por tipo de bloque en cada partido.")

        with st.expander("Supuestos y limitaciones"):
            for s in result.get("supuestos", []):
                st.markdown(f"- {s}")


# ===================== TAB 3: ROTACION FISICA =====================
with tab_rotacion:
    st.markdown(f"#### {WHATIF_SCENARIO_DESCRIPTIONS['rotacion']['titulo']}")
    st.caption(WHATIF_SCENARIO_DESCRIPTIONS["rotacion"]["descripcion"])

    # Solo jugadores con datos fisicos
    players_with_phys = sorted(physical["dyn_name"].dropna().unique()) if not physical.empty else []
    if not players_with_phys:
        st.warning("Sin datos fisicos disponibles para simulacion de rotacion.")
    else:
        rot_player = st.selectbox(
            "Jugador", options=players_with_phys, key="whatif_rot_player",
        )
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rot_freq = st.slider(
                "Descanso cada N partidos", 2, 5, 3, key="whatif_rot_freq",
            )
        with col_r2:
            n_future = st.slider(
                "Partidos futuros a proyectar", 3, 12, 6, key="whatif_n_future",
            )

        n_iter_rot = st.slider(
            "Iteraciones Monte Carlo", 100, 5000, WHATIF_DEFAULT_ITERATIONS,
            step=100, key="whatif_rot_iter",
        )

        if st.button("Proyectar rotacion", key="btn_rotation"):
            with st.spinner("Proyectando fatiga..."):
                result = simulate_rotation(
                    physical, fatigue_df, fatigue_stats, risk_df,
                    rot_player, rotation_frequency=rot_freq,
                    n_future_matches=n_future, n_iterations=n_iter_rot,
                )

            if "error" in result and result["error"]:
                st.error(result["error"])
            else:
                # KPIs
                baseline_info = result["baseline"]
                risk_info = result.get("player_risk", {})
                render_kpi_row([
                    {"label": "Fatiga actual", "value": f"{baseline_info.get('current_fatigue', 0):.3f}"},
                    {"label": "Riesgo actual", "value": risk_info.get("risk_level", "N/D")},
                    {"label": "Pico sin rotacion", "value": f"{result['peak_baseline']:.3f}"},
                    {"label": "Reduccion con rotacion", "value": f"{result['reduction_pct']:.1f}%"},
                ])

                st.markdown("---")

                # Curva de fatiga
                st.markdown("##### Proyeccion de Fatiga")
                fig = fatigue_projection_dual(
                    result["baseline"]["curve"],
                    result["rotated"]["curve"],
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    "Linea roja = sin rotacion. Linea verde = con rotacion. "
                    "Bandas = P25-P75. Marcas X = partidos de descanso."
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("##### Pico de Fatiga")
                    fig = rotation_risk_comparison(
                        result["peak_baseline"],
                        result["peak_rotated"],
                        result["reduction_pct"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("##### Carga Acumulada Proyectada")
                    fig = cumulative_load_projection(
                        result["baseline"]["curve"],
                        result["rotated"]["curve"],
                        baseline_info["load_mean"],
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with st.expander("Supuestos y limitaciones"):
                    for s in result.get("supuestos", []):
                        st.markdown(f"- {s}")


# ===================== TAB 4: FORMACION ALTERNATIVA =====================
with tab_formacion:
    st.markdown(f"#### {WHATIF_SCENARIO_DESCRIPTIONS['formacion']['titulo']}")
    st.caption(WHATIF_SCENARIO_DESCRIPTIONS["formacion"]["descripcion"])

    formations = list(FORMATION_TEMPLATES.keys())
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        formation_a = st.selectbox(
            "Formacion A", options=formations, index=0, key="whatif_form_a",
        )
    with col_f2:
        default_b = 1 if len(formations) > 1 else 0
        formation_b = st.selectbox(
            "Formacion B", options=formations, index=default_b, key="whatif_form_b",
        )

    n_iter_form = st.slider(
        "Iteraciones Monte Carlo", 100, 5000, WHATIF_DEFAULT_ITERATIONS,
        step=100, key="whatif_form_iter",
    )

    if st.button("Comparar formaciones", key="btn_formation"):
        with st.spinner("Simulando formaciones..."):
            result = simulate_formation_comparison(
                scores_all, aggregated, dynamic_sev,
                formation_a, formation_b,
                n_iterations=n_iter_form,
            )

        metrics_a = result["metrics_a"]
        metrics_b = result["metrics_b"]
        comparison = result["comparison"]

        # KPIs
        comp_mean_a = metrics_a.get("team_metrics", {}).get("composite_mean", {}).get("mean", 0)
        comp_mean_b = metrics_b.get("team_metrics", {}).get("composite_mean", {}).get("mean", 0)
        diff = comp_mean_b - comp_mean_a
        render_kpi_row([
            {"label": f"Score {formation_a}", "value": f"{comp_mean_a:.3f}"},
            {"label": f"Score {formation_b}", "value": f"{comp_mean_b:.3f}"},
            {"label": "Diferencia", "value": f"{diff:+.3f}"},
            {"label": "Jugadores", "value": f"{metrics_a.get('n_players', 0)} / {metrics_b.get('n_players', 0)}"},
        ])

        st.markdown("---")

        # Pitch diagrams
        st.markdown("##### Diagramas de Formacion")
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            fig = formation_pitch_diagram(metrics_a["lineup"], formation_a, title=formation_a)
            st.plotly_chart(fig, use_container_width=True)

        with col_p2:
            fig = formation_pitch_diagram(metrics_b["lineup"], formation_b, title=formation_b)
            st.plotly_chart(fig, use_container_width=True)

        # Radar + barras
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("##### Perfil Radar")
            fig = formation_comparison_radar(metrics_a, metrics_b, formation_a, formation_b)
            st.plotly_chart(fig, use_container_width=True)

        with col_r2:
            st.markdown("##### Comparativa por Dimension")
            fig = formation_comparison_bar(comparison, formation_a, formation_b)
            st.plotly_chart(fig, use_container_width=True)

        # Lineups table
        st.markdown("##### Lineups asignados")
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown(f"**{formation_a}**")
            lineup_a_data = [
                {"Posicion": p["position"], "Jugador": p["player_name"], "Score": f"{p['composite_score']:.3f}"}
                for p in metrics_a["lineup"]
            ]
            st.dataframe(lineup_a_data, use_container_width=True, hide_index=True)

        with col_t2:
            st.markdown(f"**{formation_b}**")
            lineup_b_data = [
                {"Posicion": p["position"], "Jugador": p["player_name"], "Score": f"{p['composite_score']:.3f}"}
                for p in metrics_b["lineup"]
            ]
            st.dataframe(lineup_b_data, use_container_width=True, hide_index=True)

        with st.expander("Supuestos y limitaciones"):
            for s in result.get("supuestos", []):
                st.markdown(f"- {s}")
