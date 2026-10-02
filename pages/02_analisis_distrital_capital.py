"""
pages/02_analisis_distrital_capital.py
Página 2 — Análisis territorial: Distrito y Capital Distrital
Tablero de Análisis Espacial de Crecimiento Poblacional · SSIAT / SDOT-PCM
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

# Etiqueta legible del tipo de capital
df_cap["TIPO_CAPITAL"] = df_cap["CAPITAL"].map({
    1: "Capital departamental",
    2: "Capital provincial",
    3: "Capital distrital",
})


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — solo filtro de período
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔍 Filtros")
    periodo = st.radio("Período de análisis",
                       ["2007 – 2017", "2017 – 2025"], index=0)
    usar_0717    = periodo == "2007 – 2017"
    col_tcm_dist = "TC_07_17"      if usar_0717 else "TC_17_25"
    col_tcm_cap  = "TASA_0717"     if usar_0717 else "TASA_1725"
    col_dinamica = "DINAMICA_0717" if usar_0717 else "DINAMICA_1725"
    st.markdown("---")
    st.caption("Fuentes: INEI 2007, 2017, 2025 · SSIAT 2026")

# Sin filtros de región ni tipo — dataset completo
dff = df_cap.copy()


# ══════════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="header-banner">
  <h2>📍 Análisis territorial — Distrito y Capital Distrital</h2>
  <p>Período: <b>{periodo}</b> &nbsp;·&nbsp;
     Capitales analizadas: <b>{len(dff):,}</b> &nbsp;·&nbsp;
     SSIAT / SDOT-PCM · 2026</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILA 1 — KPIs
# ══════════════════════════════════════════════════════════════════════════════
total        = len(dff)
n_cap_crec   = int((dff[col_tcm_cap] > 0).sum())
n_cap_decrec = int((dff[col_tcm_cap] < 0).sum())
n_doble_cap  = int(((dff["TASA_0717"] < 0) & (dff["TASA_1725"] < 0)).sum())
n_suburban   = int((dff[col_dinamica] == "Capital crece / Distrito decrece").sum())

k1, k2, k3, k4, k5 = st.columns(5)
for col_st, cls, label, valor, sub, color in [
    (k1, "blue",   "🗺️ Distritos / capitales",
     f"{total:,}", "Base INEI 2025", "#1E40AF"),
    (k2, "green",  "📈 Capitales que crecen",
     f"{n_cap_crec:,}",
     f"{n_cap_crec/total*100:.1f}% del total", "#166534"),
    (k3, "red",    "📉 Capitales que decrecen",
     f"{n_cap_decrec:,}",
     f"{n_cap_decrec/total*100:.1f}% del total", "#991B1B"),
    (k4, "amber",  "⚠️ Doble decrecimiento",
     f"{n_doble_cap:,}",
     "Capital Y distrito decrecen", "#92400E"),
    (k5, "purple", "🏘️ Suburbanización",
     f"{n_suburban:,}",
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

# ── Dinámica capital vs. distrito ──────────────────────────────────────────
with col_izq:
    st.markdown('<div class="section-title">Dinámica capital vs. distrito</div>',
                unsafe_allow_html=True)

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


# ── Mapa de capitales ───────────────────────────────────────────────────────
with col_mapa:
    st.markdown('<div class="section-title">Mapa de capitales distritales</div>',
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

    col_pob_cap   = "POB2017" if usar_0717 else "POB2025"
    label_pob_cap = "Pob. 2017" if usar_0717 else "Pob. 2025"

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

        pob_max = dff_map[col_pob_cap].replace(0, np.nan).max()

        for _, row in dff_map.iterrows():
            pob = row.get(col_pob_cap)
            pob = 100 if (pob is None or pd.isna(pob)) else pob
            radius = max(3, min(18, 3 + 15 * (pob / pob_max) ** 0.4))

            if mode == "tcm":
                color = color_tcm_cap(row[col_tcm_cap])
                _val  = row.get(col_pob_cap)
                pob_m = pob if (_val is None or pd.isna(_val)) else _val
                tooltip_txt = (
                    f"<b>{row['NOMBCCPP']}</b><br>"
                    f"{row['NOMBDIST']} — {row['NOMBDEP']}<br>"
                    f"TCM capital ({periodo}): <b>{row[col_tcm_cap]:.2f}%</b><br>"
                    f"{label_pob_cap}: {int(pob_m):,}<br>"
                    f"Región: {row.get('REGION_NAT','')}"
                )
            else:
                din   = row.get(col_dinamica, "Sin datos")
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
                color="#ffffff", weight=0.5,
                fill=True, fill_color=color, fill_opacity=0.85,
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
          <i>Tamaño ∝ Pob.</i>
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
          <i>Tamaño ∝ Pob.</i>
        </div>"""
        m_din.get_root().html.add_child(folium.Element(legend_din))
        st_folium(m_din, width=None, height=420, returned_objects=[])


# ══════════════════════════════════════════════════════════════════════════════
# FILA 3 — Gráfico capitales por tipo + distribución tamaño
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
col_graf1, col_graf2 = st.columns([1.4, 1])

# ── Gráfico: capitales por tipo (dpto/prov/dist) que crecen o decrecen ─────
with col_graf1:
    tab_tipo, tab_dep = st.tabs([
        "Por tipo de capital",
        "Por departamento",
    ])

    # Datos para ambos tabs
    tipo_stats = dff.groupby("TIPO_CAPITAL").agg(
        crece   = (col_tcm_cap, lambda x: (x > 0).sum()),
        decrece = (col_tcm_cap, lambda x: (x < 0).sum()),
        total   = ("UBIGEO", "count"),
    ).reset_index()

    ORDEN_TIPO = ["Capital departamental", "Capital provincial", "Capital distrital"]
    tipo_stats = tipo_stats.set_index("TIPO_CAPITAL").reindex(ORDEN_TIPO).reset_index()

    with tab_tipo:
        st.markdown(
            '<div class="section-title">'
            'Capitales departamentales, provinciales y distritales '
            f'· crecimiento/decrecimiento ({periodo})</div>',
            unsafe_allow_html=True,
        )
        fig_tipo = go.Figure()
        fig_tipo.add_trace(go.Bar(
            name="Crecen",
            x=tipo_stats["TIPO_CAPITAL"],
            y=tipo_stats["crece"],
            marker_color="#10B981",
            text=tipo_stats["crece"],
            textposition="outside", textfont_size=11,
        ))
        fig_tipo.add_trace(go.Bar(
            name="Decrecen",
            x=tipo_stats["TIPO_CAPITAL"],
            y=tipo_stats["decrece"],
            marker_color="#EF4444",
            text=tipo_stats["decrece"],
            textposition="outside", textfont_size=11,
        ))
        fig_tipo.update_layout(
            barmode="group",
            height=280,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_tickfont_size=11,
            yaxis=dict(title="N.° de capitales", gridcolor="#f1f5f9",
                       tickfont_size=9),
            legend=dict(orientation="h", y=1.08, x=0, font_size=10),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_tipo, use_container_width=True)
        st.caption(
            f"Período {periodo} · "
            f"Capitales departamentales: "
            f"{int(tipo_stats.loc[tipo_stats['TIPO_CAPITAL']=='Capital departamental','crece'].values[0])} crecen / "
            f"{int(tipo_stats.loc[tipo_stats['TIPO_CAPITAL']=='Capital departamental','decrece'].values[0])} decrecen."
        )

    with tab_dep:
        st.markdown(
            '<div class="section-title">'
            f'Capitales por departamento · crecimiento/decrecimiento ({periodo})</div>',
            unsafe_allow_html=True,
        )
        tipo_sel = st.selectbox(
            "Tipo de capital",
            ["Todas"] + ORDEN_TIPO,
            key="tipo_dep_sel",
            label_visibility="collapsed",
        )

        dep_data = dff.copy()
        if tipo_sel != "Todas":
            dep_data = dep_data[dep_data["TIPO_CAPITAL"] == tipo_sel]

        dep_stats = dep_data.groupby("NOMBDEP").agg(
            crece   = (col_tcm_cap, lambda x: (x > 0).sum()),
            decrece = (col_tcm_cap, lambda x: (x < 0).sum()),
        ).reset_index().sort_values("decrece", ascending=True)

        fig_dep = go.Figure()
        fig_dep.add_trace(go.Bar(
            name="Decrecen",
            y=dep_stats["NOMBDEP"],
            x=dep_stats["decrece"],
            orientation="h",
            marker_color="#EF4444",
        ))
        fig_dep.add_trace(go.Bar(
            name="Crecen",
            y=dep_stats["NOMBDEP"],
            x=dep_stats["crece"],
            orientation="h",
            marker_color="#10B981",
        ))
        fig_dep.update_layout(
            barmode="stack",
            height=520,
            margin=dict(t=10, b=10, l=130, r=20),
            xaxis=dict(title="N.° de capitales", gridcolor="#f1f5f9",
                       tickfont_size=9),
            yaxis=dict(tickfont_size=10),
            legend=dict(orientation="h", y=1.03, x=0, font_size=10),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_dep, use_container_width=True)


# ── Distribución por tamaño de capital ────────────────────────────────────
with col_graf2:
    st.markdown('<div class="section-title">'
                'Capitales por tamaño de población (2017)</div>',
                unsafe_allow_html=True)

    from utils.carga_datos import LABELS_POB
    dist_rango  = dff["RANGO_POB"].value_counts().reindex(LABELS_POB, fill_value=0)
    total_rango = dist_rango.sum()

    fig_hist = go.Figure(go.Bar(
        y=dist_rango.index.tolist(),
        x=dist_rango.values,
        orientation="h",
        marker_color="#2E75B6",
        text=[f"{v:,}  ({v/total_rango*100:.0f}%)"
              for v in dist_rango.values],
        textposition="outside", textfont_size=10,
    ))
    fig_hist.update_layout(
        height=290,
        margin=dict(t=10, b=10, l=10, r=90),
        xaxis=dict(title="N.° de capitales", gridcolor="#f1f5f9",
                   tickfont_size=9),
        yaxis=dict(tickfont_size=10, autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    pct_peq = (dist_rango["< 500"] + dist_rango["500–2k"]) / total_rango * 100
    st.caption(
        f"El **{pct_peq:.0f}%** de las capitales tiene menos de 2,000 hab. "
        "— relevante para umbrales Art. 14 TUO DS 134-2025-PCM."
    )


# ══════════════════════════════════════════════════════════════════════════════
# FILA 4 — Tabla integrada con cascada + descargas
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">Tabla integrada — distrito y capital</div>',
            unsafe_allow_html=True)

# Construir tabla base
cols_tabla = [c for c in [
    "UBIGEO", "NOMBDEP", "NOMBPROV", "NOMBDIST", "NOMBCCPP",
    "REGION_NAT", "TIPOLOGIA", "TIPO_CAPITAL",
    col_tcm_dist, col_tcm_cap,
    "POB2017", "POB2025",
    col_dinamica, "RANGO_POB",
] if c in dff.columns]

tabla_base = dff[cols_tabla].rename(columns={
    "NOMBDEP":    "Departamento",
    "NOMBPROV":   "Provincia",
    "NOMBDIST":   "Distrito",
    "NOMBCCPP":   "Capital",
    "REGION_NAT": "Región",
    "TIPOLOGIA":  "Tipología",
    "TIPO_CAPITAL": "Tipo capital",
    col_tcm_dist: "TCM distrito (%)",
    col_tcm_cap:  "TCM capital (%)",
    "POB2017":    "Pob. cap. 2017",
    "POB2025":    "Pob. cap. 2025",
    col_dinamica: "Dinámica",
    "RANGO_POB":  "Tamaño capital",
})

# ── Menú en cascada: Departamento → Provincia → Distrito ───────────────────
c1, c2, c3 = st.columns(3)

with c1:
    lista_dep = ["Todos"] + sorted(
        tabla_base["Departamento"].dropna().unique().tolist()
    )
    dep_sel = st.selectbox("Departamento", lista_dep, index=0,
                           key="dep_sel_p2")

with c2:
    if dep_sel != "Todos":
        provs = sorted(
            tabla_base[tabla_base["Departamento"] == dep_sel]["Provincia"]
            .dropna().unique().tolist()
        )
    else:
        provs = sorted(tabla_base["Provincia"].dropna().unique().tolist())
    lista_prov = ["Todas"] + provs
    prov_sel = st.selectbox("Provincia", lista_prov, index=0,
                            key="prov_sel_p2")

with c3:
    mask_d = pd.Series([True] * len(tabla_base), index=tabla_base.index)
    if dep_sel  != "Todos":
        mask_d &= tabla_base["Departamento"] == dep_sel
    if prov_sel != "Todas":
        mask_d &= tabla_base["Provincia"]    == prov_sel
    dists      = sorted(tabla_base[mask_d]["Distrito"].dropna().unique().tolist())
    lista_dist = ["Todos"] + dists
    dist_sel   = st.selectbox("Distrito", lista_dist, index=0,
                              key="dist_sel_p2")

# Aplicar cascada
tabla = tabla_base.copy()
if dep_sel  != "Todos":  tabla = tabla[tabla["Departamento"] == dep_sel]
if prov_sel != "Todas":  tabla = tabla[tabla["Provincia"]    == prov_sel]
if dist_sel != "Todos":  tabla = tabla[tabla["Distrito"]     == dist_sel]

tabla_sorted = tabla.sort_values("TCM distrito (%)")

st.dataframe(
    tabla_sorted, use_container_width=True,
    height=280, hide_index=True,
)

# Descargas
fname = f"distrito_capital_{periodo.replace(' ','').replace('–','_')}"
if dep_sel  != "Todos":  fname += f"_{dep_sel}"
if prov_sel != "Todas":  fname += f"_{prov_sel}"

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv = tabla_sorted.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ Descargar CSV", data=csv,
        file_name=f"{fname}.csv", mime="text/csv",
    )
with col_dl2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        tabla_sorted.to_excel(writer, index=False, sheet_name="DistritoCapital")
    st.download_button(
        "⬇️ Descargar Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"{fname}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.markdown("---")
st.caption(
    "Fuentes: INEI Censos 2007, 2017 y 2025 · "
    "capitales_censo25_1892.xlsx · SSIAT · SDOT-PCM · 2026"
)
