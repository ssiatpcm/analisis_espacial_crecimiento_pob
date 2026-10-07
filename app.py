"""
app.py — Punto de entrada · SSIAT / SDOT-PCM
Define la navegación y los nombres del menú lateral.
"""
import streamlit as st

pg = st.navigation(
    [
        st.Page(
            "pages/00_pagina_principal.py",
            title="Página principal",
            icon="🗺️",
        ),
        st.Page(
            "pages/01_resumen_ejecutivo.py",
            title="Resumen ejecutivo",
            icon="📊",
        ),
        st.Page(
            "pages/02_analisis_distrital_capital.py",
            title="Análisis distrital y capital",
            icon="📍",
        ),
        st.Page(
            "pages/03_brechas_normativas.py",
            title="Brechas normativas",
            icon="⚖️",
        ),
        st.Page(
            "pages/04_creaciones_en_riesgo.py",
            title="Creaciones en riesgo",
            icon="🚨",
        ),
    ],
    position="sidebar",
)

pg.run()
