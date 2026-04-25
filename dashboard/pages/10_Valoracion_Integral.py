"""Pagina 10: Valoracion Integral.

Score integral (0-100) por jugador combinando 5 dimensiones
con pesos configurables: rendimiento, fisico, mercado, comercial, medico.
"""

import streamlit as st

from dashboard.config import (
    M5_DATA_SOURCES,
    M5_DEFAULT_WEIGHTS,
    M5_DIM_DESCRIPTIONS,
    M5_DIM_LABELS,
    M5_GLOSSARY,
    label,
)
from dashboard.components.charts_valuation import (
    data_source_legend,
    dimension_detail_bars,
    valuation_breakdown_heatmap,
    valuation_radar,
    valuation_radar_dual,
    valuation_ranking_bar,
    value_performance_quadrant,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import load_valuation
from dashboard.data.valuation import (
    compute_integral_score,
    generate_player_summary,
    has_external_data,
    get_external_coverage,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Valoracion Integral de Jugadores")
st.info(
    "Herramienta de **apoyo a la decision** que combina 5 dimensiones con pesos configurables. "
    "No es un ranking absoluto -- los resultados dependen de los pesos asignados y de la calidad de los datos."
)

# ---------------------------------------------------------------------------
# Aviso de datos externos
# ---------------------------------------------------------------------------

valuation_base = load_valuation()

if not has_external_data():
    st.warning(
        "**Datos externos no disponibles.** Las dimensiones Mercado, Comercial y Medica "
        "muestran score 0 porque no se ha encontrado el archivo "
        "`dashboard/data/external/datos_externos_jugadores.csv`. "
        "Solo se usan las dimensiones Rendimiento y Fisico (datos reales). "
        "Consulta la documentacion del modulo para el formato del CSV."
    )
else:
    coverage = get_external_coverage(valuation_base["player_name"].tolist())
    if coverage["missing"]:
        st.warning(
            f"Datos externos parciales: {coverage['covered']}/{coverage['total']} jugadores cubiertos. "
            f"Sin datos: {', '.join(coverage['missing'])}."
        )

# ---------------------------------------------------------------------------
# Glosario expandible
# ---------------------------------------------------------------------------

with st.expander("Glosario y fuentes de datos"):
    st.markdown(data_source_legend(), unsafe_allow_html=True)
    st.markdown("---")
    cols_gl = st.columns(2)
    with cols_gl[0]:
        st.markdown("**Dimensiones**")
        for dim, desc in M5_DIM_DESCRIPTIONS.items():
            src = M5_DATA_SOURCES.get(dim, "externo")
            tag = "Real" if src == "real" else "Externo"
            st.markdown(f"- **{dim}** ({tag}): {desc}")
    with cols_gl[1]:
        st.markdown("**Terminos**")
        for term, desc in M5_GLOSSARY.items():
            st.markdown(f"- **{term}**: {desc}")

# ---------------------------------------------------------------------------
# Sliders de pesos
# ---------------------------------------------------------------------------

st.markdown("### Configuracion de pesos")

weight_cols = st.columns(5)
weights = {}
dim_keys = ["rendimiento", "fisico", "mercado", "comercial", "medico"]
dim_display = ["Rendimiento", "Fisico", "Mercado", "Comercial", "Medico"]
for col, key, display in zip(weight_cols, dim_keys, dim_display):
    with col:
        weights[key] = st.slider(
            display,
            min_value=0, max_value=100, step=5,
            value=M5_DEFAULT_WEIGHTS[key],
            key=f"w_{key}",
        )

total_weight = sum(weights.values())
if total_weight != 100:
    st.warning(f"Los pesos suman **{total_weight}%** (deben sumar 100%). Ajusta los sliders.")
    st.stop()

# ---------------------------------------------------------------------------
# Calcular integral score con pesos actuales
# ---------------------------------------------------------------------------

df = compute_integral_score(valuation_base, weights)
players = sorted(df["player_name"].tolist())

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_ranking, tab_perfil, tab_comparativa = st.tabs([
    "Ranking",
    "Perfil Individual",
    "Comparativa",
])

# ========================== TAB 1: RANKING ==========================
with tab_ranking:
    best_player = df.iloc[0]
    render_kpi_row([
        {"label": "Jugadores valorados", "value": len(df)},
        {"label": "Score medio", "value": f"{df['integral_score'].mean():.1f}"},
        {"label": "Mejor valorado", "value": best_player["player_name"]},
        {"label": "Score maximo", "value": f"{best_player['integral_score']:.1f}"},
    ])

    st.markdown("---")

    col_rank, col_heat = st.columns([1, 1])

    with col_rank:
        st.markdown("#### Ranking por Score Integral")
        st.plotly_chart(valuation_ranking_bar(df), use_container_width=True)

    with col_heat:
        st.markdown("#### Desglose por dimensiones")
        st.plotly_chart(valuation_breakdown_heatmap(df), use_container_width=True)

    st.markdown("---")

    # Solo mostrar scatter si hay datos de mercado
    if has_external_data() and df["market_value_m"].notna().any():
        st.markdown("#### Rendimiento vs Valor de Mercado")
        st.plotly_chart(value_performance_quadrant(df), use_container_width=True)

    # Descarga CSV
    st.markdown("---")
    csv_cols = ["player_name", "profile", "integral_score",
                "score_rendimiento", "score_fisico", "score_mercado",
                "score_comercial", "score_medico"]
    if has_external_data():
        csv_cols += ["market_value_m", "age"]
    csv_data = df[[c for c in csv_cols if c in df.columns]].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar ranking (CSV)",
        data=csv_data,
        file_name="sevilla_valoracion_integral.csv",
        mime="text/csv",
    )

# ========================== TAB 2: PERFIL INDIVIDUAL ==========================
with tab_perfil:
    selected = st.selectbox("Selecciona un jugador", players, key="perfil_player")
    player_row = df[df["player_name"] == selected].iloc[0]

    # KPIs jugador
    kpi_items = [
        {"label": "Score Integral", "value": f"{player_row['integral_score']:.1f}"},
        {"label": "Posicion", "value": player_row["profile"]},
        {"label": "Partidos", "value": int(player_row.get("n_matches", 0))},
    ]
    if has_external_data() and player_row.get("market_value_m") is not None:
        mv = player_row.get("market_value_m", 0)
        kpi_items.insert(2, {"label": "Valor mercado", "value": f"{mv:.0f}M"})
    render_kpi_row(kpi_items)

    st.markdown("---")

    col_radar, col_bars = st.columns([1, 1])
    with col_radar:
        st.markdown("#### Radar de valoracion")
        st.plotly_chart(valuation_radar(player_row, selected), use_container_width=True)
    with col_bars:
        st.markdown("#### Desglose por dimension")
        st.plotly_chart(dimension_detail_bars(player_row, selected), use_container_width=True)

    # Fortalezas y areas de mejora
    st.markdown("---")
    score_dims = ["score_rendimiento", "score_fisico", "score_mercado", "score_comercial", "score_medico"]
    team_medians = df[score_dims].median()
    summary = generate_player_summary(player_row, team_medians)

    col_f, col_m = st.columns(2)
    with col_f:
        st.markdown("#### Fortalezas")
        for f in summary["fortalezas"]:
            st.markdown(f"- {f}")
    with col_m:
        st.markdown("#### Areas de mejora")
        for m in summary["mejora"]:
            st.markdown(f"- {m}")

    # Datos externos de referencia (solo si hay)
    if has_external_data() and player_row.get("has_external_data", False):
        with st.expander("Datos externos del jugador"):
            ext_info = {
                "Valor de mercado": f"{player_row.get('market_value_m', '-')} M",
                "Edad": f"{player_row.get('age', '-')}",
                "Anos de contrato": player_row.get("contract_years", "-"),
                "Seguidores Instagram": f"{player_row.get('instagram_followers_k', '-')}K",
                "Lesiones (2 temp.)": player_row.get("injuries_2y", "-"),
                "Dias perdidos": player_row.get("days_missed", "-"),
            }
            for k, v in ext_info.items():
                st.markdown(f"- **{k}**: {v}")

# ========================== TAB 3: COMPARATIVA ==========================
with tab_comparativa:
    col_a, col_b = st.columns(2)
    with col_a:
        player_a = st.selectbox("Jugador A", players, index=0, key="comp_a")
    with col_b:
        default_b = 1 if len(players) > 1 else 0
        player_b = st.selectbox("Jugador B", players, index=default_b, key="comp_b")

    if player_a == player_b:
        st.warning("Selecciona dos jugadores diferentes para comparar.")
        st.stop()

    row_a = df[df["player_name"] == player_a].iloc[0]
    row_b = df[df["player_name"] == player_b].iloc[0]

    # KPIs comparativos
    delta_score = row_a["integral_score"] - row_b["integral_score"]
    render_kpi_row([
        {"label": player_a, "value": f"{row_a['integral_score']:.1f}"},
        {"label": player_b, "value": f"{row_b['integral_score']:.1f}"},
        {"label": "Diferencia", "value": f"{abs(delta_score):.1f}", "delta": f"{'A>B' if delta_score > 0 else 'B>A'}"},
    ])

    st.markdown("---")

    # Radar dual
    st.markdown("#### Comparativa radar")
    st.plotly_chart(valuation_radar_dual(row_a, player_a, row_b, player_b), use_container_width=True)

    # Tabla comparativa lado a lado
    st.markdown("#### Detalle por dimension")
    comp_dims = ["score_rendimiento", "score_fisico", "score_mercado", "score_comercial", "score_medico", "integral_score"]
    comp_data = {
        "Dimension": [M5_DIM_LABELS.get(d, d) for d in comp_dims],
        player_a: [f"{row_a.get(d, 0):.1f}" for d in comp_dims],
        player_b: [f"{row_b.get(d, 0):.1f}" for d in comp_dims],
        "Diferencia": [f"{row_a.get(d, 0) - row_b.get(d, 0):+.1f}" for d in comp_dims],
    }
    st.dataframe(comp_data, hide_index=True, use_container_width=True)

    # Datos extra
    if has_external_data():
        st.markdown("#### Contexto")
        ctx_fields = [
            ("Posicion", "profile"),
            ("Valor mercado (M)", "market_value_m"),
            ("Edad", "age"),
            ("Anos contrato", "contract_years"),
            ("Partidos analizados", "n_matches"),
        ]
        ctx_data = {
            "": [f[0] for f in ctx_fields],
            player_a: [str(row_a.get(f[1], "-")) for f in ctx_fields],
            player_b: [str(row_b.get(f[1], "-")) for f in ctx_fields],
        }
        st.dataframe(ctx_data, hide_index=True, use_container_width=True)
