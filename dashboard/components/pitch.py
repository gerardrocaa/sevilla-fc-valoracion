"""Diagrama 2D de campo para heatmaps posicionales."""

import numpy as np
from scipy.ndimage import gaussian_filter
import plotly.graph_objects as go

from dashboard.config import PLOTLY_TEMPLATE, SEVILLA_RED


def draw_pitch() -> go.Figure:
    """Dibuja un campo de futbol 2D (105x68m) con lineas."""
    fig = go.Figure()

    # Campo (fondo verde)
    fig.add_shape(type="rect", x0=0, y0=0, x1=105, y1=68,
                  line=dict(color="white", width=2), fillcolor="#4a8c3f",
                  layer="below")

    # Linea central
    fig.add_shape(type="line", x0=52.5, y0=0, x1=52.5, y1=68,
                  line=dict(color="white", width=1.5), layer="below")

    # Circulo central
    fig.add_shape(type="circle", x0=52.5 - 9.15, y0=34 - 9.15,
                  x1=52.5 + 9.15, y1=34 + 9.15,
                  line=dict(color="white", width=1.5), layer="below")

    # Punto central
    fig.add_trace(go.Scatter(
        x=[52.5], y=[34], mode="markers",
        marker=dict(size=4, color="white"),
        showlegend=False, hoverinfo="skip",
    ))

    # Area de penalty izquierda
    fig.add_shape(type="rect", x0=0, y0=13.84, x1=16.5, y1=54.16,
                  line=dict(color="white", width=1.5), layer="below")
    # Area de penalty derecha
    fig.add_shape(type="rect", x0=88.5, y0=13.84, x1=105, y1=54.16,
                  line=dict(color="white", width=1.5), layer="below")

    # Area pequena izquierda
    fig.add_shape(type="rect", x0=0, y0=24.84, x1=5.5, y1=43.16,
                  line=dict(color="white", width=1.5), layer="below")
    # Area pequena derecha
    fig.add_shape(type="rect", x0=99.5, y0=24.84, x1=105, y1=43.16,
                  line=dict(color="white", width=1.5), layer="below")

    # Porterias
    fig.add_shape(type="rect", x0=-1.5, y0=30.34, x1=0, y1=37.66,
                  line=dict(color="white", width=1.5), layer="below")
    fig.add_shape(type="rect", x0=105, y0=30.34, x1=106.5, y1=37.66,
                  line=dict(color="white", width=1.5), layer="below")

    fig.update_layout(
        xaxis=dict(range=[-4, 109], showgrid=False, zeroline=False,
                   showticklabels=False, constrain="domain", fixedrange=True),
        yaxis=dict(range=[-4, 72], showgrid=False, zeroline=False,
                   showticklabels=False, scaleanchor="x", scaleratio=1, fixedrange=True),
        dragmode=False,
        height=480,
        margin=dict(l=5, r=5, t=40, b=5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=PLOTLY_TEMPLATE["layout"]["font"],
        hoverlabel=PLOTLY_TEMPLATE["layout"]["hoverlabel"],
    )
    return fig


def _to_pitch_coords(x_vals, y_vals):
    """Convert SkillCorner centered coordinates to pitch [0,105]x[0,68]."""
    return x_vals + 52.5, y_vals + 34.0


def pitch_heatmap(events, x_col="x_start", y_col="y_start", title="Heatmap Posicional"):
    """Genera un heatmap de densidad sobre el campo."""
    fig = draw_pitch()

    x_raw = events[x_col].dropna().values.astype(float)
    y_raw = events[y_col].dropna().values.astype(float)

    if len(x_raw) == 0:
        fig.update_layout(title=title + " (sin datos)")
        return fig

    # SkillCorner: centered at 0 -> shift to pitch coords
    if x_raw.min() < -1:
        x_vals, y_vals = _to_pitch_coords(x_raw, y_raw)
    elif x_raw.max() <= 1.5:
        x_vals = x_raw * 105
        y_vals = y_raw * 68
    else:
        x_vals, y_vals = x_raw, y_raw

    x_vals = np.clip(x_vals, 0, 105)
    y_vals = np.clip(y_vals, 0, 68)

    # Compute density grid (bins stay within pitch bounds)
    nx, ny = 50, 34
    density, xedges, yedges = np.histogram2d(
        x_vals, y_vals, bins=[nx, ny],
        range=[[0, 105], [0, 68]],
    )
    # Smooth with Gaussian filter
    density = gaussian_filter(density, sigma=2.5)
    # Transpose: histogram2d returns (nx, ny), Heatmap expects (ny, nx)
    density = density.T

    # Mask zero-density cells as transparent
    density_masked = np.where(density < density.max() * 0.02, np.nan, density)

    # Bin centers
    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2

    fig.add_trace(go.Heatmap(
        x=x_centers, y=y_centers, z=density_masked,
        colorscale=[
            [0, "rgba(255,255,0,0.5)"],
            [0.3, "rgba(255,200,0,0.7)"],
            [0.55, "rgba(255,140,0,0.8)"],
            [0.8, "rgba(230,50,20,0.9)"],
            [1, "rgba(150,0,10,0.95)"],
        ],
        showscale=False,
        hovertemplate="x: %{x:.1f}m<br>y: %{y:.1f}m<br>densidad: %{z:.1f}<extra></extra>",
        zsmooth="best",
    ))

    fig.update_layout(title=title)
    return fig
