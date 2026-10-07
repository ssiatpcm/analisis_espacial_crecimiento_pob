"""
pages/04_creaciones_en_riesgo.py
Página 4 — Creaciones distritales en riesgo demográfico
Tablero de Análisis Espacial de Crecimiento Poblacional · SSIAT / SDOT-PCM
Fuentes:
    - totalcreaciones_dist2002.shp  → 64 creaciones + 48 distritos de origen
    - distritos_crec_pob.xlsx       → variables demográficas
"""

import warnings
warnings.filterwarnings("ignore")

import io
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.carga_datos import cargar_dataframe

# ── Configuración ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Creaciones en riesgo · SSIAT",
    page_icon="🚨",
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
.kpi-box.blue   { border-left:4px solid #2E75B6; }
.kpi-box.green  { border-left:4px solid #10B981; }
.kpi-box.red    { border-left:4px solid #EF4444; }
.kpi-box.amber  { border-left:4px solid #F59E0B; }
.kpi-label { font-size:.78rem; color:#64748b; margin-bottom:.15rem; }
.kpi-value { font-size:1.7rem; font-weight:700; line-height:1.1; }
.kpi-sub   { font-size:.76rem; color:#94a3b8; margin-top:.2rem; }
.riesgo-row {
    display:flex; align-items:flex-start; gap:8px;
    padding:7px 10px; border-radius:7px; margin-bottom:5px;
    font-size:.82rem; background:#f8fafc;
}
.section-title {
    font-size:.72rem; font-weight:600; letter-spacing:.06em;
    text-transform:uppercase; color:#94a3b8; margin-bottom:.6rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PALETAS Y CLASIFICACIONES
# ══════════════════════════════════════════════════════════════════════════════
COLORES_RIESGO = {
    "Crecimiento sostenido":  "#10B981",
    "Crecimiento":            "#60A5FA",
    "Recuperación (↓→↑)":    "#60A5FA",
    "Reversión (↑→↓)":       "#F59E0B",
    "Decrecimiento":          "#EF4444",
    "Doble decrecimiento":    "#7F1D1D",
    "Sin datos":              "#CBD5E1",
}

COLORES_DESP = {
    "Crecimiento sostenido":       "#10B981",
    "Recuperación (↓→↑)":         "#60A5FA",
    "Decrecimiento reciente":      "#F59E0B",
    "Despoblamiento persistente":  "#7F1D1D",
    "Sin datos":                   "#CBD5E1",
}

DESCRIPCION_RIESGO = {
    "Crecimiento sostenido":  "TCM positiva en ambos períodos intercensales",
    "Crecimiento":            "TCM positiva en el período reciente (17–25)",
    "Recuperación (↓→↑)":    "TCM negativa en 07-17, recupera en 17-25",
    "Reversión (↑→↓)":       "Crecía en 07-17, decrece en 17-25",
    "Decrecimiento":          "TCM negativa · creación reciente sin datos previos",
    "Doble decrecimiento":    "TCM negativa en ambos períodos · mayor riesgo",
    "Sin datos":              "Creaciones 2022/2025 sin censo posterior",
}

DESCRIPCION_DESP = {
    "Crecimiento sostenido":       "TCM positiva en ambos períodos",
    "Recuperación (↓→↑)":         "Decreció en 07-17 pero se recupera en 17-25",
    "Decrecimiento reciente":      "Crecía en 07-17, pierde población en 17-25",
    "Despoblamiento persistente":  "TCM negativa en ambos períodos",
    "Sin datos":                   "Sin datos censales suficientes",
}


# ══════════════════════════════════════════════════════════════════════════════
# CARGA Y PREPARACIÓN
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Cargando creaciones distritales...")
def cargar_creaciones():
    shp = ROOT / "data" / "totalcreaciones_dist2002.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    gdf["UBIGEO"] = gdf["UBIGEO"].astype(str).str.zfill(6)

    df = cargar_dataframe()

    merged = gdf[["UBIGEO", "tipo", "geometry"]].merge(
        df[[
            "UBIGEO", "NOMBDEP", "NOMBPROV", "NOMBDIST",
            "POB2007", "POB2017", "POB2025",
            "TC_07_17", "TC_17_25",
            "REGION_NAT", "ANIO", "AMB_INT", "MODALIDAD", "TIPOLOGIA",
        ]],
        on="UBIGEO", how="left",
    )

    merged["AMB_INT"] = merged["AMB_INT"].fillna("Sin ámbito especial")
    LABEL_AMB = {
        "VRAEM":         "VRAEM",
        "Alto Huallaga": "Alto Huallaga",
        "ACF":           "Áreas Críticas Fronterizas (ACF)",
        "Sin ámbito especial": "Sin ámbito especial",
    }
    merged["AMB_INT"] = merged["AMB_INT"].map(LABEL_AMB).fillna(merged["AMB_INT"])

    def clasif_riesgo(r):
        t17, t25 = r["TC_07_17"], r["TC_17_25"]
        if pd.isna(t25):               return "Sin datos"
        if pd.isna(t17):
            return "Crecimiento" if t25 > 0 else "Decrecimiento"
        if t17 > 0 and t25 > 0:       return "Crecimiento sostenido"
        if t17 > 0 and t25 < 0:       return "Reversión (↑→↓)"
        if t17 < 0 and t25 > 0:       return "Recuperación (↓→↑)"
        if t17 < 0 and t25 < 0:       return "Doble decrecimiento"
        return "Sin datos"

    def clasif_desp(r):
        t17, t25 = r["TC_07_17"], r["TC_17_25"]
        if pd.isna(t17) or pd.isna(t25): return "Sin datos"
        if t17 < 0 and t25 < 0:          return "Despoblamiento persistente"
        if t17 < 0 and t25 >= 0:         return "Recuperación (↓→↑)"
        if t17 >= 0 and t25 < 0:         return "Decrecimiento reciente"
        return "Crecimiento sostenido"

    crea = merged[merged["tipo"] == "creacion"].copy()
    orig = merged[merged["tipo"] == "origen"].copy()

    crea["CAT_RIESGO"] = crea.apply(clasif_riesgo, axis=1)
    orig["CAT_DESP"]   = orig.apply(clasif_desp,   axis=1)

    return crea, orig


crea, orig = cargar_creaciones()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — filtros
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Filtros")
    periodo = st.radio("Período de referencia",
                       ["2017 – 2025", "2007 – 2017"], index=0)
    usar_1725 = periodo == "2017 – 2025"
    col_tcm   = "TC_17_25" if usar_1725 else "TC_07_17"

    ambitos_disp = ["Todos"] + sorted(crea["AMB_INT"].dropna().unique().tolist())
    ambito_sel   = st.selectbox("Ámbito de influencia", ambitos_disp, index=0)

    LABEL_MOD_SIDEBAR = {
        "IN":  "Interés Nacional (IN)",
        "SOT": "Saneamiento y Org. Territorial (SOT)",
        "ZF":  "Zona de Frontera (ZF)",
    }
    mods_disp = ["Todas"] + [
        LABEL_MOD_SIDEBAR.get(m, m)
        for m in sorted(crea["MODALIDAD"].dropna().unique().tolist())
    ]
    modalidad_sel = st.selectbox("Modalidad de creación", mods_disp, index=0)
    # Mapa inverso para filtrar
    MOD_INV = {v: k for k, v in LABEL_MOD_SIDEBAR.items()}

    st.markdown("---")
    st.caption("Fuente: Shapefile totalcreaciones_dist2002 · SSIAT 2026")

# Aplicar filtros de ámbito y modalidad
crea_f = crea.copy()
if ambito_sel != "Todos":
    crea_f = crea_f[crea_f["AMB_INT"] == ambito_sel]
if modalidad_sel != "Todas":
    mod_code = MOD_INV.get(modalidad_sel, modalidad_sel)
    crea_f = crea_f[crea_f["MODALIDAD"] == mod_code]
orig_f = orig.copy()


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
n_riesgo = int(((crea_f[col_tcm] < 0).sum()))
st.markdown(f"""
<div class="header-banner">
  <h2>🚨 Creaciones distritales en riesgo demográfico — Post-2002</h2>
  <p>Período de referencia: <b>{periodo}</b> &nbsp;·&nbsp;
     Ámbito: <b>{ambito_sel}</b> &nbsp;·&nbsp;
     64 creaciones · 48 distritos de origen · SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
total_c    = len(crea_f)
n_crec_c   = int((crea_f[col_tcm] > 0).sum())
n_decrec_c = int((crea_f[col_tcm] < 0).sum())
n_desp_o   = int((orig_f["CAT_DESP"] == "Despoblamiento persistente").sum())

k1, k2, k3, k4 = st.columns(4)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",  "🗺️ Creaciones post-2002",
     f"{total_c:,}", f"Ámbito: {ambito_sel}", "#1E40AF"),
    (k2, "green", "📈 Con crecimiento",
     f"{n_crec_c:,}",
     f"{n_crec_c/total_c*100:.1f}% · período {periodo}", "#166534"),
    (k3, "red",   "📉 Con decrecimiento",
     f"{n_decrec_c:,}",
     f"{n_decrec_c/total_c*100:.1f}% · riesgo demográfico", "#991B1B"),
    (k4, "amber", "⚠️ Despoblamiento persistente",
     f"{n_desp_o:,}",
     f"de 48 distritos de origen ({n_desp_o/48*100:.0f}%)", "#92400E"),
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
# FILA 2 — Mapa + Clasificación de riesgo
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Distribución espacial — clasificación de riesgo</div>',
            unsafe_allow_html=True)

col_mapa, col_clas = st.columns([1.8, 1])

with col_mapa:
    tab_crea, tab_orig, tab_ambos = st.tabs([
        "Creaciones", "Distritos de origen", "Ambos",
    ])

    def base_map():
        m = folium.Map(location=[-9.5, -75.5], zoom_start=5,
                       tiles=None, prefer_canvas=True)
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">'
                 'OpenStreetMap</a> contributors',
            name="OpenStreetMap", max_zoom=19,
        ).add_to(m)
        return m

    def add_layer_crea(m, data, col_tcm_map):
        data = data.copy()
        data["_color"] = data["CAT_RIESGO"].map(COLORES_RIESGO).fillna("#CBD5E1")
        folium.GeoJson(
            data.__geo_interface__,
            style_function=lambda feat: {
                "fillColor":   feat["properties"].get("_color", "#CBD5E1"),
                "color":       "#1B4D5C",
                "weight":      0.8,
                "fillOpacity": 0.85,
            },
            tooltip=folium.GeoJsonTooltip(
                fields   = ["NOMBDIST", "NOMBDEP", "ANIO", "AMB_INT",
                            "MODALIDAD", col_tcm_map, "POB2025", "CAT_RIESGO"],
                aliases  = ["Distrito", "Dpto.", "Año creación", "Ámbito",
                            "Modalidad", f"TCM {periodo}", "Pob. 2025", "Clasificación"],
                localize=True, sticky=False,
            ),
            smooth_factor=1.5, embed=False,
            name="Creaciones",
        ).add_to(m)

    def add_layer_orig(m, data):
        data = data.copy()
        data["_color"] = data["CAT_DESP"].map(COLORES_DESP).fillna("#CBD5E1")
        folium.GeoJson(
            data.__geo_interface__,
            style_function=lambda feat: {
                "fillColor":   feat["properties"].get("_color", "#CBD5E1"),
                "color":       "#475569",
                "weight":      0.5,
                "fillOpacity": 0.65,
            },
            tooltip=folium.GeoJsonTooltip(
                fields   = ["NOMBDIST", "NOMBDEP", "TC_07_17",
                            "TC_17_25", "POB2025", "CAT_DESP"],
                aliases  = ["Distrito origen", "Dpto.", "TCM 07-17",
                            "TCM 17-25", "Pob. 2025", "Categoría"],
                localize=True, sticky=False,
            ),
            smooth_factor=1.5, embed=False,
            name="Origen",
        ).add_to(m)

    leyenda_crea = """
    <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                background:white;padding:11px 15px;border-radius:8px;
                border:1px solid #e2e8f0;font-size:12px;line-height:1.7;
                box-shadow:0 2px 5px rgba(0,0,0,.12)">
      <b style="font-size:12px">Creaciones · clasificación de riesgo</b><br>
      <span style="color:#10B981;font-size:14px">■</span> Crecimiento sostenido<br>
      <span style="color:#60A5FA;font-size:14px">■</span> Crecimiento (período reciente)<br>
      <span style="color:#F59E0B;font-size:14px">■</span> Reversión (↑→↓)<br>
      <span style="color:#EF4444;font-size:14px">■</span> Decrecimiento<br>
      <span style="color:#7F1D1D;font-size:14px">■</span> Doble decrecimiento<br>
      <span style="color:#CBD5E1;font-size:14px">■</span> Sin datos
    </div>"""

    leyenda_orig = """
    <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                background:white;padding:11px 15px;border-radius:8px;
                border:1px solid #e2e8f0;font-size:12px;line-height:1.7;
                box-shadow:0 2px 5px rgba(0,0,0,.12)">
      <b style="font-size:12px">Distritos de origen · categoría</b><br>
      <span style="color:#10B981;font-size:14px">■</span> Crecimiento sostenido<br>
      <span style="color:#60A5FA;font-size:14px">■</span> Recuperación (↓→↑)<br>
      <span style="color:#F59E0B;font-size:14px">■</span> Decrecimiento reciente<br>
      <span style="color:#7F1D1D;font-size:14px">■</span> Despoblamiento persistente<br>
      <span style="color:#CBD5E1;font-size:14px">■</span> Sin datos
    </div>"""

    with tab_crea:
        m = base_map()
        add_layer_crea(m, crea_f, col_tcm)
        m.get_root().html.add_child(folium.Element(leyenda_crea))
        st_folium(m, width=None, height=480, returned_objects=[])

    with tab_orig:
        m2 = base_map()
        add_layer_orig(m2, orig_f)
        m2.get_root().html.add_child(folium.Element(leyenda_orig))
        st_folium(m2, width=None, height=480, returned_objects=[])

    with tab_ambos:
        m3 = base_map()
        add_layer_orig(m3, orig_f)
        add_layer_crea(m3, crea_f, col_tcm)
        m3.get_root().html.add_child(folium.Element(leyenda_crea))
        st_folium(m3, width=None, height=480, returned_objects=[])


with col_clas:
    st.markdown('<div class="section-title">Clasificación de riesgo — creaciones</div>',
                unsafe_allow_html=True)

    counts_r = crea_f["CAT_RIESGO"].value_counts()
    for cat, color in COLORES_RIESGO.items():
        n = counts_r.get(cat, 0)
        if n == 0:
            continue
        pct = n / total_c * 100
        desc = DESCRIPCION_RIESGO.get(cat, "")
        st.markdown(f"""
        <div class="riesgo-row">
          <div style="width:10px;height:10px;border-radius:50%;background:{color};
                      flex-shrink:0;margin-top:3px"></div>
          <div>
            <span style="font-weight:500;font-size:.83rem">{cat}</span>
            <span style="color:#64748b;font-size:.83rem"> — {n} ({pct:.1f}%)</span><br>
            <span style="font-size:.72rem;color:#94a3b8">{desc}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">Categoría — distritos de origen</div>',
                unsafe_allow_html=True)

    counts_orig_side = orig_f["CAT_DESP"].value_counts()
    total_orig_side  = len(orig_f)
    for cat, color in COLORES_DESP.items():
        n = counts_orig_side.get(cat, 0)
        if n == 0:
            continue
        pct = n / total_orig_side * 100
        desc = DESCRIPCION_DESP.get(cat, "")
        st.markdown(f"""
        <div class="riesgo-row">
          <div style="width:10px;height:10px;border-radius:50%;background:{color};
                      flex-shrink:0;margin-top:3px"></div>
          <div>
            <span style="font-weight:500;font-size:.83rem">{cat}</span>
            <span style="color:#64748b;font-size:.83rem"> — {n} ({pct:.1f}%)</span><br>
            <span style="font-size:.72rem;color:#94a3b8">{desc}</span>
          </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Gráfico temporal + modalidad + origen
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_yr, col_mod, col_amb = st.columns(3)

with col_yr:
    st.markdown('<div class="section-title">'
                'Creaciones por año vs % con decrecimiento</div>',
                unsafe_allow_html=True)

    yr = crea.groupby("ANIO").agg(
        total   = ("UBIGEO", "count"),
        decrece = ("TC_17_25", lambda x: (x < 0).sum()),
    ).reset_index().dropna(subset=["ANIO"])
    yr["pct_dec"] = (yr["decrece"] / yr["total"] * 100).round(1)
    yr["ANIO"] = yr["ANIO"].astype(int).astype(str)

    fig_yr = go.Figure()
    fig_yr.add_trace(go.Bar(
        x=yr["ANIO"], y=yr["total"],
        name="N° creaciones",
        marker_color="#2E75B6",
        yaxis="y1",
    ))
    fig_yr.add_trace(go.Scatter(
        x=yr["ANIO"], y=yr["pct_dec"],
        name="% con decrec. 17-25",
        mode="lines+markers",
        line=dict(color="#EF4444", width=2),
        marker=dict(size=6),
        yaxis="y2",
    ))
    fig_yr.update_layout(
        height=280,
        margin=dict(t=10, b=10, l=10, r=120),
        xaxis=dict(tickfont_size=9, tickangle=45),
        yaxis=dict(title="N° creaciones", gridcolor="#f1f5f9",
                   tickfont_size=9),
        yaxis2=dict(title="% con decrec.", overlaying="y", side="right",
                    tickfont_size=9, range=[0, 100],
                    tickformat=".0f",
                    showgrid=False),
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            xanchor="left", yanchor="middle",
            font_size=9,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e2e8f0", borderwidth=1,
        ),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        barmode="overlay",
    )
    st.plotly_chart(fig_yr, use_container_width=True)
    st.caption("Pico de creaciones: 2015 (16) y 2021 (15). "
               "Mayor % de decrecimiento en 2010 (75% — 3 de 4 creaciones).")

with col_mod:
    st.markdown('<div class="section-title">'
                'Distribución por modalidad de creación</div>',
                unsafe_allow_html=True)

    mod = crea.groupby("MODALIDAD").agg(
        total   = ("UBIGEO", "count"),
        crece   = ("TC_17_25", lambda x: (x > 0).sum()),
        decrece = ("TC_17_25", lambda x: (x < 0).sum()),
    ).reset_index().sort_values("total", ascending=False)

    LABEL_MOD = {
        "IN":  "Interés Nacional (IN)",
        "SOT": "Saneamiento y Organización Territorial (SOT)",
        "ZF":  "Zona de Frontera (ZF)",
    }
    mod["label"] = mod["MODALIDAD"].map(LABEL_MOD).fillna(mod["MODALIDAD"])

    fig_mod = go.Figure()
    fig_mod.add_trace(go.Bar(
        x=mod["label"], y=mod["crece"],
        name="Crecen", marker_color="#10B981",
        text=mod["crece"], textposition="outside", textfont_size=10,
    ))
    fig_mod.add_trace(go.Bar(
        x=mod["label"], y=mod["decrece"],
        name="Decrecen", marker_color="#EF4444",
        text=mod["decrece"], textposition="outside", textfont_size=10,
    ))
    fig_mod.update_layout(
        barmode="group", height=280,
        margin=dict(t=10, b=10, l=10, r=130),
        xaxis_tickfont_size=10,
        yaxis=dict(gridcolor="#f1f5f9", tickfont_size=9),
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            xanchor="left", yanchor="middle",
            font_size=10,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e2e8f0", borderwidth=1,
        ),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_mod, use_container_width=True)
    st.caption("Iniciativa (IN) concentra el mayor número de creaciones "
               "con riesgo demográfico (7 de 9 casos).")

with col_amb:
    st.markdown('<div class="section-title">'
                'Riesgo por ámbito de influencia</div>',
                unsafe_allow_html=True)

    amb = crea.groupby("AMB_INT").agg(
        total  = ("UBIGEO", "count"),
        riesgo = (col_tcm, lambda x: (x < 0).sum()),
    ).reset_index()
    amb["pct"] = (amb["riesgo"] / amb["total"] * 100).round(1)

    fig_amb = go.Figure()
    fig_amb.add_trace(go.Bar(
        y=amb["AMB_INT"], x=amb["total"],
        orientation="h", marker_color="#BAE6FD",
        name="Total", offsetgroup=1,
        text=amb["total"], textposition="outside", textfont_size=9,
    ))
    fig_amb.add_trace(go.Bar(
        y=amb["AMB_INT"], x=amb["riesgo"],
        orientation="h", marker_color="#EF4444",
        name="Con riesgo", offsetgroup=2,
        text=amb["riesgo"], textposition="outside", textfont_size=9,
    ))
    fig_amb.update_layout(
        barmode="group", height=280,
        margin=dict(t=5, b=5, l=10, r=110),
        xaxis=dict(gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=9),
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            xanchor="left", yanchor="middle",
            font_size=9,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e2e8f0", borderwidth=1,
        ),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_amb, use_container_width=True)
    st.caption("ACF = Áreas Críticas Fronterizas · "
               "Mayor proporción de riesgo en ACF (33%).")


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4 — Dos tablas detalle
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_t1, col_t2 = st.columns(2)

def descarga_buttons(df_dl, nombre_base, key_sfx):
    c1, c2 = st.columns(2)
    with c1:
        csv = df_dl.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "⬇️ CSV", data=csv,
            file_name=f"{nombre_base}.csv",
            mime="text/csv", key=f"csv_{key_sfx}",
        )
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_dl.to_excel(w, index=False, sheet_name=nombre_base[:31])
        st.download_button(
            "⬇️ Excel", data=buf.getvalue(),
            file_name=f"{nombre_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"xlsx_{key_sfx}",
        )

# ── Tabla 1: Creaciones en riesgo ──────────────────────────────────────────
with col_t1:
    st.markdown('<div class="section-title">Creaciones en riesgo demográfico</div>',
                unsafe_allow_html=True)

    riesgo_cats = ["Todos"] + [
        c for c in COLORES_RIESGO
        if c not in ("Crecimiento sostenido", "Crecimiento",
                     "Recuperación (↓→↑)", "Sin datos")
    ]
    riesgo_sel = st.selectbox("Filtrar por riesgo", riesgo_cats,
                              key="riesgo_sel", label_visibility="collapsed")

    cols_t1 = {
        "UBIGEO": "Ubigeo",
        "NOMBDEP": "Dpto.",
        "NOMBPROV": "Provincia",
        "NOMBDIST": "Distrito",
        "ANIO": "Año crea.",
        "AMB_INT": "Ámbito",
        "MODALIDAD": "Modalidad",
        "TIPOLOGIA": "Tipología",
        "POB2017": "Pob. 2017",
        "POB2025": "Pob. 2025",
        "TC_07_17": "TCM 07-17 (%)",
        "TC_17_25": "TCM 17-25 (%)",
        "CAT_RIESGO": "Clasificación",
    }
    t1 = crea_f[[c for c in cols_t1 if c in crea_f.columns]].rename(columns=cols_t1)

    if riesgo_sel != "Todos":
        t1 = t1[t1["Clasificación"] == riesgo_sel]
    else:
        # Por defecto mostrar solo los de riesgo
        t1 = t1[~t1["Clasificación"].isin(
            ["Crecimiento sostenido", "Crecimiento", "Recuperación (↓→↑)", "Sin datos"]
        )]

    t1_sorted = t1.sort_values("TCM 17-25 (%)")
    st.dataframe(t1_sorted, use_container_width=True, height=260, hide_index=True)
    descarga_buttons(t1_sorted, "creaciones_en_riesgo", "t1")

# ── Tabla 2: Despoblamiento persistente ────────────────────────────────────
with col_t2:
    st.markdown('<div class="section-title">Despoblamiento persistente — distritos de origen</div>',
                unsafe_allow_html=True)

    desp_cats = ["Todos"] + list(COLORES_DESP.keys())[:-1]
    desp_sel  = st.selectbox("Filtrar por categoría", desp_cats,
                             key="desp_sel", label_visibility="collapsed")

    cols_t2 = {
        "UBIGEO": "Ubigeo",
        "NOMBDEP": "Dpto.",
        "NOMBPROV": "Provincia",
        "NOMBDIST": "Distrito",
        "REGION_NAT": "Región",
        "TIPOLOGIA": "Tipología",
        "POB2007": "Pob. 2007",
        "POB2017": "Pob. 2017",
        "POB2025": "Pob. 2025",
        "TC_07_17": "TCM 07-17 (%)",
        "TC_17_25": "TCM 17-25 (%)",
        "CAT_DESP": "Categoría",
    }
    t2 = orig_f[[c for c in cols_t2 if c in orig_f.columns]].rename(columns=cols_t2)

    if desp_sel != "Todos":
        t2 = t2[t2["Categoría"] == desp_sel]

    t2_sorted = t2.sort_values("TCM 17-25 (%)")
    st.dataframe(t2_sorted, use_container_width=True, height=260, hide_index=True)
    descarga_buttons(t2_sorted, "despoblamiento_persistente_origen", "t2")


# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: INEI Censos 2007, 2017 y 2025 · "
    "Shapefile totalcreaciones_dist2002 · "
    "Elaborado por SSIAT · SDOT-PCM · 2026"
)
