"""
app.py — Punto de entrada · SSIAT / SDOT-PCM
Análisis Espacial del Crecimiento Poblacional en el Perú
"""
import streamlit as st

st.set_page_config(
    page_title="Crecimiento Poblacional · SSIAT",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #f0f4f8; }
.main-header {
    background: linear-gradient(90deg, #1B4D5C 0%, #2E75B6 100%);
    color: white; padding: 1rem 1.5rem;
    border-radius: 8px; margin-bottom: 1.5rem;
}
.main-header h1 { color: white; margin: 0; font-size: 1.35rem; }
.main-header p  { color: #d0e8f5; margin: .25rem 0 0; font-size: .82rem; }
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
    Dashboard interactivo para el análisis del crecimiento y decrecimiento
    poblacional en el Perú a escala distrital y centro poblado, basado en los censos nacionales del INEI
    2007, 2017 y 2025, y proyecciones al 2025.

    Los resultados se vinculan al marco normativo de demarcación territorial
    (Ley N.° 27795 · TUO D.S. 134-2025-PCM).

    **👈 Selecciona una página en el menú lateral.**
    """)
with col2:
    st.markdown("### Módulos")
    for ico, nom, desc in [
        ("📊", "P1 · Resumen ejecutivo",    "KPIs, mapa TCM y alertas"),
        ("🗺️", "P2 · Análisis distrital",   "LISA/Moran y ranking"),
        ("📍", "P3 · Centros poblados",      "CCPP e IDW"),
        ("⚖️", "P4 · Brechas normativas",   "Art. 14 TUO — semáforo"),
        ("🚨", "P5 · Creaciones en riesgo", "Post-2002 con decrecimiento"),
        ("🔭", "P6 · Proyecciones 2030",    "Escenarios prospectivos"),
    ]:
        st.markdown(f"**{ico} {nom}**  \n_{desc}_")
        st.divider()

st.caption(
    "INEI Censos 2007, 2017 y 2025 · Proyecciones 2025 · SSIAT · SDOT-PCM · 2026"
)
