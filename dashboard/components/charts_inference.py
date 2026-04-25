"""Graficos Plotly para Modulo 3: Inferencia Predictiva."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import (
    CLUSTER_COLORS,
    CLUSTERING_FEATURES,
    DIM_LABELS,
    PLOTLY_TEMPLATE,
    RISK_COLORS,
    SEVILLA_RED,
    label,
)


def _apply_template(fig):
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    fig.update_layout(
        dragmode=False,
        margin=dict(t=20, b=60, l=120, r=80),
    )
    fig.update_xaxes(fixedrange=True, automargin=True)
    fig.update_yaxes(fixedrange=True, automargin=True)
    return fig


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def cluster_scatter_pca(labels_df: pd.DataFrame, meta: dict):
    """Scatter 2D con clusters coloreados por PCA."""
    fig = go.Figure()

    n_clusters = meta.get("n_clusters", 1)
    cluster_labels = meta.get("cluster_labels", {})

    for c in range(n_clusters):
        mask = labels_df["cluster"] == c
        subset = labels_df[mask]
        color = CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        cl_label = cluster_labels.get(str(c), cluster_labels.get(c, f"Cluster {c}"))

        fig.add_trace(go.Scatter(
            x=subset["pc1"],
            y=subset["pc2"],
            mode="markers+text",
            text=subset["player_name"],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(size=12, color=color, opacity=0.8,
                        line=dict(width=1, color="white")),
            name=cl_label,
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"Cluster: {cl_label}<br>"
                "PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Componente Principal 1",
        yaxis_title="Componente Principal 2",
        height=500,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5,
                    font=dict(size=10)),
    )
    return _apply_template(fig)


def cluster_profile_radar(centers: pd.DataFrame, meta: dict):
    """Radar chart con perfil promedio por cluster."""
    dim_cols = [c for c in CLUSTERING_FEATURES if c in centers.columns]
    categories = [DIM_LABELS.get(d, d) for d in dim_cols]
    cluster_labels = meta.get("cluster_labels", {})

    fig = go.Figure()
    for _, row in centers.iterrows():
        c = int(row["cluster"])
        color = CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        cl_label = cluster_labels.get(str(c), cluster_labels.get(c, f"Cluster {c}"))

        values = [row.get(d, 0) for d in dim_cols]
        values_closed = values + [values[0]]
        cats_closed = categories + [categories[0]]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=cats_closed,
            fill="toself",
            opacity=0.3,
            name=cl_label,
            line=dict(color=color, width=2),
            hovertemplate="%{theta}: %{r:.3f}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=500,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=80, l=60, r=60),
    )
    return _apply_template(fig)


def cluster_feature_heatmap(labels_df: pd.DataFrame, meta: dict):
    """Heatmap jugadores x dimensiones coloreado por valor."""
    dim_cols = [c for c in CLUSTERING_FEATURES if c in labels_df.columns]
    if not dim_cols:
        fig = go.Figure()
        return _apply_template(fig)

    df = labels_df.sort_values("cluster")
    z = df[dim_cols].values
    y_labels = df["player_name"].tolist()
    x_labels = [DIM_LABELS.get(d, d) for d in dim_cols]
    cluster_info = [str(c) for c in df["cluster"].values]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=x_labels,
        y=y_labels,
        colorscale="RdYlGn",
        text=np.round(z, 2).astype(str),
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="Jugador: %{y}<br>Dimensión: %{x}<br>Score: %{z:.3f}<extra></extra>",
        zmin=0, zmax=1,
        colorbar=dict(title="Score"),
    ))

    fig.update_layout(
        height=max(450, len(y_labels) * 30),
        yaxis=dict(autorange="reversed"),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Fatiga
# ---------------------------------------------------------------------------

def fatigue_evolution_lines(fatigue_df: pd.DataFrame, players: list = None):
    """Lineas de indice de fatiga por partido."""
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    df = fatigue_df.copy()
    if players:
        df = df[df["dyn_name"].isin(players)]

    fig = go.Figure()
    for player in df["dyn_name"].unique():
        pdata = df[df["dyn_name"] == player].copy()
        pdata["j_order"] = pd.Categorical(pdata["jornada"], categories=jornada_order, ordered=True)
        pdata = pdata.sort_values("j_order")

        fig.add_trace(go.Scatter(
            x=pdata["jornada"],
            y=pdata["fatigue_index"],
            mode="lines+markers",
            name=player,
            marker=dict(size=8),
            hovertemplate=f"<b>{player}</b><br>Jornada: %{{x}}<br>Fatiga: %{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        yaxis_title="Índice de Fatiga",
        yaxis_range=[-0.05, 1.05],
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=9)),
        margin=dict(t=20, b=100, l=80, r=20),
    )
    return _apply_template(fig)


def fatigue_cumulative_bar(fatigue_df: pd.DataFrame, players: list = None):
    """Barras apiladas de carga acumulada por jugador."""
    df = fatigue_df.copy()
    if players:
        df = df[df["dyn_name"].isin(players)]

    if df.empty or "cumulative_load" not in df.columns:
        fig = go.Figure()
        return _apply_template(fig)

    # Get last match cumulative load per player
    last = df.sort_values("jornada").groupby("dyn_name").last().reset_index()
    last = last.sort_values("cumulative_load", ascending=True)

    fig = go.Figure(go.Bar(
        x=last["cumulative_load"],
        y=last["dyn_name"],
        orientation="h",
        marker_color=SEVILLA_RED,
        text=last["cumulative_load"].round(0).astype(int),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Carga acumulada: %{x:,.0f} m<extra></extra>",
    ))

    max_val = last["cumulative_load"].max() if len(last) > 0 else 1
    fig.update_layout(
        xaxis_title="Carga acumulada (m)",
        height=max(400, len(last) * 38),
        xaxis_range=[0, max_val * 1.2],
    )
    return _apply_template(fig)


def psv99_trend_lines(fatigue_df: pd.DataFrame, players: list = None):
    """Tendencia PSV-99 con linea de regresion."""
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    df = fatigue_df.copy()
    if players:
        df = df[df["dyn_name"].isin(players)]

    fig = go.Figure()
    for player in df["dyn_name"].unique():
        pdata = df[df["dyn_name"] == player].copy()
        pdata = pdata.dropna(subset=["psv99"])
        if pdata.empty:
            continue
        pdata["j_order"] = pd.Categorical(pdata["jornada"], categories=jornada_order, ordered=True)
        pdata = pdata.sort_values("j_order")

        fig.add_trace(go.Scatter(
            x=pdata["jornada"],
            y=pdata["psv99"],
            mode="lines+markers",
            name=player,
            marker=dict(size=8),
            hovertemplate=f"<b>{player}</b><br>Jornada: %{{x}}<br>PSV-99: %{{y:.1f}} km/h<extra></extra>",
        ))

    fig.update_layout(
        yaxis_title="PSV-99 (km/h)",
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=9)),
        margin=dict(t=20, b=100, l=80, r=20),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Riesgo de lesion
# ---------------------------------------------------------------------------

def risk_semaphore_chart(risk_df: pd.DataFrame):
    """Barras horizontales semaforo de riesgo."""
    df = risk_df.sort_values("risk_score", ascending=True).copy()

    colors = [RISK_COLORS.get(r, "#999") for r in df["risk_level"]]

    # Minimum visual width so 0.0 scores are still visible
    display_x = df["risk_score"].clip(lower=0.02)

    fig = go.Figure(go.Bar(
        x=display_x,
        y=df["dyn_name"],
        orientation="h",
        marker_color=colors,
        text=df["risk_score"].round(2),
        textposition="outside",
        customdata=df["risk_score"],
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score riesgo: %{customdata:.3f}<br>"
            "<extra></extra>"
        ),
    ))

    # Add threshold lines
    fig.add_vline(x=0.33, line_dash="dash", line_color="#999", opacity=0.5)
    fig.add_vline(x=0.66, line_dash="dash", line_color="#999", opacity=0.5)

    fig.update_layout(
        xaxis_title="Score de Riesgo",
        xaxis_range=[0, 1.15],
        height=max(400, len(df) * 35),
    )
    return _apply_template(fig)


def risk_factors_bar(risk_df: pd.DataFrame, player: str):
    """Factores de riesgo desglosados para un jugador."""
    row = risk_df[risk_df["dyn_name"] == player]
    if row.empty:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos", showarrow=False, xref="paper", yref="paper",
                           x=0.5, y=0.5, font=dict(size=14))
        return _apply_template(fig)

    row = row.iloc[0]
    metrics = {
        "ACWR": row.get("acwr", 1.0),
        "Cambio PSV-99 (%)": row.get("psv99_change_pct", 0),
        "Cambio carga (%)": row.get("load_change_pct", 0),
        "Sprint ratio (%)": row.get("sprint_ratio", 0),
    }

    names = list(metrics.keys())
    values = list(metrics.values())

    # Color based on whether the value is in risk zone
    colors = []
    for name, val in zip(names, values):
        if name == "ACWR":
            colors.append(RISK_COLORS["alto"] if (val < 0.8 or val > 1.3) else RISK_COLORS["bajo"])
        elif name == "Cambio PSV-99 (%)":
            colors.append(RISK_COLORS["alto"] if val < -5 else RISK_COLORS["bajo"])
        elif name == "Cambio carga (%)":
            colors.append(RISK_COLORS["alto"] if val > 30 else RISK_COLORS["bajo"])
        else:
            colors.append(SEVILLA_RED)

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        hovertemplate="%{y}: %{x:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=f"Factores de riesgo: {player}", font=dict(size=14)),
        height=300,
        margin=dict(t=40, b=40, l=150, r=80),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Correlaciones
# ---------------------------------------------------------------------------

def correlation_heatmap(corr_df: pd.DataFrame):
    """Matriz de correlaciones entre pares de variables."""
    if corr_df.empty:
        fig = go.Figure()
        return _apply_template(fig)

    # Build correlation matrix (labels as axes)
    labels_x = corr_df["var_x"].tolist()
    labels_y = corr_df["var_y"].tolist()
    all_vars = list(dict.fromkeys(labels_x + labels_y))
    n = len(all_vars)

    matrix = np.full((n, n), np.nan)
    np.fill_diagonal(matrix, 1.0)

    for _, row in corr_df.iterrows():
        i = all_vars.index(row["var_x"])
        j = all_vars.index(row["var_y"])
        val = row["statistic"] if pd.notna(row["statistic"]) else 0
        matrix[i, j] = val
        matrix[j, i] = val

    # Significance markers
    text_matrix = np.empty((n, n), dtype=object)
    for i in range(n):
        for j in range(n):
            if np.isnan(matrix[i, j]):
                text_matrix[i, j] = ""
            else:
                val_str = f"{matrix[i, j]:.2f}"
                # Check if significant
                match = corr_df[((corr_df["var_x"] == all_vars[i]) & (corr_df["var_y"] == all_vars[j])) |
                                ((corr_df["var_x"] == all_vars[j]) & (corr_df["var_y"] == all_vars[i]))]
                if not match.empty and match.iloc[0].get("significant", False):
                    val_str += " *"
                text_matrix[i, j] = val_str

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=all_vars,
        y=all_vars,
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        text=text_matrix,
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="X: %{x}<br>Y: %{y}<br>r: %{z:.3f}<extra></extra>",
        colorbar=dict(title="r"),
    ))

    fig.update_layout(
        height=max(400, n * 60),
        margin=dict(t=20, b=100, l=150, r=20),
        xaxis_tickangle=-30,
    )
    return _apply_template(fig)


def correlation_detail_scatter(dynamic_sev: pd.DataFrame, var_x: str, var_y: str,
                                label_x: str, label_y: str):
    """Scatter con regresion lineal para un par de variables."""
    from dashboard.data.inference import _prepare_dynamic_for_correlations

    df = _prepare_dynamic_for_correlations(dynamic_sev)

    if var_x not in df.columns or var_y not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Variables no disponibles", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_template(fig)

    valid = df[[var_x, var_y, "player_name"]].dropna()
    if valid.empty:
        fig = go.Figure()
        return _apply_template(fig)

    x = valid[var_x].astype(float)
    y = valid[var_y].astype(float)

    fig = go.Figure()

    # Scatter points
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="markers",
        marker=dict(size=6, color=SEVILLA_RED, opacity=0.4),
        hovertemplate=f"{label_x}: %{{x:.2f}}<br>{label_y}: %{{y:.2f}}<extra></extra>",
        showlegend=False,
    ))

    # Regression line
    from scipy import stats as sp_stats
    if len(x) > 2:
        slope, intercept, r, p, se = sp_stats.linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 50)
        y_line = slope * x_line + intercept
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line,
            mode="lines",
            line=dict(color="#333", width=2, dash="dash"),
            name=f"r={r:.3f}, p={p:.4f}",
            hovertemplate=f"Regresión: r={r:.3f}<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title=label_x,
        yaxis_title=label_y,
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


def significance_forest(corr_df: pd.DataFrame):
    """Forest plot con intervalos de confianza."""
    if corr_df.empty:
        fig = go.Figure()
        return _apply_template(fig)

    df = corr_df.copy()
    df["pair_label"] = df["var_x"] + " vs " + df["var_y"]
    df = df.sort_values("statistic", ascending=True)

    colors = [SEVILLA_RED if sig else "#999" for sig in df["significant"]]

    fig = go.Figure()

    # CI error bars
    for i, (_, row) in enumerate(df.iterrows()):
        stat = row["statistic"] if pd.notna(row["statistic"]) else 0
        ci_lo = row.get("ci_lower", stat)
        ci_hi = row.get("ci_upper", stat)
        color = SEVILLA_RED if row.get("significant", False) else "#999"

        fig.add_trace(go.Scatter(
            x=[ci_lo, ci_hi],
            y=[row["pair_label"], row["pair_label"]],
            mode="lines",
            line=dict(color=color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Point estimates
    fig.add_trace(go.Scatter(
        x=df["statistic"],
        y=df["pair_label"],
        mode="markers",
        marker=dict(size=10, color=colors, symbol="diamond",
                    line=dict(width=1, color="white")),
        showlegend=False,
        hovertemplate="<b>%{y}</b><br>r = %{x:.3f}<extra></extra>",
    ))

    # Zero line
    fig.add_vline(x=0, line_dash="dash", line_color="#ccc")

    fig.update_layout(
        xaxis_title="Correlación (Spearman)",
        xaxis_range=[-1, 1],
        height=max(350, len(df) * 50),
        margin=dict(t=20, b=60, l=200, r=40),
    )
    return _apply_template(fig)
