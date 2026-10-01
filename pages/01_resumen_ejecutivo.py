"""
pages/01_resumen_ejecutivo.py
Página 1 — Resumen Ejecutivo
Tablero de Análisis Espacial de Crecimiento Poblacional · SSIAT / SDOT-PCM
Fuentes: shapefile total_distritos_1892.shp + distritos_crec_pob.xlsx
"""

import warnings
warnings.filterwarnings("ignore")

import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.carga_datos import cargar_dataframe, cargar_datos_integrados

# ── Configuración ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resumen Ejecutivo · SSIAT",
    page_icon="📊",
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
.kpi-label { font-size:.78rem; color:#64748b; margin-bottom:.15rem; }
.kpi-value { font-size:1.7rem; font-weight:700; line-height:1.1; }
.kpi-sub   { font-size:.76rem; color:#94a3b8; margin-top:.2rem; }
.alert-box { padding:.55rem .9rem; border-radius:7px; margin-bottom:.4rem;
             font-size:.82rem; display:flex; align-items:flex-start; gap:.5rem; }
.alert-red   { background:#FEF2F2; border:1px solid #FECACA; color:#991B1B; }
.alert-amber { background:#FFFBEB; border:1px solid #FDE68A; color:#92400E; }
.alert-green { background:#F0FDF4; border:1px solid #BBF7D0; color:#166534; }
.alert-blue  { background:#EFF6FF; border:1px solid #BFDBFE; color:#1E40AF; }
.section-title { font-size:.72rem; font-weight:600; letter-spacing:.06em;
                 text-transform:uppercase; color:#94a3b8; margin-bottom:.6rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
df  = cargar_dataframe()
gdf = cargar_datos_integrados()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — solo filtro de período
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Filtros")
    periodo = st.radio("Período de análisis",
                       ["2007 – 2017", "2017 – 2025"], index=0)
    usar_0717     = periodo == "2007 – 2017"
    col_tcm       = "TC_07_17"       if usar_0717 else "TC_17_25"
    col_tendencia = "TENDENCIA_0717" if usar_0717 else "TENDENCIA_1725"
    st.markdown("---")
    st.caption("Fuentes: INEI 2007, 2017, 2025 · SSIAT 2026")

# Sin filtros de región ni tipo — usar dataset completo
dff   = df.copy()
gdf_f = gdf.copy()


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>📊 Resumen Ejecutivo — Crecimiento Poblacional en el Perú</h2>
  <p>Período: <b>{periodo}</b> &nbsp;·&nbsp;
     Distritos: <b>{1874 if usar_0717 else 1892:,}</b> &nbsp;·&nbsp;
     SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
total     = len(dff)
total_kpi = 1874 if usar_0717 else 1892
n_crec    = int((dff[col_tcm] > 0).sum())
n_decrec  = int((dff[col_tcm] < 0).sum())
n_doble   = int(((dff["TC_07_17"] < 0) & (dff["TC_17_25"] < 0)).sum())
n_creac   = int(dff["ES_CREACION"].sum())

k1, k2, k3, k4, k5 = st.columns(5)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",  "🗺️ Distritos",
     f"{total_kpi:,}", "Base censo 2017" if usar_0717 else "Base censo 2025", "#1E40AF"),
    (k2, "green", "📈 Con crecimiento",
     f"{n_crec:,}", f"{n_crec/total*100:.1f}% del total", "#166534"),
    (k3, "red",   "📉 Con decrecimiento",
     f"{n_decrec:,}", f"{n_decrec/total*100:.1f}% del total", "#991B1B"),
    (k4, "red",   "⚠️ Doble decrec.",
     f"{n_doble:,}", "Negativa en ambos períodos intercensales", "#991B1B"),
    (k5, "amber", "🏗️ Creaciones",
     f"{n_creac:,}", "Post-2002", "#92400E"),
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
# FILA 2 — Mapa (izq ampliado) | Alertas (der compactas)
# ══════════════════════════════════════════════════════════════════════════════
col_mapa, col_der = st.columns([2, 1])

# ── Mapa coroplético ────────────────────────────────────────────────────────
with col_mapa:
    st.markdown('<div class="section-title">Mapa TCM distrital</div>',
                unsafe_allow_html=True)

    def color_tcm(v):
        if pd.isna(v): return "#CBD5E1"
        if v >= 1.5:   return "#1D4ED8"
        if v >= 0.5:   return "#60A5FA"
        if v >= 0:     return "#BAE6FD"
        if v >= -2.5:  return "#FCA5A5"
        if v >= -5.0:  return "#EF4444"
        return "#7F1D1D"

    m = folium.Map(
        location=[-9.5, -75.5],
        zoom_start=5,
        tiles=None,
        prefer_canvas=True,
    )
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">'
             'OpenStreetMap</a> contributors',
        name="OpenStreetMap",
        max_zoom=19,
    ).add_to(m)

    gdf_f = gdf_f.copy()
    gdf_f["_color"] = gdf_f[col_tcm].apply(color_tcm)

    col_pob_mapa   = "POB2017" if usar_0717 else "POB2025"
    label_pob_mapa = "Pob. 2017" if usar_0717 else "Pob. 2025"

    folium.GeoJson(
        gdf_f.__geo_interface__,
        style_function=lambda feat: {
            "fillColor":   feat["properties"].get("_color", "#CBD5E1"),
            "color":       "#ffffff",
            "weight":      0.3,
            "fillOpacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(
            fields   = ["NOMBDIST", "NOMBDEP", col_tcm,
                        col_pob_mapa, "REGION_NAT", "TIPOLOGIA"],
            aliases  = ["Distrito", "Departamento", f"TCM {periodo}",
                        label_pob_mapa, "Región", "Tipología"],
            localize = True,
            sticky   = False,
        ),
        smooth_factor=2.0,
        name="Distritos",
        embed=False,
    ).add_to(m)

    legend = """
    <div style="position:fixed;bottom:18px;left:14px;z-index:1000;
                background:white;padding:8px 12px;border-radius:8px;
                border:1px solid #e2e8f0;font-size:11px;
                box-shadow:0 2px 6px rgba(0,0,0,.15)">
      <b>TCM anual (%)</b><br>
      <span style="color:#1D4ED8">■</span> ≥ 1.5 &nbsp;
      <span style="color:#60A5FA">■</span> 0.5–1.5 &nbsp;
      <span style="color:#BAE6FD">■</span> 0–0.5<br>
      <span style="color:#FCA5A5">■</span> −2.5–0 &nbsp;
      <span style="color:#EF4444">■</span> −5–−2.5 &nbsp;
      <span style="color:#7F1D1D">■</span> &lt;−5<br>
      <span style="color:#CBD5E1">■</span> Sin datos
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    st_folium(m, width=None, height=480, returned_objects=[])


# ── Alertas compactas ───────────────────────────────────────────────────────
with col_der:
    st.markdown('<div class="section-title">🔔 Alertas</div>',
                unsafe_allow_html=True)

    for cls, ico, txt in [
        ("red",   "🚨",
         f"<b>{n_decrec:,} distritos</b> con decrecimiento "
         f"({n_decrec/total*100:.1f}%) — principalmente Sierra."),
        ("red",   "⚠️",
         f"<b>{n_doble:,} distritos</b> con doble decrecimiento "
         f"en ambos períodos."),
        ("amber", "🏗️",
         f"<b>{n_creac}</b> creaciones post-2002 en el territorio nacional."),
        ("blue",  "📊",
         f"Población total Censo 2025: "
         f"<b>{df['POB2025'].sum():,.0f} hab.</b>"),
        ("green", "✅",
         f"<b>{n_crec:,} distritos</b> ({n_crec/total*100:.1f}%) "
         f"con crecimiento — Costa y Selva Baja."),
    ]:
        st.markdown(
            f'<div class="alert-box alert-{cls}">{ico} <span>{txt}</span></div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Ranking crecimiento + Evolución + Comparativa
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_rank, col_evol = st.columns([1.5, 1])

with col_rank:
    # Dos tabs: decrecimiento y crecimiento
    tab_decrec, tab_crec = st.tabs([
        "Top departamentos · % con decrecimiento",
        "Top departamentos · % con crecimiento",
    ])

    dep = dff.groupby("NOMBDEP").agg(
        total  = ("UBIGEO", "count"),
        decrec = (col_tcm,  lambda x: (x < 0).sum()),
        crec   = (col_tcm,  lambda x: (x > 0).sum()),
    ).reset_index()
    dep["pct_decrec"] = dep["decrec"] / dep["total"] * 100
    dep["pct_crec"]   = dep["crec"]   / dep["total"] * 100

    ref_decrec = (dff[col_tcm] < 0).sum() / total * 100
    ref_crec   = (dff[col_tcm] > 0).sum() / total * 100

    with tab_decrec:
        top_d = dep.sort_values("decrec", ascending=False).head(12)
        fig_d = go.Figure(go.Bar(
            y=top_d["NOMBDEP"], x=top_d["pct_decrec"], orientation="h",
            marker_color="#EF4444",
            text=top_d["pct_decrec"].apply(lambda v: f"{v:.0f}%"),
            textposition="outside", textfont_size=10,
        ))
        fig_d.add_vline(
            x=ref_decrec, line_dash="dot", line_color="#64748b", line_width=1.5,
            annotation_text=f"Ref. nacional {ref_decrec:.0f}%",
            annotation_position="top right", annotation_font_size=10,
        )
        fig_d.update_layout(
            height=375, margin=dict(t=10, b=10, l=130, r=70),
            xaxis=dict(title="% con decrecimiento", range=[0, 110],
                       gridcolor="#f1f5f9"),
            yaxis=dict(autorange="reversed", tickfont_size=11),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_d, use_container_width=True)

    with tab_crec:
        top_c = dep.sort_values("crec", ascending=False).head(12)
        fig_c2 = go.Figure(go.Bar(
            y=top_c["NOMBDEP"], x=top_c["pct_crec"], orientation="h",
            marker_color="#10B981",
            text=top_c["pct_crec"].apply(lambda v: f"{v:.0f}%"),
            textposition="outside", textfont_size=10,
        ))
        fig_c2.add_vline(
            x=ref_crec, line_dash="dot", line_color="#64748b", line_width=1.5,
            annotation_text=f"Ref. nacional {ref_crec:.0f}%",
            annotation_position="top right", annotation_font_size=10,
        )
        fig_c2.update_layout(
            height=375, margin=dict(t=10, b=10, l=130, r=70),
            xaxis=dict(title="% con crecimiento", range=[0, 110],
                       gridcolor="#f1f5f9"),
            yaxis=dict(autorange="reversed", tickfont_size=11),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_c2, use_container_width=True)

with col_evol:
    st.markdown('<div class="section-title">'
                'Evolución N.° de distritos (2007–2025)</div>',
                unsafe_allow_html=True)

    evol = pd.DataFrame({
        "Año": [2007, 2017, 2020, 2021, 2022, 2025],
        "N":   [1833, 1874, 1875, 1890, 1891, 1892],
    })
    fig_e = go.Figure(go.Scatter(
        x=evol["Año"], y=evol["N"],
        mode="lines+markers+text",
        line=dict(color="#2E75B6", width=2.5),
        marker=dict(size=8, color="#2E75B6"),
        text=evol["N"], textposition="top center", textfont_size=11,
    ))
    fig_e.update_layout(
        height=175, margin=dict(t=10, b=20, l=10, r=10),
        xaxis=dict(tickvals=evol["Año"].tolist(), tickfont_size=9,
                   gridcolor="#f1f5f9"),
        yaxis=dict(range=[1820, 1910], tickfont_size=9, gridcolor="#f1f5f9"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_e, use_container_width=True)

    st.markdown('<div class="section-title" style="margin-top:.4rem">'
                'Comparativa 07-17 vs 17-25 · % con decrecimiento</div>',
                unsafe_allow_html=True)

    comp = dff.groupby("REGION_NAT").agg(
        p1=("TC_07_17", lambda x: (x < 0).sum() / max(len(x), 1) * 100),
        p2=("TC_17_25", lambda x: (x < 0).sum() / max(len(x), 1) * 100),
    ).reset_index()

    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        name="07-17", x=comp["REGION_NAT"], y=comp["p1"],
        marker_color="#4C72B0",
        text=comp["p1"].apply(lambda v: f"{v:.0f}%"),
        textposition="outside", textfont_size=9,
    ))
    fig_c.add_trace(go.Bar(
        name="17-25", x=comp["REGION_NAT"], y=comp["p2"],
        marker_color="#DD8452",
        text=comp["p2"].apply(lambda v: f"{v:.0f}%"),
        textposition="outside", textfont_size=9,
    ))
    fig_c.update_layout(
        barmode="group", height=175, margin=dict(t=10, b=10, l=10, r=10),
        yaxis=dict(range=[0, 110], tickfont_size=9, gridcolor="#f1f5f9"),
        xaxis_tickfont_size=9,
        legend=dict(orientation="h", y=1.2, x=0, font_size=9),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_c, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4 — Tabla interactiva + descarga
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Detalle distrital — tabla interactiva</div>',
            unsafe_allow_html=True)

cols_t = [c for c in [
    "UBIGEO", "NOMBDEP", "NOMBPROV", "NOMBDIST", "REGION_NAT",
    "TIPOLOGIA", "POB2007", "POB2017", "POB2025",
    "TC_07_17", "TC_17_25", "DOBLE_DECREC", "ES_CREACION", "ANIO",
] if c in dff.columns]

tabla = dff[cols_t].rename(columns={
    "NOMBDEP":      "Departamento",
    "NOMBPROV":     "Provincia",
    "NOMBDIST":     "Distrito",
    "REGION_NAT":   "Región",
    "TIPOLOGIA":    "Tipología",
    "TC_07_17":     "TCM 07-17 (%)",
    "TC_17_25":     "TCM 17-25 (%)",
    "DOBLE_DECREC": "Doble decrec.",
    "ES_CREACION":  "Creación",
    "ANIO":         "Año crea.",
})

# Tres buscadores separados: departamento, provincia, distrito
c_dep, c_prov, c_dist = st.columns(3)
with c_dep:
    b_dep = st.text_input("🔍 Departamento", "",
                          placeholder="Ej: LIMA",
                          label_visibility="collapsed")
with c_prov:
    b_prov = st.text_input("🔍 Provincia", "",
                           placeholder="Ej: HUARAZ",
                           label_visibility="collapsed")
with c_dist:
    b_dist = st.text_input("🔍 Distrito o ubigeo", "",
                           placeholder="Ej: CANGALLO o 050204",
                           label_visibility="collapsed")

if b_dep:
    tabla = tabla[tabla["Departamento"].str.contains(b_dep.upper(), na=False)]
if b_prov:
    tabla = tabla[tabla["Provincia"].str.contains(b_prov.upper(), na=False)]
if b_dist:
    tabla = tabla[
        tabla["Distrito"].str.contains(b_dist.upper(), na=False) |
        tabla["UBIGEO"].astype(str).str.contains(b_dist, na=False)
    ]

tabla_sorted = tabla.sort_values("TCM 07-17 (%)")

st.dataframe(
    tabla_sorted,
    use_container_width=True, height=280, hide_index=True,
)

# Descarga en CSV y Excel
col_dl1, col_dl2 = st.columns([1, 1])
with col_dl1:
    csv = tabla_sorted.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Descargar CSV",
        data=csv,
        file_name=f"crecimiento_{periodo.replace(' ','').replace('–','_')}.csv",
        mime="text/csv",
    )
with col_dl2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tabla_sorted.to_excel(writer, index=False, sheet_name="Crecimiento")
    st.download_button(
        label="⬇️ Descargar Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"crecimiento_{periodo.replace(' ','').replace('–','_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.markdown("---")
st.caption(
    "Fuentes: INEI Censos Nacionales 2007, 2017 y 2025 · "
    "Elaborado por SSIAT · SDOT-PCM · 2026"
)
