"""
pages/01_resumen_ejecutivo.py
Página 1 — Resumen Ejecutivo
Tablero de Análisis Espacial de Crecimiento Poblacional · SSIAT / SDOT-PCM
Fuentes: shapefile total_distritos_1892.shp + distritos_crec_pob.xlsx
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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
.alert-box { padding:.6rem 1rem; border-radius:7px; margin-bottom:.45rem;
             font-size:.84rem; display:flex; align-items:flex-start; gap:.6rem; }
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
gdf = cargar_datos_integrados()   # GeoDataFrame en WGS84 con atributos integrados


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — filtros
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Filtros")

    periodo = st.radio("Período de análisis",
                       ["2007 – 2017", "2017 – 2025"], index=0)
    usar_0717     = periodo == "2007 – 2017"
    col_tcm       = "TC_07_17"       if usar_0717 else "TC_17_25"
    col_tendencia = "TENDENCIA_0717" if usar_0717 else "TENDENCIA_1725"

    regiones   = ["Todas"] + sorted(df["REGION_NAT"].dropna().unique().tolist())
    region_sel = st.selectbox("Región natural", regiones)

    tipo_dist = st.selectbox(
        "Tipo de distrito",
        ["Todos", "Solo creaciones (post-2002)", "Solo origen"],
    )
    st.markdown("---")
    st.caption("Fuentes: INEI 2007, 2017, 2025 · Proy. 2025 · SSIAT 2026")

# Aplicar filtros al DataFrame tabular
dff = df.copy()
if region_sel != "Todas":
    dff = dff[dff["REGION_NAT"] == region_sel]
if tipo_dist == "Solo creaciones (post-2002)":
    dff = dff[dff["ES_CREACION"]]
elif tipo_dist == "Solo origen":
    dff = dff[~dff["ES_CREACION"]]

# Aplicar filtros al GeoDataFrame (para el mapa)
gdf_f = gdf.copy()
if region_sel != "Todas":
    gdf_f = gdf_f[gdf_f["REGION_NAT"] == region_sel]
if tipo_dist == "Solo creaciones (post-2002)":
    gdf_f = gdf_f[gdf_f["ES_CREACION"] == True]
elif tipo_dist == "Solo origen":
    gdf_f = gdf_f[gdf_f["ES_CREACION"] == False]


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>📊 Resumen Ejecutivo — Crecimiento Poblacional en el Perú</h2>
  <p>Período: <b>{periodo}</b> &nbsp;·&nbsp;
     Región: <b>{region_sel}</b> &nbsp;·&nbsp;
     Distritos: <b>{len(dff):,}</b> &nbsp;·&nbsp;
     SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
# En 2007-2017 la base censal es 1874; en 2017-2025 es 1892. Para el cálculo de porcentajes, usamos 1847 y 1892 respectivamente 
total     = len(dff)
total_kpi = 1874 if usar_0717 else 1892
n_crec    = int((dff[col_tcm] > 0).sum())
n_decrec  = int((dff[col_tcm] < 0).sum())
n_doble   = int(((dff["TC_07_17"] < 0) & (dff["TC_17_25"] < 0)).sum())
n_creac   = int(dff["ES_CREACION"].sum())
pob_total = dff["POB2025" if not usar_0717 else "POB2017"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",  "🗺️ Distritos",          f"{total_kpi:,}", "Base censo 2017" if usar_0717 else "Base censo 2025", "#1E40AF"),
    (k2, "green", "📈 Con crecimiento",    f"{n_crec:,}",   f"{n_crec/total*100:.1f}% del total", "#166534"),
    (k3, "red",   "📉 Con decrecimiento",  f"{n_decrec:,}", f"{n_decrec/total*100:.1f}% del total","#991B1B"),
    (k4, "red",   "⚠️ Doble decrec.",      f"{n_doble:,}",  "Negativa en ambos períodos intercensales",          "#991B1B"),
    (k5, "amber", "🏗️ Creaciones",         f"{n_creac:,}",  "Post-2002",                           "#92400E"),
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
# FILA 2 — Región natural | Mapa | Alertas
# ══════════════════════════════════════════════════════════════════════════════
col_izq, col_mapa, col_der = st.columns([1.1, 1.7, 1.1])

COLOR_REG = {
    "COSTA":      "#ECF007",
    "SIERRA":     "#5E2417",
    "SELVA ALTA": "#175E1A",
    "SELVA BAJA": "#18C420",
}

# ── TCM por región natural ─────────────────────────────────────────────────
with col_izq:
    st.markdown('<div class="section-title">TCM por región natural</div>',
                unsafe_allow_html=True)

    reg = dff.groupby("REGION_NAT").agg(
        n       = ("UBIGEO",  "count"),
        pob     = ("POB2017", "sum"),
        tcm_med = (col_tcm,   "mean"),
        n_crec  = (col_tcm,   lambda x: (x > 0).sum()),
    ).reset_index().sort_values("pob", ascending=False)

    for _, r in reg.iterrows():
        tc  = r["tcm_med"]
        col = "#10B981" if tc > 0 else "#EF4444"
        pct = r["n_crec"] / r["n"] * 100 if r["n"] > 0 else 0
        st.markdown(f"""
        <div style="background:#f8fafc;border-radius:8px;padding:.7rem .9rem;
                    margin-bottom:.4rem;
                    border-left:3px solid {COLOR_REG.get(r['REGION_NAT'], '#94a3b8')}">
          <div style="font-weight:600;font-size:.82rem">{r['REGION_NAT']}</div>
          <div style="display:flex;justify-content:space-between;margin-top:.2rem">
            <span style="font-size:.76rem;color:#64748b">{int(r['n'])} distritos</span>
            <span style="font-weight:700;font-size:.82rem;color:{col}">
              {'▲' if tc > 0 else '▼'} {tc:.2f}%</span>
          </div>
          <div style="background:#e2e8f0;border-radius:99px;height:5px;margin-top:.3rem">
            <div style="background:{col};width:{min(pct,100):.0f}%;
                        height:5px;border-radius:99px"></div>
          </div>
          <div style="font-size:.7rem;color:#94a3b8;margin-top:.15rem">
            {pct:.0f}% crecen</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:.7rem">'
                '% Población nacional</div>', unsafe_allow_html=True)
    fig_pie = px.pie(
        reg, values="pob", names="REGION_NAT",
        color="REGION_NAT", color_discrete_map=COLOR_REG, hole=0.45,
    )
    fig_pie.update_traces(textposition="outside", textinfo="percent+label",
                          textfont_size=10)
    fig_pie.update_layout(margin=dict(t=5,b=5,l=5,r=5), height=185,
                          showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pie, use_container_width=True)


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
        tiles=None,             # Sin tile por defecto - lo agregamos explícitamente abajo 
        prefer_canvas=True,     # Canvas renderer: más rápido que SVG para muchos polígonos
    )
 
    # Tile OSM explícito — sin API key, siempre disponible, sobrescribe cualquier default
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap",
        max_zoom=19,
    ).add_to(m)
    
    # Pre-calcular colores fuera del GeoJson para evitar llamadas repetidas
    gdf_f = gdf_f.copy()
    gdf_f["_color"] = gdf_f[col_tcm].apply(color_tcm)
    
    col_pob_mapa = "POB2017" if usar_0717 else "POB2025"
    label_pob_mapa = "Pob. 2017" if usar_0717 else "Pob. 2025"

    folium.GeoJson(
        gdf_f.__geo_interface__,
        style_function=lambda feat: {
            "fillColor": feat["properties"].get("_color", "#CBD5E1"),
            "color":      "#ffffff",
            "weight":      0.3,
            "fillOpacity": 0.75,
        },
        
        tooltip=folium.GeoJsonTooltip(
            fields    = ["NOMBDIST", "NOMBDEP", col_tcm,
                         col_pob_mapa, "REGION_NAT", "TIPOLOGIA"],
            aliases   = ["Distrito", "Departamento", f"TCM {periodo}",
                         label_pob_mapa, "Región", "Tipología"],
            localize  = True,
            sticky    = False, # False es más liviano que sticky=True
        ),
        smooth_factor=2.0, # Simplifica geometrías en el navegador, menos vértices renderizados
        name="Distritos",
        embed=False        # No embede el GeoJSON en el HTML -> carga más rápido 
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

    st_folium(m, width=None, height=430, returned_objects=[])


# ── Alertas automáticas ─────────────────────────────────────────────────────
with col_der:
    st.markdown('<div class="section-title">🔔 Alertas</div>',
                unsafe_allow_html=True)

    crea_d = dff[dff["ES_CREACION"] & (dff[col_tcm] < 0)]

    for cls, ico, txt in [
        ("red",   "🚨",
         f"<b>{n_decrec:,} distritos</b> con decrecimiento "
         f"({n_decrec/total*100:.1f}%) — principalmente Sierra."),
        ("red",   "⚠️",
         f"<b>{n_doble:,} distritos</b> con doble decrecimiento "
         f"en ambos períodos."),
        ("amber", "🏗️",
         f"<b>{len(crea_d)} creaciones</b> post-2002 con TCM "
         f"negativa en el período reciente."),
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

    if len(crea_d) > 0:
        st.markdown(
            '<div class="section-title" style="margin-top:.7rem">'
            'Creaciones con decrecimiento reciente</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            crea_d[["NOMBDIST", "NOMBDEP", "ANIO", col_tcm]]
            .rename(columns={col_tcm: "TCM (%)", "ANIO": "Año"})
            .sort_values("TCM (%)"),
            use_container_width=True, height=175, hide_index=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Ranking + evolución + comparativa
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_rank, col_evol = st.columns([1.5, 1])

with col_rank:
    st.markdown('<div class="section-title">'
                'Top departamentos · % distritos con decrecimiento</div>',
                unsafe_allow_html=True)

    dep = dff.groupby("NOMBDEP").agg(
        total  = ("UBIGEO", "count"),
        decrec = (col_tcm,  lambda x: (x < 0).sum()),
    ).reset_index()
    dep["pct"] = dep["decrec"] / dep["total"] * 100
    dep = dep.sort_values("decrec", ascending=False).head(12)
    ref = (dff[col_tcm] < 0).sum() / total * 100

    fig_r = go.Figure(go.Bar(
        y=dep["NOMBDEP"], x=dep["pct"], orientation="h",
        marker_color="#EF4444",
        text=dep["pct"].apply(lambda v: f"{v:.0f}%"),
        textposition="outside", textfont_size=10,
    ))
    fig_r.add_vline(
        x=ref, line_dash="dot", line_color="#64748b", line_width=1.5,
        annotation_text=f"Ref. nacional {ref:.0f}%",
        annotation_position="top right", annotation_font_size=10,
    )
    fig_r.update_layout(
        height=375, margin=dict(t=10,b=10,l=130,r=60),
        xaxis=dict(title="% con decrecimiento", range=[0,105],
                   gridcolor="#f1f5f9"),
        yaxis=dict(autorange="reversed", tickfont_size=11),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_r, use_container_width=True)

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
        height=175, margin=dict(t=10,b=20,l=10,r=10),
        xaxis=dict(tickvals=evol["Año"].tolist(), tickfont_size=9,
                   gridcolor="#f1f5f9"),
        yaxis=dict(range=[1820,1910], tickfont_size=9, gridcolor="#f1f5f9"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_e, use_container_width=True)

    st.markdown('<div class="section-title" style="margin-top:.4rem">'
                'Comparativa intercensal 07-17 vs 17-25 · % con decrecimiento</div>',
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
        barmode="group", height=175, margin=dict(t=10,b=10,l=10,r=10),
        yaxis=dict(range=[0,110], tickfont_size=9, gridcolor="#f1f5f9"),
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
    "NOMBDEP":    "Departamento",
    "NOMBPROV":   "Provincia",
    "NOMBDIST":   "Distrito",
    "REGION_NAT": "Región",
    "TIPOLOGIA":  "Tipología",
    "TC_07_17":   "TCM 07-17 (%)",
    "TC_17_25":   "TCM 17-25 (%)",
    "DOBLE_DECREC": "Doble decrec.",
    "ES_CREACION":  "Creación",
    "ANIO":         "Año crea.",
})

busqueda = st.text_input("🔍 Buscar por nombre de distrito o ubigeo", "")
if busqueda:
    mask = (
        tabla["Distrito"].str.contains(busqueda.upper(), na=False) |
        tabla["UBIGEO"].astype(str).str.contains(busqueda, na=False)
    )
    tabla = tabla[mask]

st.dataframe(
    tabla.sort_values("TCM 07-17 (%)"),
    use_container_width=True, height=275, hide_index=True,
)

csv = tabla.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️ Descargar tabla (CSV)",
    data=csv,
    file_name=f"crecimiento_{periodo.replace(' ','').replace('–','_')}.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption(
    "Fuentes: INEI Censos Nacionales 2007, 2017 y 2025 · "
    "Proyecciones Poblacionales 2025 · "
    "Elaborado por SSIAT · SDOT-PCM · 2026"
)
