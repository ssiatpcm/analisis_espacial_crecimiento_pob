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
  <p>Subsecretaría de Información y Análisis Territorial (SSIAT) · SDOT / PCM · 2026</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
    ### Acerca del tablero
    Tablero interactivo para el análisis del crecimiento y decrecimiento
    poblacional en el Perú a escala distrital y centro poblado, basado en los tres últimos censos nacionales del INEI
    2007, 2017 y 2025.

    Los resultados se vinculan a lo establecido en la Ley N° 27795, Ley de Demarcación Territorial y su Reglamento 
    aprobado por D.S. 134-2025-PCM, que aprueba el Texto Único Ordenado (TUO) del Reglamento de la Ley N° 27795, aprobado por D.S. N° 191-2020-PCM.
    Este marco normativo establece los criterios técnicos para la evaluación de las acciones de demarcación territorial que son competencia de 
    la Secretaría de Demarcación y Organización Territorial (SDOT) y los Gobiernos Regionales (GORE).

    **👈 Selecciona una página en el menú lateral.**
    """)
with col2:
    st.markdown("### Módulos")
    for ico, nom, desc in [
        ("📊", "P1 · Resumen ejecutivo",    "KPIs, mapa TCM y alertas"),
        ("🗺️", "P2 · Análisis distrito y capitales",   "TCM capital y Dinámica capital/distrito"),
        ("⚖️", "P3 · Brechas normativas",   "Tabla N° 1 y N° 2 del reglamento"),
        ("🚨", "P4 · Creaciones en riesgo", "Post-2002 con crecimiento/decrecimiento")
    ]:
        st.markdown(f"**{ico} {nom}**  \n_{desc}_")
        st.divider()

st.caption(
    "INEI Censos 2007, 2017 y 2025 · SSIAT · SDOT-PCM · 2026"
)
