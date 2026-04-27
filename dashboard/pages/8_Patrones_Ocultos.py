"""Pagina 8: Patrones Ocultos (Correlaciones)."""

import streamlit as st
import pandas as pd

from dashboard.config import CORRELATION_PAIRS, INFERENCE_GLOSSARY
from dashboard.components.charts_inference import (
    correlation_detail_scatter,
    correlation_heatmap,
    significance_forest,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import load_correlations, load_dynamic

st.title("Patrones Ocultos")
st.info(
    "Análisis de correlaciones entre variables del juego para descubrir relaciones "
    "estadísticas entre acciones tácticas y resultados. Se utilizan correlaciones "
    "de Spearman con intervalos de confianza bootstrap al 95%."
)

with st.expander("Glosario de términos"):
    for term, desc in INFERENCE_GLOSSARY.items():
        if term in ("Correlación", "IC 95%", "p-valor"):
            st.markdown(f"- **{term}**: {desc}")

with st.expander("Cómo interpretar esta página"):
    st.markdown("""
**Matriz de Correlaciones** — Mapa de calor que muestra la correlación de Spearman entre pares de variables. Rojo indica correlación positiva (cuando una sube, la otra también), azul indica correlación negativa (cuando una sube, la otra baja). El asterisco (*) marca las correlaciones estadísticamente significativas (p < 0,05). Valores cercanos a +1 o -1 son relaciones fuertes.

**Forest Plot (IC 95%)** — Cada diamante representa una correlación con su intervalo de confianza al 95%. Si el intervalo horizontal cruza la línea del cero, la correlación no es estadísticamente significativa. Los diamantes rojos son significativos y los grises no. Cuanto más lejos del cero esté el diamante, más fuerte es la relación.

**Detalle de Correlación (Scatter)** — Gráfico de dispersión que muestra los datos crudos detrás de una correlación seleccionada, con una línea de regresión superpuesta. Permite verificar visualmente si la relación es lineal, si hay outliers que distorsionan el resultado, o si la correlación es genuina. Se muestra el coeficiente r y el p-valor.
""")

# --- Load data ---
corr_df = load_correlations()
dynamic_sev = load_dynamic()

if corr_df.empty:
    st.warning("Sin datos de correlaciones disponibles.")
    st.stop()

# --- KPIs ---
n_total = len(corr_df)
n_sig = corr_df["significant"].sum() if "significant" in corr_df.columns else 0
max_r = corr_df["statistic"].abs().max() if "statistic" in corr_df.columns else 0
min_p = corr_df["p_value"].min() if "p_value" in corr_df.columns else 1

render_kpi_row([
    {"label": "Pares analizados", "value": n_total},
    {"label": "Significativas (p<0.05)", "value": int(n_sig)},
    {"label": "Max |r|", "value": f"{max_r:.3f}"},
    {"label": "Min p-valor", "value": f"{min_p:.4f}"},
])

st.markdown("---")

# --- Row 1: Heatmap + Forest plot ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Matriz de Correlaciones")
    fig = correlation_heatmap(corr_df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Rojo = correlación positiva, azul = negativa. "
        "Asterisco (*) indica significación estadística (p < 0.05)."
    )

with col2:
    st.markdown("#### Forest Plot (IC 95%)")
    fig = significance_forest(corr_df)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Diamantes rojos = significativos. Las barras horizontales muestran "
        "el intervalo de confianza al 95%. Si el IC cruza el cero, la correlación no es significativa."
    )

# --- Row 2: Detail scatter ---
st.markdown("#### Detalle de Correlación")

# Build pair options from correlation results
pair_options = []
for _, row in corr_df.iterrows():
    pair_options.append(f"{row['var_x']} vs {row['var_y']}")

selected_pair_idx = st.selectbox(
    "Seleccionar par de variables",
    options=range(len(pair_options)),
    format_func=lambda i: pair_options[i],
    key="corr_pair_select",
)

if selected_pair_idx is not None and selected_pair_idx < len(corr_df):
    pair_row = corr_df.iloc[selected_pair_idx]

    # Find the raw variable names from CORRELATION_PAIRS config
    raw_var_x = pair_row.get("raw_var_x", "")
    raw_var_y = pair_row.get("raw_var_y", "")

    if raw_var_x and raw_var_y:
        fig = correlation_detail_scatter(
            dynamic_sev, raw_var_x, raw_var_y,
            pair_row["var_x"], pair_row["var_y"],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Show interpretation
        interp = pair_row.get("interpretation", "")
        r_val = pair_row.get("statistic", 0)
        p_val = pair_row.get("p_value", 1)
        n_obs = pair_row.get("n_obs", 0)

        st.markdown(
            f"**Interpretación**: {interp} (r = {r_val:.3f}, p = {p_val:.4f}, n = {n_obs:,})"
        )

# --- Insights ---
st.markdown("### Hallazgos Principales")
sig_corrs = corr_df[corr_df["significant"] == True] if "significant" in corr_df.columns else pd.DataFrame()
if not sig_corrs.empty:
    for _, row in sig_corrs.iterrows():
        direction = "positiva" if row["statistic"] > 0 else "negativa"
        st.markdown(
            f"- **{row['var_x']}** y **{row['var_y']}**: "
            f"correlación {row['interpretation'].lower()} "
            f"(r = {row['statistic']:.3f}, p = {row['p_value']:.4f})"
        )
else:
    st.info("No se encontraron correlaciones estadísticamente significativas con p < 0.05.")

# --- Full table ---
st.markdown("### Tabla Completa")
table = corr_df.copy()
display_cols = ["var_x", "var_y", "statistic", "p_value", "n_obs", "significant",
                "ci_lower", "ci_upper", "interpretation"]
display_cols = [c for c in display_cols if c in table.columns]
table = table[display_cols].rename(columns={
    "var_x": "Variable X", "var_y": "Variable Y",
    "statistic": "Correlación", "p_value": "p-valor",
    "n_obs": "Observaciones", "significant": "Significativa",
    "ci_lower": "IC inferior", "ci_upper": "IC superior",
    "interpretation": "Interpretación",
})
st.dataframe(
    table, use_container_width=True, hide_index=True,
    column_config={
        "Correlación": st.column_config.NumberColumn(format="%.4f"),
        "p-valor": st.column_config.NumberColumn(format="%.6f"),
        "IC inferior": st.column_config.NumberColumn(format="%.4f"),
        "IC superior": st.column_config.NumberColumn(format="%.4f"),
    },
)
