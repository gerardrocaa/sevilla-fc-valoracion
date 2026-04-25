"""Graficos Plotly para Modulo 5: Valoracion Multidimensional."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import (
    M5_DATA_SOURCES,
    M5_DIM_LABELS,
    PLOTLY_TEMPLATE,
    PROFILE_COLORS,
    SEVILLA_RED,
    SEVILLA_WHITE,
    label,
)

_SCORE_DIMS = ["score_rendimiento", "score_fisico", "score_mercado", "score_comercial", "score_medico"]
_DIM_NAMES = [M5_DIM_LABELS[d] for d in _SCORE_DIMS]

_REAL_COLOR = "#2A9D8F"
_ESTIMATED_COLOR = "#E9C46A"


def _apply_template(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    fig.update_layout(
        dragmode=False,
        margin=dict(t=20, b=60, l=120, r=80),
    )
    fig.update_xaxes(fixedrange=True, automargin=True)
    fig.update_yaxes(fixedrange=True, automargin=True)
    return fig


def _dim_color(dim_name: str) -> str:
    """Color segun si la dimension usa datos reales o estimados."""
    return _REAL_COLOR if M5_DATA_SOURCES.get(dim_name) == "real" else _ESTIMATED_COLOR


# ---------------------------------------------------------------------------
# 1. Radar individual (5 ejes)
# ---------------------------------------------------------------------------

def valuation_radar(player_row: pd.Series, player_name: str) -> go.Figure:
    """Radar de 5 dimensiones para un jugador."""
    values = [player_row.get(d, 0) for d in _SCORE_DIMS]
    values_closed = values + [values[0]]
    cats = _DIM_NAMES + [_DIM_NAMES[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=cats,
        fill="toself",
        fillcolor=f"rgba(212, 0, 30, 0.15)",
        line=dict(color=SEVILLA_RED, width=2),
        marker=dict(size=6, color=SEVILLA_RED),
        name=player_name,
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[25, 50, 75, 100]),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        showlegend=False,
        height=400,
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 2. Radar dual (comparativa 2 jugadores)
# ---------------------------------------------------------------------------

def valuation_radar_dual(
    row_a: pd.Series, name_a: str,
    row_b: pd.Series, name_b: str,
) -> go.Figure:
    """Radar superpuesto de 2 jugadores."""
    vals_a = [row_a.get(d, 0) for d in _SCORE_DIMS] + [row_a.get(_SCORE_DIMS[0], 0)]
    vals_b = [row_b.get(d, 0) for d in _SCORE_DIMS] + [row_b.get(_SCORE_DIMS[0], 0)]
    cats = _DIM_NAMES + [_DIM_NAMES[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_a, theta=cats, fill="toself",
        fillcolor="rgba(212, 0, 30, 0.12)",
        line=dict(color=SEVILLA_RED, width=2),
        name=name_a,
        hovertemplate=f"<b>{name_a}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_b, theta=cats, fill="toself",
        fillcolor="rgba(69, 123, 157, 0.12)",
        line=dict(color="#457B9D", width=2),
        name=name_b,
        hovertemplate=f"<b>{name_b}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[25, 50, 75, 100]),
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        height=420,
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 3. Ranking horizontal bars
# ---------------------------------------------------------------------------

def valuation_ranking_bar(df: pd.DataFrame) -> go.Figure:
    """Barras horizontales del ranking de equipo por integral_score."""
    sorted_df = df.sort_values("integral_score", ascending=True)

    colors = []
    for _, row in sorted_df.iterrows():
        profile = row.get("profile", "")
        colors.append(PROFILE_COLORS.get(profile, SEVILLA_RED))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sorted_df["integral_score"],
        y=sorted_df["player_name"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in sorted_df["integral_score"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score Integral: %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Score Integral (0-100)",
        xaxis_range=[0, max(sorted_df["integral_score"].max() * 1.15, 10)],
        yaxis_title="",
        height=max(400, len(sorted_df) * 28),
        margin=dict(l=140, r=60, t=10, b=40),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 4. Heatmap jugadores x dimensiones
# ---------------------------------------------------------------------------

def valuation_breakdown_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap con jugadores en filas y dimensiones en columnas."""
    sorted_df = df.sort_values("integral_score", ascending=False)
    z = sorted_df[_SCORE_DIMS].values
    players = sorted_df["player_name"].tolist()

    # Texto hover con nombre dimension
    hover_text = []
    for i, p in enumerate(players):
        row_text = []
        for j, dim in enumerate(_DIM_NAMES):
            src = "Real" if M5_DATA_SOURCES.get(dim) == "real" else "Externo"
            row_text.append(f"{p}<br>{dim}: {z[i][j]:.1f}<br>{src}")
        hover_text.append(row_text)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=_DIM_NAMES,
        y=players,
        colorscale=[
            [0, "#FFF5F5"],
            [0.3, "#FED7D7"],
            [0.5, "#FEB2B2"],
            [0.7, "#FC8181"],
            [1, "#C53030"],
        ],
        zmin=0,
        zmax=100,
        text=[[f"{v:.0f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=11),
        hovertext=hover_text,
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar=dict(title="Score", tickvals=[0, 25, 50, 75, 100]),
    ))

    fig.update_layout(
        xaxis=dict(side="top", tickangle=-30),
        height=max(400, len(players) * 30),
        margin=dict(l=140, r=20, t=80, b=20),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 5. Scatter rendimiento vs mercado (cuadrantes)
# ---------------------------------------------------------------------------

def value_performance_quadrant(df: pd.DataFrame) -> go.Figure:
    """Scatter: rendimiento (x) vs valor de mercado (y) con cuadrantes."""
    fig = go.Figure()

    med_rend = df["score_rendimiento"].median()
    med_market = df["market_value_m"].median()

    # Cuadrantes (shapes)
    max_x = df["score_rendimiento"].max() * 1.1
    max_y = df["market_value_m"].max() * 1.15

    quadrant_labels = [
        (med_rend / 2, max_y * 0.92, "Sobrevalorado"),
        ((med_rend + max_x) / 2, max_y * 0.92, "Estrella"),
        (med_rend / 2, med_market * 0.3, "Bajo perfil"),
        ((med_rend + max_x) / 2, med_market * 0.3, "Ganga"),
    ]

    for x, y, txt in quadrant_labels:
        fig.add_annotation(
            x=x, y=y, text=txt,
            showarrow=False, font=dict(size=12, color="rgba(0,0,0,0.2)"),
        )

    # Lineas de mediana
    fig.add_hline(y=med_market, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=med_rend, line_dash="dot", line_color="gray", opacity=0.5)

    # Puntos por perfil
    for profile in df["profile"].unique():
        sub = df[df["profile"] == profile]
        color = PROFILE_COLORS.get(profile, SEVILLA_RED)
        fig.add_trace(go.Scatter(
            x=sub["score_rendimiento"],
            y=sub["market_value_m"],
            mode="markers+text",
            marker=dict(size=12, color=color, line=dict(width=1, color="white")),
            text=sub["player_name"],
            textposition="top center",
            textfont=dict(size=9),
            name=profile,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Rendimiento: %{x:.1f}<br>"
                "Valor mercado: %{y:.1f}M€<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Score Rendimiento (0-100)",
        yaxis_title="Valor de Mercado (M€)",
        xaxis_range=[0, max_x],
        yaxis_range=[0, max_y],
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
        height=500,
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 6. Barras de dimension para un jugador
# ---------------------------------------------------------------------------

def dimension_detail_bars(player_row: pd.Series, player_name: str) -> go.Figure:
    """Barras horizontales por dimension para un jugador, coloreadas por fuente."""
    values = [player_row.get(d, 0) for d in _SCORE_DIMS]
    colors = [_dim_color(name) for name in _DIM_NAMES]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=values,
        y=_DIM_NAMES,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Score (0-100)",
        xaxis_range=[0, 110],
        yaxis_title="",
        height=300,
        margin=dict(l=160, r=60, t=10, b=40),
        showlegend=False,
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# 7. Leyenda de fuentes de datos (HTML)
# ---------------------------------------------------------------------------

def data_source_legend() -> str:
    """Devuelve HTML para leyenda de datos reales vs externos."""
    items = []
    for dim, src in M5_DATA_SOURCES.items():
        color = _REAL_COLOR if src == "real" else _ESTIMATED_COLOR
        icon = "[R]" if src == "real" else "[E]"
        tag = "Datos reales" if src == "real" else "Datos externos"
        items.append(
            f'<span style="display:inline-block;margin-right:16px;">'
            f'{icon} <b>{dim}</b> '
            f'<span style="color:{color};font-size:0.85em;">({tag})</span>'
            f'</span>'
        )
    return (
        '<div style="background:#f9f9f9;padding:10px 14px;border-radius:6px;'
        'border-left:4px solid #D4001E;margin-bottom:12px;line-height:1.8;">'
        + "".join(items)
        + "</div>"
    )
