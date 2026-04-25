"""Fabrica de graficos Plotly para el dashboard."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import (
    DIM_COLS,
    DIM_LABELS,
    EVENT_SUBTYPE_ES,
    MATCHES,
    PHASE_ES,
    PLOTLY_TEMPLATE,
    PROFILE_COLORS,
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
# Vista General
# ---------------------------------------------------------------------------

def ranking_bar(df: pd.DataFrame, col: str = "composite_score"):
    df_sorted = df.sort_values(col, ascending=True)
    colors = [PROFILE_COLORS.get(p, "#999") for p in df_sorted["profile"]]
    max_val = df_sorted[col].max() if len(df_sorted) > 0 else 1

    fig = go.Figure(go.Bar(
        x=df_sorted[col],
        y=df_sorted["player_name"],
        orientation="h",
        marker_color=colors,
        text=df_sorted[col].round(3),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Score", yaxis_title="",
        height=max(400, len(df_sorted) * 38),
        xaxis_range=[0, max_val * 1.25],
    )
    return _apply_template(fig)


def heatmap_jugadores_jornadas(scores_all: pd.DataFrame, col: str = "composite_score"):
    pivot = scores_all.pivot_table(
        index="player_name", columns="jornada", values=col, aggfunc="first"
    )
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    pivot = pivot.reindex(columns=[j for j in jornada_order if j in pivot.columns])
    pivot = pivot.reindex(pivot.mean(axis=1).sort_values(ascending=False).index)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="RdYlGn",
        text=np.where(pd.notna(pivot.values), np.round(pivot.values, 2).astype(str), ""),
        texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="Score"),
        hovertemplate="Jugador: %{y}<br>Jornada: %{x}<br>Score: %{z:.4f}<extra></extra>",
        zmin=0, zmax=1,
    ))
    fig.update_layout(
        height=max(450, len(pivot) * 35),
        yaxis=dict(autorange="reversed"),
    )
    return _apply_template(fig)


def team_evolution(scores_all: pd.DataFrame):
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    mean_by_j = scores_all.groupby("jornada")["composite_score"].mean().reindex(jornada_order).dropna()

    labels_list = []
    for j in mean_by_j.index:
        mid = next((m for m, info in MATCHES.items() if info["jornada"] == j), None)
        labels_list.append(f"{j}<br>{MATCHES[mid]['score']}" if mid else j)

    fig = go.Figure(go.Scatter(
        x=labels_list,
        y=mean_by_j.values,
        mode="lines+markers+text",
        text=[f"{v:.3f}" for v in mean_by_j.values],
        textposition="top center",
        line=dict(color=SEVILLA_RED, width=3),
        marker=dict(size=10),
        hovertemplate="Jornada: %{x}<br>Score medio: %{y:.4f}<extra></extra>",
    ))
    fig.update_layout(
        yaxis_title="Score Compuesto Medio",
        yaxis_range=[0, 1.05],
        height=420,
    )
    return _apply_template(fig)


def dimension_stacked_bar(scores_all: pd.DataFrame):
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    dim_colors = ["#E63946", "#457B9D", "#2A9D8F", "#264653", "#E9C46A", "#F4A261"]

    fig = go.Figure()
    for i, dim in enumerate(DIM_COLS):
        means = scores_all.groupby("jornada")[dim].mean().reindex(jornada_order).fillna(0)
        fig.add_trace(go.Bar(
            x=means.index,
            y=means.values,
            name=DIM_LABELS[dim],
            marker_color=dim_colors[i],
            hovertemplate=f"{DIM_LABELS[dim]}<br>Jornada: %{{x}}<br>Score: %{{y:.4f}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        yaxis_title="Score acumulado",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=50, b=60, l=80, r=20),
    )
    return _apply_template(fig)


def top5_by_dimension(aggregated: pd.DataFrame):
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[DIM_LABELS[d] for d in DIM_COLS],
        horizontal_spacing=0.25,
        vertical_spacing=0.22,
    )

    for idx, dim in enumerate(DIM_COLS):
        row, col = idx // 3 + 1, idx % 3 + 1
        top = aggregated.dropna(subset=[dim]).nlargest(5, dim)
        colors = [PROFILE_COLORS.get(p, "#999") for p in top["profile"]]
        max_val = top[dim].max() if len(top) > 0 else 1

        fig.add_trace(go.Bar(
            x=top[dim],
            y=top["player_name"],
            orientation="h",
            marker_color=colors,
            text=top[dim].round(3),
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(size=10, color="white"),
            showlegend=False,
            hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
        ), row=row, col=col)

    # Uniform x-axis [0, 1] across all subplots for fair comparison
    fig.update_xaxes(range=[0, 1], dtick=0.25)

    fig.update_layout(
        height=750,
        margin=dict(l=140, r=30, t=40, b=30),
    )
    # Update subplot title font size to avoid overlap
    for ann in fig.layout.annotations:
        ann.font.size = 12
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Perfil Individual
# ---------------------------------------------------------------------------

def radar_chart(player_scores: pd.DataFrame, dim_labels: dict = None):
    if dim_labels is None:
        dim_labels = DIM_LABELS
    categories = list(dim_labels.values())

    fig = go.Figure()
    for _, row in player_scores.iterrows():
        values = [row.get(d, 0) for d in dim_labels.keys()]
        values_closed = values + [values[0]]
        cats_closed = categories + [categories[0]]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=cats_closed,
            fill="toself",
            opacity=0.3,
            name=row.get("jornada", row.get("match_label", "")),
            hovertemplate="%{theta}: %{r:.4f}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=500,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=80, l=60, r=60),
    )
    return _apply_template(fig)


def radar_vs_team(player_agg: pd.Series, team_avg: pd.Series, player_name: str = ""):
    categories = list(DIM_LABELS.values())
    dims = list(DIM_LABELS.keys())

    p_vals = [player_agg.get(d, 0) for d in dims]
    t_vals = [team_avg.get(d, 0) for d in dims]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=p_vals + [p_vals[0]],
        theta=categories + [categories[0]],
        fill="toself", name=player_name, opacity=0.4,
        line=dict(color=SEVILLA_RED),
    ))
    fig.add_trace(go.Scatterpolar(
        r=t_vals + [t_vals[0]],
        theta=categories + [categories[0]],
        fill="toself", name="Media equipo", opacity=0.2,
        line=dict(color="#999"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=500,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=60, l=60, r=60),
    )
    return _apply_template(fig)


def evolution_lines(scores_all: pd.DataFrame, players: list, col: str = "composite_score"):
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    fig = go.Figure()
    for player in players:
        p_data = scores_all[scores_all["player_name"] == player].copy()
        p_data["j_order"] = pd.Categorical(p_data["jornada"], categories=jornada_order, ordered=True)
        p_data = p_data.sort_values("j_order")

        profile = p_data["profile"].iloc[0] if len(p_data) > 0 else "WM"
        color = PROFILE_COLORS.get(profile, "#999")

        fig.add_trace(go.Scatter(
            x=p_data["jornada"],
            y=p_data[col],
            mode="lines+markers",
            name=player,
            line=dict(color=color, width=2),
            marker=dict(size=8),
            hovertemplate=f"<b>{player}</b><br>Jornada: %{{x}}<br>Score: %{{y:.4f}}<extra></extra>",
        ))

    col_label = DIM_LABELS.get(col, col)
    fig.update_layout(
        yaxis_title=col_label,
        yaxis_range=[0, 1.05],
        height=420,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=80, l=80, r=20),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Comparativa
# ---------------------------------------------------------------------------

def scatter_configurable(df: pd.DataFrame, x_col: str, y_col: str, size_col: str = "total_minutes"):
    fig = go.Figure()
    for _, row in df.iterrows():
        color = PROFILE_COLORS.get(row["profile"], "#999")
        size = max(8, (row.get(size_col, 100) / 50)) if size_col else 12
        fig.add_trace(go.Scatter(
            x=[row[x_col]], y=[row[y_col]],
            mode="markers+text",
            text=[row["player_name"]],
            textposition="top center",
            marker=dict(size=size, color=color, opacity=0.7),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['player_name']}</b> ({row['profile']})<br>"
                f"{label(x_col)}: %{{x:.4f}}<br>{label(y_col)}: %{{y:.4f}}<extra></extra>"
            ),
        ))

    x_vals = df[x_col].dropna()
    y_vals = df[y_col].dropna()
    if len(x_vals) > 0:
        x_pad = (x_vals.max() - x_vals.min()) * 0.15 if x_vals.max() != x_vals.min() else 0.1
        y_pad = (y_vals.max() - y_vals.min()) * 0.22 if y_vals.max() != y_vals.min() else 0.1
        fig.update_layout(
            xaxis_range=[x_vals.min() - x_pad, x_vals.max() + x_pad],
            yaxis_range=[y_vals.min() - y_pad, y_vals.max() + y_pad],
        )

    fig.update_layout(
        xaxis_title=label(x_col), yaxis_title=label(y_col), height=470,
    )
    return _apply_template(fig)


def boxplot_consistency(scores_all: pd.DataFrame, players: list):
    filtered = scores_all[scores_all["player_name"].isin(players)]
    fig = go.Figure()
    for player in players:
        p_data = filtered[filtered["player_name"] == player]
        profile = p_data["profile"].iloc[0] if len(p_data) > 0 else "WM"
        color = PROFILE_COLORS.get(profile, "#999")
        fig.add_trace(go.Box(
            y=p_data["composite_score"],
            name=player,
            marker_color=color,
            boxmean=True,
            hovertemplate="<b>%{x}</b><br>Score: %{y:.4f}<extra></extra>",
        ))
    fig.update_layout(
        yaxis_title="Score Compuesto",
        yaxis_range=[-0.05, 1.05],
        height=420,
        xaxis_tickangle=-30,
    )
    return _apply_template(fig)


def grouped_dimension_bars(aggregated: pd.DataFrame, players: list):
    filtered = aggregated[aggregated["player_name"].isin(players)]
    dim_colors_list = ["#E63946", "#457B9D", "#2A9D8F", "#264653", "#E9C46A", "#F4A261"]

    fig = go.Figure()
    for i, dim in enumerate(DIM_COLS):
        fig.add_trace(go.Bar(
            x=filtered["player_name"],
            y=filtered[dim],
            name=DIM_LABELS[dim],
            marker_color=dim_colors_list[i],
            hovertemplate=f"{DIM_LABELS[dim]}<br>%{{x}}: %{{y:.4f}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="group",
        yaxis_title="Score",
        yaxis_range=[0, 1.05],
        height=470,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=100, l=60, r=20),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Datos Fisicos
# ---------------------------------------------------------------------------

def physical_bar(physical: pd.DataFrame, metric: str, players: list):
    filtered = physical[physical["dyn_name"].isin(players)].copy()
    if filtered.empty or metric not in filtered.columns:
        fig = go.Figure()
        fig.add_annotation(text=f"Sin datos para {metric}", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5, font=dict(size=14))
        return _apply_template(fig)

    agg = filtered.groupby("dyn_name")[metric].mean().sort_values(ascending=True)
    max_val = agg.max() if len(agg) > 0 else 1

    fig = go.Figure(go.Bar(
        x=agg.values,
        y=agg.index,
        orientation="h",
        marker_color=SEVILLA_RED,
        text=agg.values.round(1),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + label(metric) + ": %{x:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=max(380, len(agg) * 38),
        xaxis_range=[0, max_val * 1.25],
    )
    return _apply_template(fig)


def physical_heatmap(physical: pd.DataFrame, metrics: list, players: list):
    filtered = physical[physical["dyn_name"].isin(players)].copy()
    if filtered.empty:
        fig = go.Figure()
        return _apply_template(fig)

    valid_metrics = [m for m in metrics if m in filtered.columns]
    if not valid_metrics:
        fig = go.Figure()
        return _apply_template(fig)

    pivot = filtered.groupby("dyn_name")[valid_metrics].mean()
    norm = (pivot - pivot.min()) / (pivot.max() - pivot.min() + 1e-9)

    fig = go.Figure(go.Heatmap(
        z=norm.values,
        x=[label(m) for m in valid_metrics],
        y=norm.index.tolist(),
        colorscale="YlOrRd",
        text=pivot.values.round(1).astype(str),
        texttemplate="%{text}",
        textfont={"size": 10},
        hovertemplate="Jugador: %{y}<br>Metrica: %{x}<br>Valor: %{text}<extra></extra>",
    ))
    fig.update_layout(
        height=max(450, len(norm) * 38),
        xaxis_tickangle=-30,
    )
    return _apply_template(fig)


def physical_scatter(physical: pd.DataFrame, x_metric: str, y_metric: str, players: list):
    filtered = physical[physical["dyn_name"].isin(players)].copy()
    if filtered.empty or x_metric not in filtered.columns or y_metric not in filtered.columns:
        fig = go.Figure()
        return _apply_template(fig)

    agg = filtered.groupby("dyn_name")[[x_metric, y_metric]].mean().reset_index()
    fig = go.Figure()
    for _, row in agg.iterrows():
        fig.add_trace(go.Scatter(
            x=[row[x_metric]], y=[row[y_metric]],
            mode="markers+text",
            text=[row["dyn_name"]],
            textposition="top center",
            marker=dict(size=12, color=SEVILLA_RED, opacity=0.7),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['dyn_name']}</b><br>"
                f"{label(x_metric)}: %{{x:.1f}}<br>{label(y_metric)}: %{{y:.1f}}<extra></extra>"
            ),
        ))

    if len(agg) > 0:
        x_pad = (agg[x_metric].max() - agg[x_metric].min()) * 0.15 if agg[x_metric].max() != agg[x_metric].min() else max(agg[x_metric].mean() * 0.1, 1)
        y_pad = (agg[y_metric].max() - agg[y_metric].min()) * 0.22 if agg[y_metric].max() != agg[y_metric].min() else max(agg[y_metric].mean() * 0.1, 1)
        fig.update_layout(
            xaxis_range=[agg[x_metric].min() - x_pad, agg[x_metric].max() + x_pad],
            yaxis_range=[agg[y_metric].min() - y_pad, agg[y_metric].max() + y_pad],
        )

    fig.update_layout(
        xaxis_title=label(x_metric), yaxis_title=label(y_metric), height=470,
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Explorador de Eventos
# ---------------------------------------------------------------------------

def pressure_histogram(dynamic: pd.DataFrame, player: str = None):
    df = dynamic.copy()
    if player:
        df = df[df["player_name"] == player]

    fig = go.Figure()
    for col_name, label in [("overall_pressure_start", "Presion inicio"),
                            ("overall_pressure_end", "Presion fin")]:
        if col_name in df.columns:
            counts = df[col_name].value_counts().reindex(
                ["no_pressure", "low_pressure", "medium_pressure",
                 "high_pressure", "very_high_pressure"]
            ).fillna(0)
            counts.index = ["Ninguna", "Baja", "Media", "Alta", "Muy alta"]
            fig.add_trace(go.Bar(
                x=counts.index, y=counts.values, name=label,
                hovertemplate="%{x}: %{y}<extra></extra>",
            ))

    fig.update_layout(
        barmode="group",
        height=420,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(t=20, b=70, l=60, r=20),
    )
    return _apply_template(fig)


def phase_donut(dynamic: pd.DataFrame, player: str = None):
    df = dynamic.copy()
    if player:
        df = df[df["player_name"] == player]

    col = "team_in_possession_phase_type"
    if col not in df.columns:
        fig = go.Figure()
        return _apply_template(fig)

    counts = df[col].value_counts()
    counts.index = [PHASE_ES.get(v, v) for v in counts.index]
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.45,
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=420,
        showlegend=False,
        margin=dict(t=20, b=40, l=60, r=60),
    )
    return _apply_template(fig)


def event_subtype_bars(dynamic: pd.DataFrame):
    if "event_subtype" not in dynamic.columns:
        fig = go.Figure()
        return _apply_template(fig)

    counts = dynamic["event_subtype"].value_counts().head(15)
    counts.index = [EVENT_SUBTYPE_ES.get(v, v) for v in counts.index]
    max_val = counts.max() if len(counts) > 0 else 1

    fig = go.Figure(go.Bar(
        x=counts.values,
        y=counts.index,
        orientation="h",
        marker_color=SEVILLA_RED,
        text=counts.values,
        textposition="outside",
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(
        height=max(400, len(counts) * 30),
        xaxis_range=[0, max_val * 1.2],
    )
    return _apply_template(fig)
