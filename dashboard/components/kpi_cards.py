"""Tarjetas KPI reutilizables."""

import streamlit as st


def render_kpi_row(metrics: list[dict]):
    """Renderiza una fila de KPI cards.

    Cada dict: {"label": str, "value": str|number, "delta": str|None}
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
            )
