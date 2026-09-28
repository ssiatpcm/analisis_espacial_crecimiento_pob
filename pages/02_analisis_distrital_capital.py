"""
pages/02_analisis_distrital_capital.py
Página 2 — Análisis territorial: Distrito y Capital Distrital
Tablero de Análisis Espacial de Crecimiento Poblacional · SSIAT / SDOT-PCM
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.carga_datos import cargar_dataframe, cargar_capitales

# ── Configuración ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Distrito y Capital · SSIAT",
    page_icon="📍",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #f0f4f8; }
.header-banner {
    background: linear-gradient(90deg, #1B4D5C 0%, #2E75B6 100%);
    color: white; padding: 1rem 1.5rem;
    border-radius: 8px; margin-bottom: 1rem;
}
.header-banner h2 { color: white; margin: 0; font-size: 1.2rem; }
.header-banner p  { color: #d0e8f5; margin: .2rem 0 0; font-size: .8rem; }
.kpi-box { background:#f8fafc; border-radius:10px; padding:.9rem 1rem; margin-bottom:.5rem; }
.kpi-box.blue  { border-left:4px solid #2E75B6; }
.kpi-box.green { border-left:4px solid #10B981; }
.kpi-box.red   { border-left:4px solid #EF4444; }
.kpi-box.amber { border-left:4px solid #F59E0B; }
.kpi-box.purple{ border-left:4px solid #8B5CF6; }
.kpi-label { font-size:.78rem; color:#64748b; margin-bottom:.15rem; }
.kpi-value { font-size:1.7rem; font-weight:700; line-height:1.1; }
.kpi-sub   { font-size:.76rem; color:#94a3b8; margin-top:.2rem; }
.sem-row {
    display:flex; align-items:flex-start; gap:8px;
    padding:7px 9px; border-radius:7px; margin-bottom:5px;
    font-size:.82rem; background:#f8fafc;
}
.section-title {
    font-size:.72rem; font-weight:600; letter-spacing:.06em;
    text-transform:uppercase; color:#94a3b8; margin-bottom:.6rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
df_dist = cargar_dataframe()
df_cap  = cargar_capitales()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — filtros
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Filtros")

    periodo = st.radio("Período de análisis",
                       ["2007 – 2017", "2017 – 2025"], index=0)
    usar_0717    = periodo == "2007 – 2017"
    col_tcm_dist = "TC_07_17"    if usar_0717 else "TC_17_25"
    col_tcm_cap  = "TASA_0717"   if usar_0717 else "TASA_1725"
    col_dinamica = "DINAMICA_0717" if usar_0717 else "DINAMICA_1725"

    regiones   = ["Todas"] + sorted(df_cap["REGION_NAT"].dropna().unique().tolist())
    region_sel = st.selectbox("Región natural", regiones)

    tipo_dist = st.selectbox(
        "Tipo de distrito",
        ["Todos", "Solo creaciones (post-2002)", "Solo origen"],
    )
    st.markdown("---")
    st.caption("Fuentes: INEI 2007, 2017 · Proy. 2025 · SSIAT 2026")

# Aplicar filtros
dff = df_cap.copy()
if region_sel != "Todas":
    dff = dff[dff["REGION_NAT"] == region_sel]
if tipo_dist == "Solo creaciones (post-2002)":
    dff = dff[dff["ANIO"].notna()]
elif tipo_dist == "Solo origen":
    dff = dff[dff["ANIO"].isna()]


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>📍 Análisis territorial — Distrito y Capital Distrital</h2>
  <p>Período: <b>{periodo}</b> &nbsp;·&nbsp;
     Región: <b>{region_sel}</b> &nbsp;·&nbsp;
     Capitales analizadas: <b>{len(dff):,}</b> &nbsp;·&nbsp;
     SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
total        = len(dff)
total_kpi    = 1874 if usar_0717 else 1892
n_cap_crec   = int((dff[col_tcm_cap] > 0).sum())
n_cap_decrec = int((dff[col_tcm_cap] < 0).sum())
n_doble_cap  = int(((dff["TASA_0717"] < 0) & (dff["TASA_1725"] < 0)).sum())
n_suburban   = int((dff[col_dinamica] == "Capital crece / Distrito decrece").sum())

k1, k2, k3, k4, k5 = st.columns(5)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",   "🗺️ Distritos / capitales", f"{total_kpi:,}",
     "Base INEI 2017" if usar_0717 else "Base INEI 2025", "#1E40AF"),
    (k2, "green",  "📈 Capitales que crecen",  f"{n_cap_crec:,}",
     f"{n_cap_crec/total*100:.1f}% del total", "#166534"),
    (k3, "red",    "📉 Capitales que decrecen", f"{n_cap_decrec:,}",
     f"{n_cap_decrec/total*100:.1f}% del total", "#991B1B"),
    (k4, "amber",  "⚠️ Doble decrecimiento",   f"{n_doble_cap:,}",
     "Capital y distrito decrecen", "#92400E"),
    (k5, "purple", "🏘️ Suburbanización",        f"{n_suburban:,}",
     "Capital crece / Distrito decrece", "#5B21B6"),
]:
    with col_st:
        st.markdown(f"""
        <div class="kpi-box {cls}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value" style="color:{color}">{valor}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 2 — Dinámica + Mapa
# ══════════════════════════════════════════════════════════════════════════════
col_izq, col_mapa = st.columns([1, 1.6])

# ── Dinámica capital vs. distrito ──────────────────────────────────────────
with col_izq:
    st.markdown('<div class="section-title">Dinámica capital vs. distrito</div>',
                unsafe_allow_html=True)

    COLORES_DIN = {
        "Ambos crecen":                       ("#10B981", "#166534"),
        "Capital crece / Distrito decrece":   ("#8B5CF6", "#5B21B6"),
        "Capital decrece / Distrito crece":   ("#F59E0B", "#92400E"),
        "Ambos decrecen":                     ("#EF4444", "#991B1B"),
        "Sin datos":                          ("#94A3B8", "#475569"),
    }
    DESCRIP_DIN = {
        "Ambos crecen":                     "Expansión territorial · Costa y Selva Baja",
        "Capital crece / Distrito decrece": "Suburbanización: vaciamiento rural hacia capital",
        "Capital decrece / Distrito crece": "Descapitalización: crecimiento fuera del centro",
        "Ambos decrecen":                   "Abandono territorial · Sierra persistente",
        "Sin datos":                        "Sin información censal suficiente",
    }

    counts = dff[col_dinamica].value_counts()
    for din, (color_dot, color_txt) in COLORES_DIN.items():
        n = counts.get(din, 0)
        if n == 0:
            continue
        pct = n / total * 100
        st.markdown(f"""
        <div class="sem-row">
          <div style="width:10px;height:10px;border-radius:50%;background:{color_dot};
                      flex-shrink:0;margin-top:3px"></div>
          <div>
            <span style="font-weight:500;font-size:.83rem">{din}</span>
            <span style="color:#64748b;font-size:.83rem"> — {n:,} ({pct:.1f}%)</span><br>
            <span style="font-size:.72rem;color:#94a3b8">{DESCRIP_DIN[din]}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">% "Ambos decrecen" por región natural</div>',
                unsafe_allow_html=True)

    reg_dd = df_cap[df_cap[col_dinamica] == "Ambos decrecen"].groupby(
        "REGION_NAT").size()
    reg_tot = df_cap.groupby("REGION_NAT").size()
    reg_pct = (reg_dd / reg_tot * 100).fillna(0).sort_values()

    COLOR_REG = {
        "COSTA": "#2563EB", "SELVA BAJA": "#10B981",
        "SELVA ALTA": "#F59E0B", "SIERRA": "#EF4444",
    }
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Bar(
        y=reg_pct.index.tolist(),
        x=reg_pct.values,
        orientation="h",
        marker_color=[COLOR_REG.get(r, "#94A3B8") for r in reg_pct.index],
        text=[f"{v:.0f}%" for v in reg_pct.values],
        textposition="outside",
        textfont_size=10,
    ))
    fig_reg.update_layout(
        height=160, margin=dict(t=5, b=5, l=10, r=40),
        xaxis=dict(range=[0, 70], gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_reg, use_container_width=True)


# ── Mapa de capitales ───────────────────────────────────────────────────────
with col_mapa:
    st.markdown('<div class="section-title">Mapa de capitales</div>',
                unsafe_allow_html=True)

    tab_tcm, tab_din = st.tabs(["TCM de la capital", "Dinámica capital / distrito"])

    def color_tcm_cap(v):
        if pd.isna(v): return "#CBD5E1"
        if v >= 1.5:   return "#1D4ED8"
        if v >= 0.5:   return "#60A5FA"
        if v >= 0:     return "#BAE6FD"
        if v >= -2.5:  return "#FCA5A5"
        if v >= -5.0:  return "#EF4444"
        return "#7F1D1D"

    COLOR_DIN_MAP = {
        "Ambos crecen":                     "#10B981",
        "Capital crece / Distrito decrece": "#8B5CF6",
        "Capital decrece / Distrito crece": "#F59E0B",
        "Ambos decrecen":                   "#EF4444",
        "Sin datos":                        "#CBD5E1",
    }

    def make_map(dff_map, mode="tcm"):
        m = folium.Map(
            location=[-9.5, -75.5], zoom_start=5,
            tiles=None, prefer_canvas=True,
        )
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">'
                 'OpenStreetMap</a> contributors',
            name="OpenStreetMap", max_zoom=19,
        ).add_to(m)

        # Tamaño proporcional a la población (radio 3–18 px)
        pob_max = dff_map["POB2017"].replace(0, np.nan).max()

        for _, row in dff_map.iterrows():
            pob = row["POB2017"] if not pd.isna(row["POB2017"]) else 100
            radius = max(3, min(18, 3 + 15 * (pob / pob_max) ** 0.4))

            if mode == "tcm":
                color = color_tcm_cap(row[col_tcm_cap])
                col_pob_cap = "POB2017" if usar_0717 else "POB2025"
                label_pob_cap = "Pob. 2017" if usar_0717 else "Pob. 2025"
                _val = row.get(col_pob_cap)
                pob_mostrar = pob if (_val is None or pd.isna(_val) or _val == 0) else _val
                tooltip_txt = (
                    f"<b>{row['NOMBCCPP']}</b><br>"
                    f"{row['NOMBDIST']} — {row['NOMBDEP']}<br>"
                    f"TCM capital ({periodo}): <b>{row[col_tcm_cap]:.2f}%</b><br>"
                    f"{label_pob_cap}: {int(pob_mostrar):,}<br>"
                    f"Región: {row.get('REGION_NAT','')}"
                )
            else:
                din = row.get(col_dinamica, "Sin datos")
                color = COLOR_DIN_MAP.get(din, "#CBD5E1")

                tooltip_txt = (
                    f"<b>{row['NOMBCCPP']}</b><br>"
                    f"{row['NOMBDIST']} — {row['NOMBDEP']}<br>"
                    f"Dinámica: <b>{din}</b><br>"
                    f"TCM capital: {row[col_tcm_cap]:.2f}% &nbsp;|&nbsp; "
                    f"TCM distrito: {row[col_tcm_dist]:.2f}%<br>"
                    f"Pob. 2017: {int(pob):,}"
                )

            folium.CircleMarker(
                location=[row["Y"], row["X"]],
                radius=radius,
                color="#ffffff",
                weight=0.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                tooltip=folium.Tooltip(tooltip_txt, sticky=False),
            ).add_to(m)

        return m

    with tab_tcm:
        m_tcm = make_map(dff, mode="tcm")
        legend_tcm = """
        <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                    background:white;padding:7px 11px;border-radius:7px;
                    border:1px solid #e2e8f0;font-size:10px;
                    box-shadow:0 2px 5px rgba(0,0,0,.12)">
          <b>TCM capital (%)</b><br>
          <span style="color:#1D4ED8">●</span> ≥ 1.5 &nbsp;
          <span style="color:#60A5FA">●</span> 0.5–1.5 &nbsp;
          <span style="color:#BAE6FD">●</span> 0–0.5<br>
          <span style="color:#FCA5A5">●</span> −2.5–0 &nbsp;
          <span style="color:#EF4444">●</span> −5–−2.5 &nbsp;
          <span style="color:#7F1D1D">●</span> &lt;−5<br>
          <span style="color:#CBD5E1">●</span> Sin datos &nbsp;·&nbsp;
          <i>Tamaño ∝ Pob. 2017</i>
        </div>"""
        m_tcm.get_root().html.add_child(folium.Element(legend_tcm))
        st_folium(m_tcm, width=None, height=420, returned_objects=[])

    with tab_din:
        m_din = make_map(dff, mode="din")
        legend_din = """
        <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                    background:white;padding:7px 11px;border-radius:7px;
                    border:1px solid #e2e8f0;font-size:10px;
                    box-shadow:0 2px 5px rgba(0,0,0,.12)">
          <b>Dinámica capital/distrito</b><br>
          <span style="color:#10B981">●</span> Ambos crecen<br>
          <span style="color:#8B5CF6">●</span> Capital crece / Distrito decrece<br>
          <span style="color:#F59E0B">●</span> Capital decrece / Distrito crece<br>
          <span style="color:#EF4444">●</span> Ambos decrecen<br>
          <span style="color:#CBD5E1">●</span> Sin datos &nbsp;·&nbsp;
          <i>Tamaño ∝ Pob. 2017</i>
        </div>"""
        m_din.get_root().html.add_child(folium.Element(legend_din))
        st_folium(m_din, width=None, height=420, returned_objects=[])


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Distribución por tamaño + Tabla
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_hist, col_tabla = st.columns([1, 1.4])

# ── Distribución por tamaño de capital ────────────────────────────────────
with col_hist:
    st.markdown('<div class="section-title">Capitales por tamaño de población (2017)</div>',
                unsafe_allow_html=True)

    from utils.carga_datos import LABELS_POB
    dist_rango = dff["RANGO_POB"].value_counts().reindex(LABELS_POB, fill_value=0)
    total_rango = dist_rango.sum()

    fig_hist = go.Figure(go.Bar(
        y=dist_rango.index.tolist(),
        x=dist_rango.values,
        orientation="h",
        marker_color="#2E75B6",
        text=[f"{v:,}  ({v/total_rango*100:.0f}%)" for v in dist_rango.values],
        textposition="outside",
        textfont_size=10,
    ))
    fig_hist.update_layout(
        height=290,
        margin=dict(t=10, b=10, l=10, r=90),
        xaxis=dict(title="N.° de capitales", gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10, autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    pct_pequenas = (dist_rango["< 500"] + dist_rango["500–2k"]) / total_rango * 100
    st.caption(
        f"El **{pct_pequenas:.0f}%** de las capitales tiene menos de 2,000 hab. "
        "— relevante para umbrales Art. 14 TUO DS 134-2025-PCM."
    )


# ── Tabla integrada ─────────────────────────────────────────────────────────
with col_tabla:
    st.markdown('<div class="section-title">Tabla integrada — distrito y capital</div>',
                unsafe_allow_html=True)

    # Filtro rápido por dinámica
    opciones_din = ["Todas"] + [
        "Ambos crecen",
        "Capital crece / Distrito decrece",
        "Capital decrece / Distrito crece",
        "Ambos decrecen",
    ]
    din_sel = st.selectbox("Filtrar por dinámica", opciones_din,
                           label_visibility="collapsed")

    busqueda = st.text_input("🔍 Buscar por nombre de distrito o ubigeo", "",
                             label_visibility="collapsed",
                             placeholder="🔍 Buscar por nombre de distrito o ubigeo")

    tabla = dff[[
        "UBIGEO", "NOMBDIST", "NOMBDEP", "REGION_NAT", "TIPOLOGIA",
        col_tcm_dist, col_tcm_cap, "POB2017", "POB2025", col_dinamica, "RANGO_POB",
    ]].rename(columns={
        "NOMBDIST":    "Distrito",
        "NOMBDEP":     "Dpto.",
        "REGION_NAT":  "Región",
        "TIPOLOGIA":   "Tipología",
        col_tcm_dist:  "TCM distrito (%)",
        col_tcm_cap:   "TCM capital (%)",
        "POB2017":     "Pob. cap. 2017",
        "POB2025":     "Pob. cap. 2025",
        col_dinamica:  "Dinámica",
        "RANGO_POB":   "Tamaño capital",
    })

    if din_sel != "Todas":
        tabla = tabla[tabla["Dinámica"] == din_sel]

    if busqueda:
        mask = (
            tabla["Distrito"].str.contains(busqueda.upper(), na=False) |
            tabla["UBIGEO"].astype(str).str.contains(busqueda, na=False)
        )
        tabla = tabla[mask]

    st.dataframe(
        tabla.sort_values("TCM distrito (%)"),
        use_container_width=True,
        height=290,
        hide_index=True,
    )

    csv = tabla.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Descargar tabla (CSV)",
        data=csv,
        file_name=f"distrito_capital_{periodo.replace(' ','').replace('–','_')}.csv",
        mime="text/csv",
    )


# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuentes: INEI Censos 2007, 2017, 2025 · Proy. 2025 · "
    "· SSIAT · 2026"
)
