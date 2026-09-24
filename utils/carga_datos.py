"""
utils/carga_datos.py
Carga de datos desde shapefile (.shp), Excel de distritos y Excel de capitales.
Compatible con entorno local (conda) y Streamlit Cloud (pip).
"""

import pandas as pd
import geopandas as gpd
import streamlit as st
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
F_XLSX     = ROOT / "data" / "distritos_crec_pob.xlsx"
F_SHP      = ROOT / "data" / "total_distritos_1892.shp"
F_CAPITALES = ROOT / "data" / "capitales_censo25_1892.xlsx"


# ── Rangos de población para las capitales ──────────────────────────────────
BINS_POB   = [0, 500, 2_000, 5_000, 10_000, 50_000, float("inf")]
LABELS_POB = ["< 500", "500–2k", "2k–5k", "5k–10k", "10k–50k", "> 50k"]


def _dinamica(tasa_cap, tasa_dist) -> str:
    """Clasifica la relación entre TCM capital y TCM distrito."""
    if pd.isna(tasa_cap) or pd.isna(tasa_dist):
        return "Sin datos"
    if tasa_cap > 0 and tasa_dist > 0:
        return "Ambos crecen"
    if tasa_cap > 0 and tasa_dist < 0:
        return "Capital crece / Distrito decrece"
    if tasa_cap < 0 and tasa_dist > 0:
        return "Capital decrece / Distrito crece"
    return "Ambos decrecen"


@st.cache_data(show_spinner="Cargando dataset de distritos...")
def cargar_dataframe() -> pd.DataFrame:
    """
    Carga el Excel de distritos y genera columnas derivadas.

    Columnas originales clave:
        UBIGEO, NOMBDEP, NOMBPROV, NOMBDIST
        POB2007, POB2017, POB2025
        TC_07_17, TC_17_25, TC_17_P25
        REGION_NAT, ANIO, AMB_INT, MODALIDAD, TIPOLOGIA

    Columnas derivadas:
        ES_CREACION    → True si ANIO no es nulo
        TENDENCIA_0717 → Crecimiento / Decrecimiento / Sin datos
        TENDENCIA_1725 → idem para 2017-2025
        DOBLE_DECREC   → True si TCM negativa en ambos períodos
    """
    df = pd.read_excel(F_XLSX, engine="openpyxl")
    df["UBIGEO"] = df["UBIGEO"].astype(str).str.zfill(6)

    df["ES_CREACION"] = df["ANIO"].notna()
    df["TENDENCIA_0717"] = df["TC_07_17"].apply(
        lambda x: "Sin datos" if pd.isna(x)
        else ("Crecimiento" if x > 0 else "Decrecimiento")
    )
    df["TENDENCIA_1725"] = df["TC_17_25"].apply(
        lambda x: "Sin datos" if pd.isna(x)
        else ("Crecimiento" if x > 0 else "Decrecimiento")
    )
    df["DOBLE_DECREC"] = (df["TC_07_17"] < 0) & (df["TC_17_25"] < 0)
    return df


@st.cache_data(show_spinner="Cargando capitales distritales...")
def cargar_capitales() -> pd.DataFrame:
    """
    Carga el Excel de capitales y lo enriquece con variables del Excel
    de distritos (REGION_NAT, TIPOLOGIA, TC_07_17, TC_17_25, ANIO).

    Columnas originales (capitales_censo25_1892.xlsx):
        UBIGEO, NOMBCCPP, NOMBDEP, NOMBPROV, NOMBDIST
        POB2007, POB2017, POB2025
        TASA_0717, TASA_1725   ← TCM de la capital
        X, Y                   ← coordenadas WGS84 (lon, lat)

    Columnas derivadas:
        RANGO_POB    → categoría por tamaño de población 2017
        DINAMICA_0717 → relación capital vs. distrito 2007-2017
        DINAMICA_1725 → idem para 2017-2025
        DOBLE_DECREC_CAP → True si TASA_0717 < 0 y TASA_1725 < 0
    """
    cap = pd.read_excel(F_CAPITALES, engine="openpyxl")
    cap["UBIGEO"] = cap["UBIGEO"].astype(str).str.zfill(6)

    # Traer variables analíticas del Excel de distritos
    dist = cargar_dataframe()[
        ["UBIGEO", "TC_07_17", "TC_17_25", "REGION_NAT", "TIPOLOGIA", "ANIO"]
    ]
    cap = cap.merge(dist, on="UBIGEO", how="left")

    # Rango de población
    cap["RANGO_POB"] = pd.cut(
        cap["POB2017"], bins=BINS_POB, labels=LABELS_POB
    ).astype(str)

    # Dinámica capital vs. distrito
    cap["DINAMICA_0717"] = cap.apply(
        lambda r: _dinamica(r["TASA_0717"], r["TC_07_17"]), axis=1
    )
    cap["DINAMICA_1725"] = cap.apply(
        lambda r: _dinamica(r["TASA_1725"], r["TC_17_25"]), axis=1
    )

    # Doble decrecimiento de la capital
    cap["DOBLE_DECREC_CAP"] = (cap["TASA_0717"] < 0) & (cap["TASA_1725"] < 0)

    return cap


@st.cache_data(show_spinner="Cargando capa espacial...")
def cargar_geodataframe() -> gpd.GeoDataFrame:
    """
    Carga el shapefile de distritos y lo reproyecta a WGS84 (EPSG:4326).
    El CRS original es UTM zona 18S (EPSG:32718).
    """
    gdf = gpd.read_file(F_SHP)
    gdf["UBIGEO"] = gdf["UBIGEO"].astype(str).str.zfill(6)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


@st.cache_data(show_spinner="Integrando datos espaciales...")
def cargar_datos_integrados() -> gpd.GeoDataFrame:
    """
    GeoDataFrame con geometría (WGS84) + variables del Excel de distritos.
    Usado por el mapa coroplético de la P1.
    """
    df  = cargar_dataframe()
    gdf = cargar_geodataframe()

    cols_excel = [
        "UBIGEO", "POB2007", "POB2017", "POB2025", "PRY_2025",
        "TC_07_17", "TC_17_25", "TC_17_P25",
        "REGION_NAT", "ANIO", "AMB_INT", "MODALIDAD", "TIPOLOGIA",
        "ES_CREACION", "TENDENCIA_0717", "TENDENCIA_1725", "DOBLE_DECREC",
    ]
    return gdf.merge(df[cols_excel], on="UBIGEO", how="left")
