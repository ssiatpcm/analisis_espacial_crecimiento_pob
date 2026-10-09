"""
pages/03_brechas_normativas.py
Página 3 — Brechas normativas · TUO DS 134-2025-PCM
Requisito poblacional mínimo · Tablas N°1 y N°2
SSIAT / SDOT-PCM · 2026
"""

import warnings
warnings.filterwarnings("ignore")
import io

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from utils.carga_datos import cargar_dataframe, cargar_geodataframe, cargar_capitales
from utils.rendimiento import geojson_liviano, a_excel, a_csv, capa_puntos

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
UMBRAL_MIN = 4_800

CATEGORIAS = [
    "Menos de 500 hab.",
    "500 a 1,500 hab.",
    "1,500 a 4,800 hab.",
    "Más de 4,800 hab.",
]

COLORES_CAT = {
    "Menos de 500 hab.":    "#6B0000",
    "500 a 1,500 hab.":     "#C0392B",
    "1,500 a 4,800 hab.":   "#F1948A",
    "Más de 4,800 hab.":    "#2E75B6",
    "Sin datos":            "#CBD5E1",
}

COLORES_2025 = {
    "Menos de 500 hab.":    "#6B0000",
    "500 a 1,500 hab.":     "#C0392B",
    "1,500 a 4,800 hab.":   "#F1948A",
    "Más de 4,800 hab.":    "#2E75B6",
}
COLORES_2017 = {
    "Menos de 500 hab.":    "#A04040",
    "500 a 1,500 hab.":     "#E07070",
    "1,500 a 4,800 hab.":   "#F8C0B0",
    "Más de 4,800 hab.":    "#7AAED6",
}


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════════════════════════════
def categorizar(pob: float) -> str:
    if pd.isna(pob):     return "Sin datos"
    if pob < 500:        return "Menos de 500 hab."
    if pob < 1_500:      return "500 a 1,500 hab."
    if pob < UMBRAL_MIN: return "1,500 a 4,800 hab."
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

    df["CAT_2017"]    = df["POB2017"].apply(categorizar)
    df["CAT_2025"]    = df["POB2025"].apply(categorizar)
    df["BRECHA_2017"] = df["POB2017"] - UMBRAL_MIN
    df["BRECHA_2025"] = df["POB2025"] - UMBRAL_MIN
    df["CUMPLE_2017"] = df["POB2017"] >= UMBRAL_MIN
    df["CUMPLE_2025"] = df["POB2025"] >= UMBRAL_MIN

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
# FIX: comparar anno == "2025" (el radio devuelve exactamente el string del label)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚖️ Filtro")
    anno = st.radio(
        "Año censal",
        ["2017", "2025"],
        index=1,
    )
    # ── CORRECCIÓN CLAVE: anno es "2017" o "2025", no contiene texto extra ──
    usar_2025       = (anno == "2025")
    col_pob         = "POB2025"     if usar_2025 else "POB2017"
    col_cat         = "CAT_2025"    if usar_2025 else "CAT_2017"
    col_brecha      = "BRECHA_2025" if usar_2025 else "BRECHA_2017"
    col_cumple      = "CUMPLE_2025" if usar_2025 else "CUMPLE_2017"
    anno_label      = "2025"        if usar_2025 else "2017"
    anno_otro       = "2017"        if usar_2025 else "2025"
    col_pob_otro    = "POB2017"     if usar_2025 else "POB2025"
    col_cat_otro    = "CAT_2017"    if usar_2025 else "CAT_2025"
    col_cumple_otro = "CUMPLE_2017" if usar_2025 else "CUMPLE_2025"
    # Total de distritos varía según censo
    total_censo     = 1892          if usar_2025 else 1874

    st.markdown("---")
    st.markdown("""
    **Marco normativo**
    - Ley N.° 27795, Ley de Demarcación y Organización Territorial
    - D.S. N° 134-2025-PCM, que aprueba el TUO del Reglamento de la Ley N.° 27795, aprobado por D.S. N° 191-2020-PCM
    """)
    st.caption("Umbral mínimo absoluto: **4,800 hab.** (Tabla N°1)")


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>⚖️ Brechas normativas — Requisito poblacional mínimo</h2>
  <p>Tablas N° 1 y N° 2 del Anexo del Reglamento de la Ley N° 27795 · Año censal:
     <b>{anno_label}</b> · Umbral mínimo: <b>4,800 hab.</b> · SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs  (todos reactivos al año censal)
# ══════════════════════════════════════════════════════════════════════════════
# Filtrar df al universo correcto según censo
# NOTA: ANIO = año de creación del distrito (solo tienen valor los creados
# post-2002). Los 1,828 distritos preexistentes tienen ANIO = NaN.
# Universo 2017 = distritos con ANIO nulo (pre-2002) + creados hasta 2017
# Universo 2025 = todos los 1,892 distritos
if usar_2025:
    df_censo = df.copy()           # 1,892 distritos
else:
    df_censo = df[df["ANIO"].isna() | (df["ANIO"] <= 2017)].copy()  # 1,874

total    = len(df_censo)
n_cumple = int(df_censo[col_cumple].sum())
n_nc     = total - n_cumple
n_crit   = int((df_censo[col_cat] == "Menos de 500 hab.").sum())

# Referencia del otro año (sobre el mismo universo df completo para comparar)
n_cumple_otro = int(df[col_cumple_otro].sum())
diff_cumple   = n_cumple - n_cumple_otro
signo         = "+" if diff_cumple >= 0 else ""

k1, k2, k3, k4 = st.columns(4)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",  "🗺️ Total distritos",
     f"{total_censo:,}",
     f"Base Censo INEI {anno_label}", "#1E40AF"),
    (k2, "green", "✅ Cumplen ≥ 4,800 hab.",
     f"{n_cumple:,}",
     f"{n_cumple/total*100:.1f}% · {signo}{diff_cumple} vs. {anno_otro}",
     "#166534"),
    (k3, "red",   "❌ No cumplen < 4,800 hab.",
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
# FILA 2 — Mapa + Tablas de umbrales
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">Distribución espacial — requisito poblacional mínimo</div>',
            unsafe_allow_html=True)

col_mapa, col_ref = st.columns([1.4, 1])

with col_mapa:
    from streamlit_folium import st_folium

    tab_dist, tab_cap = st.tabs([
        "Distritos — umbral mínimo",
        "Capitales — umbral mínimo",
    ])

    def base_map():
        m = folium.Map(location=[-9.5, -75.5], zoom_start=5,
                       tiles=None, prefer_canvas=True)
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            name="OpenStreetMap", max_zoom=19,
        ).add_to(m)
        return m

    # ── Tab 1: Mapa distritos ───────────────────────────────────────────────
    with tab_dist:
        m = base_map()
        gdf_plot = gdf_m.copy()
        gdf_plot["_color"] = gdf_plot[col_pob].apply(color_mapa)

        # Tooltip muestra POB del año seleccionado
        campos_tooltip = ["NOMBDIST", "NOMBDEP", col_pob, col_cat,
                          col_brecha, "TIPOLOGIA", "REGION_NAT"]
        folium.GeoJson(
            geojson_liviano(gdf_plot, campos_tooltip + ["_color"]),
            style_function=lambda feat: {
                "fillColor":   feat["properties"].get("_color", "#CBD5E1"),
                "color":       "#ffffff",
                "weight":      0.3,
                "fillOpacity": 0.85,
            },
            tooltip=folium.GeoJsonTooltip(
                fields   = campos_tooltip,
                aliases  = ["Distrito", "Dpto.",
                            f"Pob. {anno_label}",   # dinámico según año
                            "Categoría", "Brecha vs. 4,800",
                            "Tipología", "Región"],
                localize = True, sticky = False,
            ),
            smooth_factor=2.0, embed=False,
        ).add_to(m)

        leyenda_dist = f"""
        <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                    background:white;padding:10px 14px;border-radius:8px;
                    border:1px solid #e2e8f0;font-size:11px;
                    box-shadow:0 2px 5px rgba(0,0,0,.12);max-width:260px">
          <b>Distritos que NO cumplen:</b><br>
          <span style="color:#6B0000">&#9632;</span> Menos de 500 hab.<br>
          <span style="color:#C0392B">&#9632;</span> 500 a 1,500 hab.<br>
          <span style="color:#F1948A">&#9632;</span> 1,500 a 4,800 hab.<br>
          <b>Distritos que SÍ cumplen:</b><br>
          <span style="color:#2E75B6">&#9632;</span> Más de 4,800 hab.<br>
          <span style="color:#CBD5E1">&#9632;</span> Sin datos<br>
          <span style="font-size:10px;color:#64748b">Censo {anno_label} · INEI</span>
        </div>"""
        m.get_root().html.add_child(folium.Element(leyenda_dist))
        st_folium(m, width=None, height=420, returned_objects=[])

    # ── Tab 2: Mapa capitales ───────────────────────────────────────────────
    with tab_cap:
        df_cap_map = cargar_capitales()
        # POB de capital según año seleccionado
        col_pob_cap_map = "POB2025" if usar_2025 else "POB2017"

        COLORES_CAP = {
            "Menos de 250 hab.":  "#6B0000",
            "250 a 750 hab.":     "#C0392B",
            "750 a 1,500 hab.":   "#F1948A",
            "Más de 1,500 hab.":  "#2E75B6",
            "Sin datos":          "#CBD5E1",
        }

        def cat_cap(pob):
            if pd.isna(pob): return "Sin datos"
            if pob < 250:    return "Menos de 250 hab."
            if pob < 750:    return "250 a 750 hab."
            if pob < 1500:   return "750 a 1,500 hab."
            return "Más de 1,500 hab."

        m2 = base_map()
        pob_max_cap = df_cap_map[col_pob_cap_map].replace(0, np.nan).max()
        colores, radios, tooltips = [], [], []

        for _, row in df_cap_map.iterrows():
            pob_v = row.get(col_pob_cap_map)
            pob_v = 50 if (pob_v is None or pd.isna(pob_v)) else pob_v
            radius = max(3, min(16, 3 + 13 * (pob_v / pob_max_cap) ** 0.4))
            cat_v  = cat_cap(pob_v)
            color  = COLORES_CAP.get(cat_v, "#CBD5E1")
            tooltip_cap = (
                f"<b>{row['NOMBCCPP']}</b><br>"
                f"{row['NOMBDIST']} — {row['NOMBDEP']}<br>"
                f"Pob. {anno_label}: {int(pob_v):,}<br>"   # dinámico
                f"Categoría: {cat_v}"
            )
            colores.append(color)
            radios.append(radius)
            tooltips.append(tooltip_cap)

        # Una sola capa con todos los puntos (mucho más rápida que un
        # CircleMarker por capital)
        pts = df_cap_map[["X", "Y"]].assign(_c=colores, _r=radios, _t=tooltips)
        capa_puntos(m2, pts, "X", "Y", "_c", "_r", "_t")

        leyenda_cap = f"""
        <div style="position:fixed;bottom:14px;left:14px;z-index:1000;
                    background:white;padding:10px 14px;border-radius:8px;
                    border:1px solid #e2e8f0;font-size:11px;
                    box-shadow:0 2px 5px rgba(0,0,0,.12);max-width:270px">
          <b>Capitales que NO cumplen (umbral 1,500 hab.):</b><br>
          <span style="color:#6B0000">&#9679;</span> Menos de 250 hab.<br>
          <span style="color:#C0392B">&#9679;</span> 250 a 750 hab.<br>
          <span style="color:#F1948A">&#9679;</span> 750 a 1,500 hab.<br>
          <b>Capitales que SÍ cumplen:</b><br>
          <span style="color:#2E75B6">&#9679;</span> Más de 1,500 hab.<br>
          <span style="color:#CBD5E1">&#9679;</span> Sin datos<br>
          <span style="font-size:10px;color:#64748b">Tamaño ∝ Pob. · Censo {anno_label} · INEI</span>
        </div>"""
        m2.get_root().html.add_child(folium.Element(leyenda_cap))
        st_folium(m2, width=None, height=420, returned_objects=[])


with col_ref:
    # ── Tablas N°1 y N°2 sin columna Área geográfica ───────────────────────
    st.markdown('<div class="section-title">Umbrales normativos</div>',
                unsafe_allow_html=True)

    tab_t1, tab_t2 = st.tabs([
        "Tabla N°1",
        "Tabla N°2",
    ])

    with tab_t1:
        st.caption("Elaborado sobre la base de la Tipología de Distritos aprobada por Resolución Viceministerial N° 005-2019-PCM/DVGT")
        tbl1 = {
            "Tipología de distritos": ["A0", "A1", "A2 (distrito cercado)", "A2 (distrito no cercado)",
                          "A3.1", "A3.2 y AB", "B1, B2, B3"],
            "Pob. mín. distrito":
                ["100,000", "50,000", "20,000", "20,000",
                 "10,000", "5,000", "4,800"],
            "Pob. mín. capital":
                ["No aplica", "No aplica", "No aplica", "7,000",
                 "3,500", "1,800", "1,500"],
        }
        st.dataframe(pd.DataFrame(tbl1),
                     width="stretch", hide_index=True, height=262)
        st.markdown("""
        <div class="norma-note">
          El umbral de <b>4,800 hab.</b> (distrito) y <b>1,500 hab.</b> (capital)
          para tipologías B1/B2/B3 es el mínimo absoluto y se usa como
          referencia universal en el mapa y los gráficos.
        </div>""", unsafe_allow_html=True)

    with tab_t2:
        st.caption("Elaborado sobre la base de la Tipología de Distritos aprobada por Resolución Viceministerial N° 005-2019-PCM/DVGT")
        tbl2 = {
            "Tipología de distritos": ["A0", "A1", "A2 (distrito cercado)", "A2 (distrito no cercado)",
                          "A3.1", "A3.2 y AB", "B1, B2, B3"],
            "Pob. mín. distrito":
                ["80,000", "40,000", "16,000", "16,000",
                 "8,000", "4,000", "3,800"],
            "Pob. mín. capital":
                ["No aplica", "No aplica", "No aplica", "5,600",
                 "2,800", "1,400", "1,200"],
        }
        st.dataframe(pd.DataFrame(tbl2),
                     width="stretch", hide_index=True, height=262)
        st.markdown("""
        <div class="norma-note">
          El umbral de <b>3,800 hab.</b> (distrito) y <b>1,200 hab.</b> (capital)
          para tipologías B1/B2/B3 es el mínimo absoluto en la Tabla N° 2.
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Gráfico nacional + Gráfico por departamento
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Análisis por volumen poblacional</div>',
            unsafe_allow_html=True)

col_nac, col_dep = st.columns(2)

with col_nac:
    st.markdown('<div class="section-title">Distritos por rango de volumen poblacional, según 2017 y 2025</div>',
                unsafe_allow_html=True)

    counts_17 = df["CAT_2017"].value_counts().reindex(CATEGORIAS, fill_value=0)
    counts_25 = df["CAT_2025"].value_counts().reindex(CATEGORIAS, fill_value=0)

    fig_nac = go.Figure()
    fig_nac.add_trace(go.Bar(
        name="2025",
        y=CATEGORIAS,
        x=counts_25.values,
        orientation="h",
        marker_color=[COLORES_2025[c] for c in CATEGORIAS],
        text=[f"{v:,}" for v in counts_25.values],
        textposition="outside",
        textfont_size=10,
        offsetgroup=1,
    ))
    fig_nac.add_trace(go.Bar(
        name="2017",
        y=CATEGORIAS,
        x=counts_17.values,
        orientation="h",
        marker_color=[COLORES_2017[c] for c in CATEGORIAS],
        text=[f"{v:,}" for v in counts_17.values],
        textposition="outside",
        textfont_size=10,
        offsetgroup=2,
    ))
    fig_nac.update_layout(
        barmode="group",
        height=310,
        margin=dict(t=10, b=10, l=10, r=150),
        xaxis=dict(title="N.° de distritos", gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10, autorange="reversed"),
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            xanchor="left", yanchor="middle",
            font_size=10,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e2e8f0",
            borderwidth=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_nac, width="stretch")

    pct_nc = (df_censo[col_cat] != "Más de 4,800 hab.").sum() / total * 100
    st.caption(
        f"Censo {anno_label}: el **{pct_nc:.1f}%** de los distritos "
        f"no alcanza el umbral mínimo de 4,800 hab. "
        f"(Tabla N°1, Anexo del Reglamento de la Ley N° 27795)."
    )


with col_dep:
    st.markdown('<div class="section-title">'
                f'Top 12 departamentos · distritos que no cumplen — Censo {anno_label}</div>',
                unsafe_allow_html=True)

    dep_g = df_censo.groupby("NOMBDEP").agg(
        total       = ("UBIGEO", "count"),
        n_menos500  = (col_cat, lambda x: (x == "Menos de 500 hab.").sum()),
        n_500_1500  = (col_cat, lambda x: (x == "500 a 1,500 hab.").sum()),
        n_1500_4800 = (col_cat, lambda x: (x == "1,500 a 4,800 hab.").sum()),
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
        margin=dict(t=10, b=10, l=10, r=130),
        xaxis=dict(title="N.° de distritos", gridcolor="#f1f5f9", tickfont_size=9),
        yaxis=dict(tickfont_size=10),
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            xanchor="left", yanchor="middle",
            font_size=10,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e2e8f0",
            borderwidth=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_dep, width="stretch")
    st.caption(
        f"Censo {anno_label} · Ancash, Lima y Ayacucho concentran "
        "el mayor número de distritos que no alcanzan el umbral mínimo poblacional."
    )


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4 — Tabla detalle
# ══════════════════════════════════════════════════════════════════════════════
# st.fragment: al usar estos filtros solo se re-ejecuta esta sección;
# los mapas no se reconstruyen ni se reenvían al navegador.
@st.fragment
def seccion_tabla():
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
    cols_tabla = [c for c in cols_tabla if c in df_censo.columns]

    tabla = df_censo[cols_tabla].rename(columns={
        "NOMBDEP":   "Departamento",
        "NOMBPROV":  "Provincia",
        "NOMBDIST":  "Distrito",
        "REGION_NAT": "Región",
        "TIPOLOGIA": "Tipología",
        "POB2017":   "Pob. 2017",
        "CAT_2017":  "Categoría 2017",
        "POB2025":   "Pob. 2025",
        "CAT_2025":  "Categoría 2025",
        col_brecha:  f"Brecha vs. 4,800 ({anno_label})",
    })

    cc1, cc2, cc3, cc4 = st.columns([1, 1, 1, 1])

    with cc1:
        st.markdown('<div class="section-title">Departamento</div>',
                    unsafe_allow_html=True)
        lista_dep = ["Todos"] + sorted(tabla["Departamento"].dropna().unique().tolist())
        dep_sel = st.selectbox("Departamento", lista_dep, index=0,
                               key="dep_sel_p3", label_visibility="collapsed")
    with cc2:
        st.markdown('<div class="section-title">Provincia</div>',
                    unsafe_allow_html=True)
        if dep_sel != "Todos":
            provs = sorted(tabla[tabla["Departamento"] == dep_sel]["Provincia"]
                           .dropna().unique().tolist())
        else:
            provs = sorted(tabla["Provincia"].dropna().unique().tolist())
        lista_prov = ["Todas"] + provs
        prov_sel = st.selectbox("Provincia", lista_prov, index=0,
                                key="prov_sel_p3", label_visibility="collapsed")
    with cc3:
        st.markdown('<div class="section-title">Distrito</div>',
                    unsafe_allow_html=True)
        mask_d = pd.Series([True] * len(tabla), index=tabla.index)
        if dep_sel  != "Todos":  mask_d &= tabla["Departamento"] == dep_sel
        if prov_sel != "Todas":  mask_d &= tabla["Provincia"]    == prov_sel
        dists      = sorted(tabla[mask_d]["Distrito"].dropna().unique().tolist())
        lista_dist = ["Todos"] + dists
        dist_sel = st.selectbox("Distrito", lista_dist, index=0,
                                key="dist_sel_p3", label_visibility="collapsed")
    with cc4:
        st.markdown('<div class="section-title">Categoría poblacional</div>',
                    unsafe_allow_html=True)
        cat_sel = st.selectbox(
            "Categoría", ["Todas"] + CATEGORIAS, index=0,
            key="cat_sel_p3", label_visibility="collapsed",
        )

    # Aplicar filtros
    if dep_sel  != "Todos":  tabla = tabla[tabla["Departamento"] == dep_sel]
    if prov_sel != "Todas":  tabla = tabla[tabla["Provincia"]    == prov_sel]
    if dist_sel != "Todos":  tabla = tabla[tabla["Distrito"]     == dist_sel]

    col_cat_tabla = f"Categoría {anno_label}"
    if cat_sel != "Todas" and col_cat_tabla in tabla.columns:
        tabla = tabla[tabla[col_cat_tabla] == cat_sel]

    tabla_sorted = tabla.sort_values(
        f"Brecha vs. 4,800 ({anno_label})", ascending=True
    )

    st.dataframe(
        tabla_sorted,
        width="stretch",
        height=300,
        hide_index=True,
    )

    dl1, dl2 = st.columns(2)
    with dl1:
        csv = a_csv(tabla_sorted)
        st.download_button(
            label=f"⬇️ Descargar CSV — Censo {anno_label}",
            data=csv,
            file_name=f"brechas_normativas_censo{anno_label}.csv",
            mime="text/csv",
        )
    with dl2:
        st.download_button(
            label=f"⬇️ Descargar Excel — Censo {anno_label}",
            data=a_excel(tabla_sorted, f"Brechas_{anno_label}"),
            file_name=f"brechas_normativas_censo{anno_label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


seccion_tabla()


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Fuente: INEI — Censos Nacionales 2017 y 2025 · "
    "Tipología de Distritos SDOT-PCM 2025 · Elaborado por SSIAT · SDOT-PCM · 2026"
)
