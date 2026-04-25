"""Pagina 6: Clustering de Perfiles de Jugadores."""

import streamlit as st

from dashboard.config import CLUSTERING_FEATURES, DIM_LABELS, INFERENCE_GLOSSARY
from dashboard.components.charts_inference import (
    cluster_feature_heatmap,
    cluster_profile_radar,
    cluster_scatter_pca,
)
from dashboard.components.kpi_cards import render_kpi_row
from dashboard.data.loader import load_clustering

st.title("Clustering de Perfiles")
st.info(
    "Agrupación automática de jugadores según su perfil de rendimiento (D1-D6). "
    "El algoritmo K-Means identifica grupos con características similares. "
    "PCA reduce las 6 dimensiones a 2 para poder visualizar los clusters."
)

with st.expander("Glosario de términos"):
    for term, desc in INFERENCE_GLOSSARY.items():
        if term in ("Cluster", "PCA", "Silhouette"):
            st.markdown(f"- **{term}**: {desc}")

# --- Load data ---
clustering = load_clustering()
labels_df = clustering["labels_df"]
meta = clustering["meta"]
centers = clustering["centers"]

if labels_df.empty:
    st.warning("Sin datos suficientes para clustering.")
    st.stop()

# --- KPIs ---
render_kpi_row([
    {"label": "Clusters", "value": meta.get("n_clusters", 0)},
    {"label": "Silhouette", "value": f"{meta.get('silhouette', 0):.3f}"},
    {"label": "Jugadores", "value": meta.get("n_players", 0)},
    {"label": "Varianza explicada", "value": f"{meta.get('variance_explained', 0):.1%}"},
])

st.markdown("---")

# --- Row 1: PCA scatter + Radar ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Mapa de Clusters (PCA)")
    fig = cluster_scatter_pca(labels_df, meta)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Cada punto es un jugador, proyectado en 2 dimensiones (PCA). "
        "Los colores indican el cluster asignado. Jugadores cercanos tienen perfiles similares."
    )

with col2:
    st.markdown("#### Perfil Promedio por Cluster")
    if not centers.empty:
        fig = cluster_profile_radar(centers, meta)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Radar con los valores promedio de cada dimensión por cluster. "
            "Permite ver qué aspecto del juego define a cada grupo."
        )

# --- Row 2: Heatmap ---
st.markdown("#### Mapa de Calor: Jugadores x Dimensiones")
fig = cluster_feature_heatmap(labels_df, meta)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Filas ordenadas por cluster. Verde = score alto, rojo = score bajo. "
    "Permite identificar visualmente los patrones de cada grupo."
)

# --- Tabla ---
st.markdown("### Asignación de Clusters")
dim_labels_inv = {v: k for k, v in DIM_LABELS.items()}
display_cols = ["player_name", "profile", "cluster_label"]
dim_display = [c for c in CLUSTERING_FEATURES if c in labels_df.columns]
display_cols.extend(dim_display)

table = labels_df[display_cols].copy()
rename_map = {
    "player_name": "Jugador",
    "profile": "Posición",
    "cluster_label": "Cluster",
}
rename_map.update({c: DIM_LABELS.get(c, c) for c in dim_display})
table = table.rename(columns=rename_map)
table = table.sort_values("Cluster")

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={DIM_LABELS[c]: st.column_config.NumberColumn(format="%.3f")
                   for c in dim_display if c in DIM_LABELS},
)
