"""Sevilla FC - Dashboard de Valoracion Integral de Jugadores.

Entry point: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure the project root (parent of dashboard/) is on sys.path
# so that `from dashboard.xxx import yyy` works in all pages.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

st.set_page_config(
    page_title="Sevilla FC - Valoración Integral",
    page_icon="SFC",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# Navigation
pages = {
    "Vista General": [st.Page("pages/1_Vista_General.py", title="Vista General", default=True)],
    "Analisis": [
        st.Page("pages/2_Perfil_Individual.py", title="Perfil Individual"),
        st.Page("pages/3_Comparativa.py", title="Comparativa"),
    ],
    "Datos": [
        st.Page("pages/4_Datos_Fisicos.py", title="Datos Físicos"),
        st.Page("pages/5_Explorador_Eventos.py", title="Explorador Eventos"),
    ],
    "Inferencia": [
        st.Page("pages/6_Clustering.py", title="Clustering"),
        st.Page("pages/7_Fatiga_Riesgo.py", title="Fatiga y Riesgo"),
        st.Page("pages/8_Patrones_Ocultos.py", title="Patrones Ocultos"),
    ],
    "Simulacion": [
        st.Page("pages/9_Escenarios_What_If.py", title="Escenarios What-If"),
    ],
    "Valoracion": [
        st.Page("pages/10_Valoracion_Integral.py", title="Valoración Integral"),
    ],
}

pg = st.navigation(pages)
pg.run()
