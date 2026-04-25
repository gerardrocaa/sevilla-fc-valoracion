"""Graficos Plotly para Modulo 4: Escenarios What-If."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import (
    BLOCK_LABELS,
    DIM_LABELS,
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
# Escenario 1: Ausencia de jugador
# ---------------------------------------------------------------------------

def absence_comparison_bar(baseline: dict, simulated: dict) -> go.Figure:
    """Barras agrupadas: baseline vs simulado con error bars.

    Args:
        baseline: {metric: {mean, P25, P50, P75}}.
        simulated: mismo formato.
    """
    metrics = sorted(baseline.keys())
    dim_labels = {**DIM_LABELS, "composite_score": "Score Compuesto"}
    names = [dim_labels.get(m, m) for m in metrics]

    base_vals = [baseline[m]["mean"] for m in metrics]
    sim_vals = [simulated[m]["mean"] for m in metrics]
    base_lo = [baseline[m]["mean"] - baseline[m]["P25"] for m in metrics]
    base_hi = [baseline[m]["P75"] - baseline[m]["mean"] for m in metrics]
    sim_lo = [simulated[m]["mean"] - simulated[m]["P25"] for m in metrics]
    sim_hi = [simulated[m]["P75"] - simulated[m]["mean"] for m in metrics]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Con jugador (baseline)",
        x=names, y=base_vals,
        marker_color="#2A9D8F",
        error_y=dict(type="data", symmetric=False, array=base_hi, arrayminus=base_lo, thickness=1.5),
        hovertemplate="<b>%{x}</b><br>Media: %{y:.3f}<extra>Baseline</extra>",
    ))

    fig.add_trace(go.Bar(
        name="Sin jugador (simulado)",
        x=names, y=sim_vals,
        marker_color="#E63946",
        error_y=dict(type="data", symmetric=False, array=sim_hi, arrayminus=sim_lo, thickness=1.5),
        hovertemplate="<b>%{x}</b><br>Media: %{y:.3f}<extra>Simulado</extra>",
    ))

    fig.update_layout(
        barmode="group",
        yaxis_title="Score medio del equipo",
        yaxis_range=[0, 1],
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


def absence_distribution_box(baseline: dict, simulated: dict) -> go.Figure:
    """Violin/box comparativo baseline vs simulado por metrica."""
    dim_labels = {**DIM_LABELS, "composite_score": "Score Compuesto"}
    metrics = sorted(baseline.keys())

    fig = go.Figure()
    for m in metrics:
        name = dim_labels.get(m, m)
        # Baseline point
        b = baseline[m]
        fig.add_trace(go.Box(
            y=[b["P25"], b["P50"], b["mean"], b["P75"]],
            name=name,
            marker_color="#2A9D8F",
            boxpoints=False,
            legendgroup="baseline",
            legendgrouptitle_text="Baseline",
            showlegend=(m == metrics[0]),
        ))
        # Simulado point
        s = simulated[m]
        fig.add_trace(go.Box(
            y=[s["P25"], s["P50"], s["mean"], s["P75"]],
            name=name,
            marker_color="#E63946",
            boxpoints=False,
            legendgroup="simulado",
            legendgrouptitle_text="Sin jugador",
            showlegend=(m == metrics[0]),
        ))

    fig.update_layout(
        yaxis_title="Score",
        yaxis_range=[0, 1],
        height=400,
        boxmode="group",
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


def redistribution_table_chart(redistribution: list[dict]) -> go.Figure:
    """Barras horizontales mostrando peso de redistribucion de contribucion."""
    if not redistribution:
        fig = go.Figure()
        fig.add_annotation(text="Sin pares posicionales", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_template(fig)

    df = pd.DataFrame(redistribution).sort_values("weight", ascending=True)

    colors = [PROFILE_COLORS.get(p, SEVILLA_RED) for p in df["profile"]]

    fig = go.Figure(go.Bar(
        x=df["weight"],
        y=df["player_name"],
        orientation="h",
        marker_color=colors,
        text=[f"{w:.0%}" for w in df["weight"]],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Peso: %{x:.1%}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        xaxis_title="Peso de redistribucion",
        xaxis_range=[0, max(df["weight"].max() * 1.3, 0.5)],
        xaxis_tickformat=".0%",
        height=max(300, len(df) * 40),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Escenario 2: Bloque defensivo
# ---------------------------------------------------------------------------

def block_grouped_bar(summaries: dict) -> go.Figure:
    """Barras agrupadas por tipo de bloque con error bars."""
    metrics = ["pressing_rate", "solidity", "recovery_rate"]
    metric_labels = {
        "pressing_rate": "Tasa pressing",
        "solidity": "Solidez",
        "recovery_rate": "Tasa recuperacion",
        "pressing_chain_mean": "Cadena pressing",
        "danger_neutralized": "Peligro neutralizado",
    }
    block_colors = {
        "high_block": "#E63946",
        "medium_block": "#E9C46A",
        "low_block": "#2A9D8F",
    }

    fig = go.Figure()
    for bt, summary in summaries.items():
        vals = []
        lo = []
        hi = []
        for m in metrics:
            ms = summary.get(m, {})
            if isinstance(ms, dict):
                vals.append(ms.get("mean", 0))
                lo.append(ms.get("mean", 0) - ms.get("P25", 0))
                hi.append(ms.get("P75", 0) - ms.get("mean", 0))
            else:
                vals.append(0)
                lo.append(0)
                hi.append(0)

        fig.add_trace(go.Bar(
            name=BLOCK_LABELS.get(bt, bt),
            x=[metric_labels.get(m, m) for m in metrics],
            y=vals,
            marker_color=block_colors.get(bt, "#999"),
            error_y=dict(type="data", symmetric=False, array=hi, arrayminus=lo, thickness=1.5),
            hovertemplate="<b>%{x}</b><br>Media: %{y:.3f}<extra>" + BLOCK_LABELS.get(bt, bt) + "</extra>",
        ))

    fig.update_layout(
        barmode="group",
        yaxis_title="Valor",
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


def block_radar(summaries: dict) -> go.Figure:
    """Radar superpuesto con un trazo por tipo de bloque."""
    metrics = ["pressing_rate", "pressing_chain_mean", "solidity", "recovery_rate"]
    metric_labels = {
        "pressing_rate": "Pressing",
        "pressing_chain_mean": "Cadena press.",
        "solidity": "Solidez",
        "recovery_rate": "Recuperacion",
    }
    block_colors = {
        "high_block": "#E63946",
        "medium_block": "#E9C46A",
        "low_block": "#2A9D8F",
    }

    fig = go.Figure()
    for bt, summary in summaries.items():
        vals = []
        for m in metrics:
            ms = summary.get(m, {})
            vals.append(ms.get("mean", 0) if isinstance(ms, dict) else 0)

        vals_closed = vals + [vals[0]]
        cats_closed = [metric_labels.get(m, m) for m in metrics] + [metric_labels.get(metrics[0], metrics[0])]

        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=cats_closed,
            fill="toself",
            opacity=0.3,
            name=BLOCK_LABELS.get(bt, bt),
            line=dict(color=block_colors.get(bt, "#999"), width=2),
            hovertemplate="%{theta}: %{r:.3f}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        margin=dict(t=20, b=80, l=60, r=60),
    )
    return _apply_template(fig)


def block_per_match_heatmap(per_match_data: dict) -> go.Figure:
    """Heatmap mostrando distribucion de metricas de bloques por partido."""
    from dashboard.config import MATCHES

    rows = []
    for bt, records in per_match_data.items():
        for rec in records:
            mid = rec.get("match_id")
            match_label = MATCHES.get(mid, {}).get("label", str(mid)) if mid else str(mid)
            rows.append({
                "block": BLOCK_LABELS.get(bt, bt),
                "match": match_label,
                "n_events": rec.get("n_events", 0),
                "pressing_rate": rec.get("pressing_rate", 0),
                "solidity": rec.get("solidity", 0),
            })

    if not rows:
        fig = go.Figure()
        fig.add_annotation(text="Sin datos por partido", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_template(fig)

    df = pd.DataFrame(rows)

    # Pivot: filas = bloque, columnas = partido, valores = n_events
    pivot = df.pivot_table(index="block", columns="match", values="n_events", fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale="YlOrRd",
        text=pivot.values.astype(int).astype(str),
        texttemplate="%{text}",
        textfont={"size": 11},
        hovertemplate="Bloque: %{y}<br>Partido: %{x}<br>Eventos: %{z}<extra></extra>",
        colorbar=dict(title="Eventos"),
    ))

    fig.update_layout(
        height=300,
        margin=dict(t=20, b=60, l=120, r=20),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Escenario 3: Rotacion por carga fisica
# ---------------------------------------------------------------------------

def fatigue_projection_dual(baseline_curve: list, rotated_curve: list) -> go.Figure:
    """Dos lineas con bandas CI: baseline vs rotacion.

    Marcas X donde el jugador descansa.
    """
    fig = go.Figure()

    # Baseline
    x_labels = [p["label"] for p in baseline_curve]
    base_mean = [p["mean"] for p in baseline_curve]
    base_p25 = [p["P25"] for p in baseline_curve]
    base_p75 = [p["P75"] for p in baseline_curve]

    # Banda CI baseline
    fig.add_trace(go.Scatter(
        x=x_labels + x_labels[::-1],
        y=base_p75 + base_p25[::-1],
        fill="toself",
        fillcolor="rgba(230, 57, 70, 0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(
        x=x_labels, y=base_mean,
        mode="lines+markers",
        name="Sin rotacion",
        line=dict(color="#E63946", width=2.5),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Fatiga: %{y:.3f}<extra>Sin rotacion</extra>",
    ))

    # Rotacion
    rot_mean = [p["mean"] for p in rotated_curve]
    rot_p25 = [p["P25"] for p in rotated_curve]
    rot_p75 = [p["P75"] for p in rotated_curve]
    rest_markers = [i for i, p in enumerate(rotated_curve) if p.get("is_rest")]

    # Banda CI rotacion
    fig.add_trace(go.Scatter(
        x=x_labels + x_labels[::-1],
        y=rot_p75 + rot_p25[::-1],
        fill="toself",
        fillcolor="rgba(42, 157, 143, 0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(
        x=x_labels, y=rot_mean,
        mode="lines+markers",
        name="Con rotacion",
        line=dict(color="#2A9D8F", width=2.5),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Fatiga: %{y:.3f}<extra>Con rotacion</extra>",
    ))

    # Marcas de descanso
    if rest_markers:
        fig.add_trace(go.Scatter(
            x=[x_labels[i] for i in rest_markers],
            y=[rot_mean[i] for i in rest_markers],
            mode="markers",
            name="Descanso",
            marker=dict(symbol="x", size=14, color="#2A9D8F", line=dict(width=2)),
            hovertemplate="<b>Descanso</b><br>%{x}<br>Fatiga: %{y:.3f}<extra></extra>",
        ))

    fig.update_layout(
        yaxis_title="Indice de Fatiga",
        yaxis_range=[-0.05, 1.05],
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


def rotation_risk_comparison(peak_baseline: float, peak_rotated: float, reduction_pct: float) -> go.Figure:
    """Comparativa de pico de fatiga con/sin rotacion."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Sin rotacion", "Con rotacion"],
        y=[peak_baseline, peak_rotated],
        marker_color=["#E63946", "#2A9D8F"],
        text=[f"{peak_baseline:.3f}", f"{peak_rotated:.3f}"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Pico fatiga: %{y:.3f}<extra></extra>",
    ))

    fig.add_annotation(
        x=1, y=peak_rotated,
        text=f"Reduccion: {reduction_pct:.1f}%",
        showarrow=False,
        font=dict(size=12, color="#2A9D8F"),
        yshift=35,
    )

    fig.update_layout(
        yaxis_title="Pico de Fatiga (P50)",
        yaxis_range=[0, max(peak_baseline, peak_rotated) * 1.3],
        height=350,
    )
    return _apply_template(fig)


def cumulative_load_projection(baseline_curve: list, rotated_curve: list, load_mean: float) -> go.Figure:
    """Area chart de carga acumulada proyectada."""
    x_labels = [p["label"] for p in baseline_curve]

    # Estimar carga acumulada
    base_load = []
    rot_load = []
    cum_base = 0
    cum_rot = 0

    for i, (bp, rp) in enumerate(zip(baseline_curve, rotated_curve)):
        if i == 0:
            base_load.append(0)
            rot_load.append(0)
            continue
        cum_base += load_mean
        cum_rot += 0 if rp.get("is_rest") else load_mean
        base_load.append(cum_base)
        rot_load.append(cum_rot)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_labels, y=base_load,
        mode="lines+markers",
        fill="tozeroy",
        name="Sin rotacion",
        line=dict(color="#E63946", width=2),
        fillcolor="rgba(230, 57, 70, 0.15)",
        hovertemplate="<b>%{x}</b><br>Carga: %{y:,.0f}m<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=x_labels, y=rot_load,
        mode="lines+markers",
        fill="tozeroy",
        name="Con rotacion",
        line=dict(color="#2A9D8F", width=2),
        fillcolor="rgba(42, 157, 143, 0.15)",
        hovertemplate="<b>%{x}</b><br>Carga: %{y:,.0f}m<extra></extra>",
    ))

    fig.update_layout(
        yaxis_title="Carga acumulada proyectada (m)",
        height=350,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Escenario 4: Formacion alternativa
# ---------------------------------------------------------------------------

# Posiciones tipicas en coordenadas de campo normalizado (0-105 x 0-68)
_FORMATION_POSITIONS = {
    "4-3-3": {
        "GK": [(5, 34)],
        "CB": [(25, 22), (25, 46)],
        "FB": [(30, 8), (30, 60)],
        "DM": [(42, 34)],
        "WM": [(52, 22), (52, 46)],
        "W": [(72, 10), (72, 58)],
        "CF": [(80, 34)],
    },
    "4-4-2": {
        "GK": [(5, 34)],
        "CB": [(25, 22), (25, 46)],
        "FB": [(30, 8), (30, 60)],
        "WM": [(50, 12), (50, 56)],
        "DM": [(48, 28), (48, 40)],
        "CF": [(78, 24), (78, 44)],
    },
    "3-5-2": {
        "GK": [(5, 34)],
        "CB": [(22, 16), (22, 34), (22, 52)],
        "WM": [(45, 6), (45, 62)],
        "DM": [(42, 26), (42, 42)],
        "AM": [(60, 34)],
        "CF": [(78, 24), (78, 44)],
    },
    "3-4-3": {
        "GK": [(5, 34)],
        "CB": [(22, 16), (22, 34), (22, 52)],
        "WM": [(45, 8), (45, 60)],
        "DM": [(42, 26), (42, 42)],
        "W": [(75, 10), (75, 58)],
        "CF": [(80, 34)],
    },
}


def formation_pitch_diagram(lineup: list[dict], formation: str, title: str = "") -> go.Figure:
    """Diagrama de cancha con jugadores posicionados."""
    from dashboard.components.pitch import draw_pitch

    fig = draw_pitch()

    pos_coords = _FORMATION_POSITIONS.get(formation, {})
    pos_counters: dict = {}

    for p in lineup:
        profile = p["position"]
        if profile not in pos_counters:
            pos_counters[profile] = 0

        coords_list = pos_coords.get(profile, [(52.5, 34)])
        idx = pos_counters[profile] % len(coords_list)
        x, y = coords_list[idx]
        pos_counters[profile] += 1

        color = PROFILE_COLORS.get(profile, SEVILLA_RED)
        name = p["player_name"]
        score = p.get("composite_score", 0)

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(size=22, color=color, opacity=0.9,
                        line=dict(width=2, color="white")),
            text=[name.split()[-1] if not name.startswith("(") else "?"],
            textposition="top center",
            textfont=dict(size=9, color="white"),
            showlegend=False,
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Posicion: {profile}<br>"
                f"Score: {score:.3f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(text=title or formation, font=dict(size=14)),
        height=420,
    )
    return fig


def formation_comparison_radar(metrics_a: dict, metrics_b: dict, name_a: str, name_b: str) -> go.Figure:
    """Radar D1-D6 medias de equipo por formacion."""
    dim_cols = [c for c in DIM_LABELS.keys() if c in metrics_a.get("team_metrics", {})]
    categories = [DIM_LABELS.get(d, d) for d in dim_cols]

    if not categories:
        fig = go.Figure()
        fig.add_annotation(text="Sin metricas comparables", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_template(fig)

    vals_a = [metrics_a["team_metrics"][d]["mean"] for d in dim_cols]
    vals_b = [metrics_b["team_metrics"][d]["mean"] for d in dim_cols]

    vals_a_closed = vals_a + [vals_a[0]]
    vals_b_closed = vals_b + [vals_b[0]]
    cats_closed = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=vals_a_closed, theta=cats_closed,
        fill="toself", opacity=0.3,
        name=name_a,
        line=dict(color="#E63946", width=2),
        hovertemplate="%{theta}: %{r:.3f}<extra></extra>",
    ))

    fig.add_trace(go.Scatterpolar(
        r=vals_b_closed, theta=cats_closed,
        fill="toself", opacity=0.3,
        name=name_b,
        line=dict(color="#2A9D8F", width=2),
        hovertemplate="%{theta}: %{r:.3f}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5),
        margin=dict(t=20, b=80, l=60, r=60),
    )
    return _apply_template(fig)


def formation_comparison_bar(comparison: dict, name_a: str, name_b: str) -> go.Figure:
    """Barras agrupadas: formacion A vs B con diferencias."""
    dim_labels_ext = {**DIM_LABELS, "composite_mean": "Score Compuesto"}
    metrics = sorted(comparison.keys())
    names = [dim_labels_ext.get(m, m) for m in metrics]

    vals_a = [comparison[m]["formation_a"] for m in metrics]
    vals_b = [comparison[m]["formation_b"] for m in metrics]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=name_a, x=names, y=vals_a,
        marker_color="#E63946",
        hovertemplate="<b>%{x}</b><br>%{y:.3f}<extra>" + name_a + "</extra>",
    ))

    fig.add_trace(go.Bar(
        name=name_b, x=names, y=vals_b,
        marker_color="#2A9D8F",
        hovertemplate="<b>%{x}</b><br>%{y:.3f}<extra>" + name_b + "</extra>",
    ))

    fig.update_layout(
        barmode="group",
        yaxis_title="Score medio equipo",
        yaxis_range=[0, 1],
        height=450,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
    )
    return _apply_template(fig)
