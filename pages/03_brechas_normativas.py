"""
pages/03_brechas_normativas.py
Página 3 — Brechas normativas · TUO DS 134-2025-PCM
Requisito poblacional mínimo · Tablas N°1 y N°2
SSIAT / SDOT-PCM · 2026

Fuentes de datos:
    - distritos_crec_pob.xlsx  → POB2017 (Censo 2017) y POB2025 (Censo 2025)
    - total_distritos_1892.shp → geometría distrital
Marco normativo:
    - Tabla N°1 (DS 191-2020-PCM): umbral creación distrital
    - Tabla N°2 (RVM 005-2019-PCM): umbral fusión/reorganización
    - Umbral mínimo absoluto: 4,800 hab. (tipologías B1/B2/B3 · Tabla N°1)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.carga_datos import cargar_dataframe, cargar_geodataframe

# ── Configuración ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Brechas normativas · SSIAT",
    page_icon="⚖️",
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
.section-title {
    font-size:.72rem; font-weight:600; letter-spacing:.06em;
    text-transform:uppercase; color:#94a3b8; margin-bottom:.6rem;
}
.norma-note {
    background:#EFF6FF; border:1px solid #BFDBFE;
    border-radius:7px; padding:8px 12px;
    font-size:.78rem; color:#1E40AF; margin-top:.5rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES NORMATIVAS
# ══════════════════════════════════════════════════════════════════════════════

# Umbral mínimo absoluto para creación distrital (Tabla N°1 · B1/B2/B3)
UMBRAL_MIN = 4_800

# Rangos para el mapa y gráficos (según leyenda del mapa de referencia SSIAT)
CATEGORIAS = [
    "Menos de 500 hab.",
    "500 a 1,500 hab.",
    "1,500 a 4,800 hab.",
    "Más de 4,800 hab.",
]

# Paleta de colores — igual que el mapa de referencia
COLORES_CAT = {
    "Menos de 500 hab.":    "#6B0000",   # guinda oscuro
    "500 a 1,500 hab.":     "#C0392B",   # rojo
    "1,500 a 4,800 hab.":   "#F1948A",   # rosado
    "Más de 4,800 hab.":    "#2E75B6",   # azul SDOT
    "Sin datos":            "#CBD5E1",
}

# Tabla N°1 — DS 191-2020-PCM (creación distrital)
TABLA1 = {
    "A0":         {"distrito": 100_000, "capital": None},
    "A1":         {"distrito":  50_000, "capital": None},
    "A2_cercado": {"distrito":  20_000, "capital": None},
    "A2":         {"distrito":  20_000, "capital":  7_000},
    "A3.1":       {"distrito":  10_000, "capital":  3_500},
    "A3.2 y AB":  {"distrito":   5_000, "capital":  1_800},
    "B1, B2, B3": {"distrito":   4_800, "capital":  1_500},
}

# Tabla N°2 — RVM 005-2019-PCM (fusión/reorganización)
TABLA2 = {
    "A0":         {"distrito":  80_000, "capital": None},
    "A1":         {"distrito":  40_000, "capital": None},
    "A2_cercado": {"distrito":  16_000, "capital": None},
    "A2":         {"distrito":  16_000, "capital":  5_600},
    "A3.1":       {"distrito":   8_000, "capital":  2_800},
    "A3.2 y AB":  {"distrito":   4_000, "capital":  1_400},
    "B1, B2, B3": {"distrito":   3_800, "capital":  1_200},
}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════════════════════════════
def categorizar(pob: float) -> str:
    """Asigna categoría poblacional según leyenda del mapa de referencia."""
    if pd.isna(pob):         return "Sin datos"
    if pob < 500:            return "Menos de 500 hab."
    if pob < 1_500:          return "500 a 1,500 hab."
    if pob < UMBRAL_MIN:     return "1,500 a 4,800 hab."
    return "Más de 4,800 hab."


def color_mapa(v: float) -> str:
    return COLORES_CAT.get(categorizar(v), "#CBD5E1")


# ══════════════════════════════════════════════════════════════════════════════
# CARGA Y PREPARACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Calculando brechas normativas...")
def preparar_datos():
    df  = cargar_dataframe()
    gdf = cargar_geodataframe()

    df["CAT_2017"]   = df["POB2017"].apply(categorizar)
    df["CAT_2025"]   = df["POB2025"].apply(categorizar)
    df["BRECHA_2017"] = df["POB2017"] - UMBRAL_MIN
    df["BRECHA_2025"] = df["POB2025"] - UMBRAL_MIN
    df["CUMPLE_2017"] = df["POB2017"] >= UMBRAL_MIN
    df["CUMPLE_2025"] = df["POB2025"] >= UMBRAL_MIN

    # Merge GDF con columnas de brecha
    cols_merge = [
        "UBIGEO", "POB2017", "POB2025",
        "CAT_2017", "CAT_2025",
        "BRECHA_2017", "BRECHA_2025",
        "REGION_NAT", "TIPOLOGIA", "ANIO",
        "NOMBDEP", "NOMBPROV", "NOMBDIST",
    ]
    gdf_m = gdf[["UBIGEO", "geometry"]].merge(
        df[cols_merge], on="UBIGEO", how="left"
    )
    return df, gdf_m


df, gdf_m = preparar_datos()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — filtro único: año censal
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚖️ Filtro")
    anno = st.radio(
        "Año censal",
        ["2017 — Censo INEI", "2025 — Censo INEI"],
        index=1,
    )
    usar_2025  = anno == "2025 — Censo INEI"
    col_pob    = "POB2025"   if usar_2025 else "POB2017"
    col_cat    = "CAT_2025"  if usar_2025 else "CAT_2017"
    col_brecha = "BRECHA_2025" if usar_2025 else "BRECHA_2017"
    col_cumple = "CUMPLE_2025" if usar_2025 else "CUMPLE_2017"
    anno_label = "2025" if usar_2025 else "2017"
    anno_otro  = "2017" if usar_2025 else "2025"
    col_pob_otro    = "POB2017"   if usar_2025 else "POB2025"
    col_cat_otro    = "CAT_2017"  if usar_2025 else "CAT_2025"
    col_cumple_otro = "CUMPLE_2017" if usar_2025 else "CUMPLE_2025"

    st.markdown("---")
    st.markdown("""
    **Marco normativo**
    - Ley N.° 27795
    - TUO DS 134-2025-PCM
    - Tabla N°1 (DS 191-2020-PCM)
    - Tabla N°2 (RVM 005-2019-PCM)
    """)
    st.caption("Umbral mínimo absoluto: **4,800 hab.** (tipologías B1/B2/B3 · Tabla N°1)")


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>⚖️ Brechas normativas — Requisito poblacional mínimo</h2>
  <p>TUO DS 134-2025-PCM · Tablas N°1 y N°2 · Año censal seleccionado:
     <b>{anno_label}</b> · Umbral mínimo: <b>4,800 hab.</b> · SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
total    = len(df)
n_cumple = int(df[col_cumple].sum())
n_nc     = total - n_cumple
n_crit   = int((df[col_cat] == "Menos de 500 hab.").sum())

# Referencia del otro año para comparar
n_cumple_otro = int(df[col_cumple_otro].sum())
diff_cumple   = n_cumple - n_cumple_otro
signo         = "+" if diff_cumple >= 0 else ""

k1, k2, k3, k4 = st.columns(4)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",  "🗺️ Total distritos",
     f"{total:,}", f"Censo {anno_label} · Base INEI",  "#1E40AF"),
    (k2, "green", f"✅ Cumplen ≥ 4,800 hab.",
     f"{n_cumple:,}",
     f"{n_cumple/total*100:.1f}% · {signo}{diff_cumple} vs. {anno_otro}",
     "#166534"),
    (k3, "red",   f"❌ No cumplen < 4,800 hab.",
     f"{n_nc:,}",
     f"{n_nc/total*100:.1f}% · principalmente Sierra",
     "#991B1B"),
    (k4, "amber", "⚠️ Críticos < 500 hab.",
     f"{n_crit:,}",
     f"{n_crit/total*100:.1f}% · caso extremo",
     "#92400E"),
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
# FILA 2 — Mapa + Tabla de umbrales + Variación
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Distribución espacial — requisito poblacional mínimo</div>',
            unsafe_allow_html=True)

col_mapa, col_ref = st.columns([1.4, 1])

with col_mapa:
    # Construir mapa Folium
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

    # Pre-calcular color según año seleccionado
    gdf_plot = gdf_m.copy()
    gdf_plot["_color"] = gdf_plot[col_pob].apply(color_mapa)

    folium.GeoJson(
        gdf_plot.__geo_interface__,
        style_function=lambda feat: {
            "fillColor":   feat["properties"].get("_color", "#CBD5E1"),
            "color":       "#ffffff",
            "weight":      0.3,
            "fillOpacity": 0.85,
        },
        tooltip=folium.GeoJsonTooltip(
            fields   = ["NOMBDIST", "NOMBDEP", col_pob, col_cat,
                        col_brecha, "TIPOLOGIA", "REGION_NAT"],
            aliases  = ["Distrito", "Dpto.", f"Pob. {anno_label}",
                        "Categoría", "Brecha vs. 4,800",
                        "Tipología", "Región"],
            localize = True,
            sticky   = False,
        ),
        smooth_factor=2.0,
        embed=False,
    ).add_to(m)

    # Leyenda igual al mapa de referencia SSIAT
    leyenda_html = f"""
    <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                background:white;padding:10px 14px;border-radius:8px;
                border:1px solid #e2e8f0;font-size:11px;
                box-shadow:0 2px 5px rgba(0,0,0,.12);max-width:260px">
      <b style="font-size:11px">Distritos que NO cumplen el<br>
      requisito poblacional:</b><br>
      <span style="color:#6B0000">■</span>
        Distritos con menos de 500 hab.<br>
      <span style="color:#C0392B">■</span>
        Distritos entre 500 y 1,500 hab.<br>
      <span style="color:#F1948A">■</span>
        Distritos con más de 1,500 hab.<br>
      <b style="font-size:11px">Distritos que SÍ cumplen:</b><br>
      <span style="color:#2E75B6">■</span>
        Distritos con más de 4,800 hab.<br>
      <span style="color:#CBD5E1">■</span> Sin datos<br>
      <span style="font-size:10px;color:#64748b">
        Fuente: Censo {anno_label} · INEI</span>
    </div>"""
    m.get_root().html.add_child(folium.Element(leyenda_html))

    from streamlit_folium import st_folium
    st_folium(m, width=None, height=440, returned_objects=[])


with col_ref:
    # Tabla de umbrales
    st.markdown('<div class="section-title">Umbrales Tabla N°1 y N°2</div>',
                unsafe_allow_html=True)

    tbl_data = {
        "Tipología":    ["A0", "A1", "A2 cercado", "A2 no cerc.",
                         "A3.1", "A3.2 / AB", "B1/B2/B3"],
        "T1 · dist.":   ["100,000", "50,000", "20,000", "20,000",
                         "10,000", "5,000", "4,800"],
        "T1 · cap.":    ["—", "—", "—", "7,000",
                         "3,500", "1,800", "1,500"],
        "T2 · dist.":   ["80,000", "40,000", "16,000", "16,000",
                         "8,000", "4,000", "3,800"],
        "T2 · cap.":    ["—", "—", "—", "5,600",
                         "2,800", "1,400", "1,200"],
    }
    st.dataframe(
        pd.DataFrame(tbl_data),
        use_container_width=True,
        hide_index=True,
        height=245,
    )

    st.markdown("""
    <div class="norma-note">
      El umbral de <b>4,800 hab.</b> (T1 · B1/B2/B3) es el mínimo
      absoluto para la creación distrital y se usa como referencia
      universal en el mapa y los gráficos.
    </div>
    """, unsafe_allow_html=True)

    # Variación entre censos
    st.markdown('<div class="section-title" style="margin-top:.8rem">'
                'Variación por categoría · 2017 → 2025</div>',
                unsafe_allow_html=True)

    var_data = []
    for cat in CATEGORIAS:
        n17 = int((df["CAT_2017"] == cat).sum())
        n25 = int((df["CAT_2025"] == cat).sum())
        var_data.append({"Categoría": cat, "2017": n17, "2025": n25,
                         "Variación": n25 - n17})
    df_var = pd.DataFrame(var_data)

    def color_var(v):
        if v > 0:  return "color: #991B1B"
        if v < 0:  return "color: #166534"
        return "color: #64748b"

    st.dataframe(
        df_var.style.applymap(
            lambda v: color_var(v) if isinstance(v, int) and v != 0 else "",
            subset=["Variación"]
        ),
        use_container_width=True,
        hide_index=True,
        height=175,
    )


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Gráfico nacional + Gráfico por departamento
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Análisis por categoría poblacional</div>',
            unsafe_allow_html=True)

col_nac, col_dep = st.columns(2)

# ── Gráfico 1: Nacional 2017 vs 2025 ───────────────────────────────────────
with col_nac:
    st.markdown('<div class="section-title">Distritos por categoría — 2017 vs 2025</div>',
                unsafe_allow_html=True)

    counts_17 = df["CAT_2017"].value_counts().reindex(CATEGORIAS, fill_value=0)
    counts_25 = df["CAT_2025"].value_counts().reindex(CATEGORIAS, fill_value=0)
    colores   = [COLORES_CAT[c] for c in CATEGORIAS]

    fig_nac = go.Figure()
    fig_nac.add_trace(go.Bar(
        name="2025 (Censo INEI)",
        y=CATEGORIAS,
        x=counts_25.values,
        orientation="h",
        marker_color=colores,
        text=[f"{v:,}" for v in counts_25.values],
        textposition="outside",
        textfont_size=10,
        offsetgroup=1,
    ))
    fig_nac.add_trace(go.Bar(
        name="2017 (Censo INEI)",
        y=CATEGORIAS,
        x=counts_17.values,
        orientation="h",
        marker_color=colores,
        marker_opacity=0.5,
        text=[f"{v:,}" for v in counts_17.values],
        textposition="outside",
        textfont_size=10,
        offsetgroup=2,
    ))
    fig_nac.update_layout(
        barmode="group",
        height=290,
        margin=dict(t=10, b=10, l=10, r=70),
        xaxis=dict(title="N.° de distritos", gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10, autorange="reversed"),
        legend=dict(orientation="h", y=1.08, x=0, font_size=10),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_nac, use_container_width=True)

    pct_nc = (df[col_cat] != "Más de 4,800 hab.").sum() / total * 100
    st.caption(
        f"Censo {anno_label}: el **{pct_nc:.1f}%** de los distritos "
        f"no alcanza el umbral mínimo de 4,800 hab. establecido en "
        f"la Tabla N°1 del TUO DS 134-2025-PCM."
    )


# ── Gráfico 2: Top 12 departamentos con más incumplidores ──────────────────
with col_dep:
    st.markdown('<div class="section-title">'
                'Top 12 departamentos · distritos que no cumplen</div>',
                unsafe_allow_html=True)

    dep_g = df.groupby("NOMBDEP").agg(
        total          = ("UBIGEO", "count"),
        n_menos500     = (col_cat,  lambda x: (x == "Menos de 500 hab.").sum()),
        n_500_1500     = (col_cat,  lambda x: (x == "500 a 1,500 hab.").sum()),
        n_1500_4800    = (col_cat,  lambda x: (x == "1,500 a 4,800 hab.").sum()),
    ).reset_index()
    dep_g["n_inc"] = dep_g["n_menos500"] + dep_g["n_500_1500"] + dep_g["n_1500_4800"]
    dep_g = dep_g.sort_values("n_inc", ascending=True).tail(12)

    fig_dep = go.Figure()
    for col_n, cat_label, color_bar in [
        ("n_menos500",  "< 500 hab.",       "#6B0000"),
        ("n_500_1500",  "500–1,500 hab.",   "#C0392B"),
        ("n_1500_4800", "1,500–4,800 hab.", "#F1948A"),
    ]:
        fig_dep.add_trace(go.Bar(
            name=cat_label,
            y=dep_g["NOMBDEP"],
            x=dep_g[col_n],
            orientation="h",
            marker_color=color_bar,
        ))

    fig_dep.update_layout(
        barmode="stack",
        height=340,
        margin=dict(t=10, b=10, l=10, r=20),
        xaxis=dict(title="N.° de distritos", gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10),
        legend=dict(orientation="h", y=1.05, x=0, font_size=10),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_dep, use_container_width=True)
    st.caption(f"Censo {anno_label} · Ancash, Lima y Ayacucho concentran "
               "el mayor número de distritos que no alcanzan el umbral mínimo.")


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4 — Tabla detalle
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">'
            'Detalle por distrito — categoría y brecha respecto al umbral mínimo</div>',
            unsafe_allow_html=True)

cols_tabla = [
    "UBIGEO", "NOMBDEP", "NOMBPROV", "NOMBDIST",
    "REGION_NAT", "TIPOLOGIA",
    "POB2017", "CAT_2017",
    "POB2025", "CAT_2025",
    col_brecha,
]
cols_tabla = [c for c in cols_tabla if c in df.columns]

tabla = df[cols_tabla].rename(columns={
    "NOMBDEP":     "Departamento",
    "NOMBPROV":    "Provincia",
    "NOMBDIST":    "Distrito",
    "REGION_NAT":  "Región",
    "TIPOLOGIA":   "Tipología",
    "POB2017":     "Pob. 2017",
    "CAT_2017":    "Categoría 2017",
    "POB2025":     "Pob. 2025",
    "CAT_2025":    "Categoría 2025",
    col_brecha:    f"Brecha vs. 4,800 ({anno_label})",
})

# Filtros rápidos
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    busqueda = st.text_input(
        "", placeholder="🔍 Buscar por ubigeo, nombre de distrito o departamento",
        label_visibility="collapsed",
    )
with col_f2:
    cat_sel = st.selectbox(
        "Filtrar por categoría",
        ["Todas"] + CATEGORIAS,
        label_visibility="collapsed",
    )

# Aplicar filtros
if busqueda:
    mask = (
        tabla["Distrito"].str.contains(busqueda.upper(), na=False) |
        tabla["Departamento"].str.contains(busqueda.upper(), na=False) |
        tabla["UBIGEO"].astype(str).str.contains(busqueda, na=False)
    )
    tabla = tabla[mask]

col_cat_tabla = f"Categoría {anno_label}"
if cat_sel != "Todas" and col_cat_tabla in tabla.columns:
    tabla = tabla[tabla[col_cat_tabla] == cat_sel]

tabla_sorted = tabla.sort_values(
    f"Brecha vs. 4,800 ({anno_label})", ascending=True
)

st.dataframe(
    tabla_sorted,
    use_container_width=True,
    height=300,
    hide_index=True,
)

csv = tabla_sorted.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label=f"⬇️ Descargar tabla — Censo {anno_label} (CSV)",
    data=csv,
    file_name=f"brechas_normativas_censo{anno_label}.csv",
    mime="text/csv",
)

# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Marco normativo: Ley N.° 27795 · TUO DS 134-2025-PCM · Art. 14 · "
    "Tabla N°1 (DS 191-2020-PCM) · Tabla N°2 (RVM 005-2019-PCM) · "
    "Datos: INEI Censos 2017 y 2025 · Elaborado por SSIAT · SDOT-PCM · 2026"
)
