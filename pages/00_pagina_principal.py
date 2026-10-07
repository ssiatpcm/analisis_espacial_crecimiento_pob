"""
pages/00_pagina_principal.py
Página principal del tablero · SSIAT / SDOT-PCM
Análisis Espacial de Crecimiento Poblacional en el Perú
"""
import streamlit as st

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
.mod-card {
    background: #f8fafc; border-radius: 8px; padding: .7rem 1rem;
    margin-bottom: .5rem; border-left: 3px solid #2E75B6;
}
.mod-card span { font-size: .78rem; color: #64748b; }
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
    Tablero interactivo para el análisis del crecimiento y decrecimiento
    poblacional en el Perú a escala distrital y centro poblado, basado en los tres últimos censos nacionales del INEI
    2007, 2017 y 2025.

    Los resultados se vinculan a lo establecido en la **Ley N° 27795, Ley de Demarcación Territorial** y su Reglamento 
    aprobado por D.S. 134-2025-PCM, que aprueba el Texto Único Ordenado (TUO) del Reglamento de la Ley N° 27795, aprobado por D.S. N° 191-2020-PCM.

    Este marco normativo establece los criterios técnicos para la evaluación de las acciones de demarcación territorial que son competencia de 
    la Secretaría de Demarcación y Organización Territorial (SDOT) y los Gobiernos Regionales (GORE).

    **👈 Selecciona una página en el menú lateral.**
    """)

    st.markdown("---")
    st.markdown("""
    **Fuentes de datos**
    - INEI · Censos Nacionales de Población y Vivienda 2007, 2017 y 2025
    - SDOT-PCM · Tipología de Distritos de las 1,892 circunscripciones territoriales (2025)
    """)

with col2:
    st.markdown("### Módulos del tablero")
    for ico, nom, desc in [
        ("📊", "Resumen ejecutivo",
         "KPIs nacionales, mapa TCM distrital y alertas por período"),
        ("📍", "Análisis distrital y capital",
         "Dinámica capital vs. distrito, suburbanización y despoblamiento"),
        ("⚖️", "Brechas normativas",
         "Cumplimiento del umbral mínimo poblacional · TUO DS 134-2025-PCM"),
        ("🚨", "Creaciones en riesgo",
         "Distritos post-2002 con decrecimiento · despoblamiento persistente"),
    ]:
        st.markdown(f"""
        <div class="mod-card">
          <b>{ico} {nom}</b><br>
          <span>{desc}</span>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "INEI Censos 2007, 2017 y 2025 · "
    "Elaborado por SSIAT · SDOT-PCM · 2026"
)
