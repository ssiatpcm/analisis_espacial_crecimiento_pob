"""
app.py — Punto de entrada del Tablero de Análisis Espacial de Crecimiento Poblacional
SSIAT / SDOT-PCM · 2026
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Crecimiento Poblacional · SSIAT",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    :root {
        --azul-sdot: #2E75B6;
        --azul-oscuro: #1B4D5C;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    .main-header {
        background: linear-gradient(90deg, #1B4D5C 0%, #2E75B6 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.4rem; }
    .main-header p  { color: #d0e8f5; margin: 0.25rem 0 0; font-size: 0.85rem; }
    [data-testid="stMetric"] {
        background-color: #f0f4f8;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border-left: 3px solid #2E75B6;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🗺️ Análisis Espacial de Crecimiento Poblacional en el Perú</h1>
        <p>Subsecretaría de Información y Análisis Territorial · SDOT / PCM · 2026</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### Acerca del tablero

    Dashboard interactivo para el análisis espacial del crecimiento y decrecimiento
    poblacional en el Perú a escala distrital y de centros poblados (CCPP),
    basado en los censos INEI 2007 y 2017 y las proyecciones al 2024.

    Los resultados se vinculan al marco normativo de demarcación territorial
    (Ley N.° 27795 · TUO DS 134-2025-PCM, Art. 14).

    **Navega a través del menú lateral para acceder a cada módulo.**
    """)

with col2:
    st.markdown("### Módulos")
    modulos = [
        ("📊", "P1 · Resumen ejecutivo",    "KPIs globales y alertas normativas"),
        ("🗺️", "P2 · Análisis distrital",   "Mapa LISA, TCM y ranking"),
        ("📍", "P3 · Centros poblados",      "CCPP, IDW e indicador capital"),
        ("⚖️", "P4 · Brechas normativas",   "Semáforo Art. 14 TUO"),
        ("🚨", "P5 · Creaciones en riesgo", "Post-2002 con decrecimiento"),
        ("🔭", "P6 · Proyecciones 2030",    "Escenarios tendencial/opt./pesim."),
    ]
    for icono, nombre, desc in modulos:
        st.markdown(f"**{icono} {nombre}**  \n_{desc}_")
        st.divider()

st.markdown("---")
st.caption("Fuentes: INEI Censos 2007, 2017 · Proyecciones INEI 2024 · SSIAT · SDOT-PCM · 2026")
