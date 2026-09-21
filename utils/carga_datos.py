"""
utils/carga_datos.py
Carga de datos desde shapefile (.shp) y Excel (.xlsx).
Compatible con entorno local (conda) y Streamlit Cloud (pip).
"""

import pandas as pd
import geopandas as gpd
import streamlit as st
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
F_XLSX  = ROOT / "data" / "distritos_crec_pob.xlsx"
F_SHP   = ROOT / "data" / "total_distritos_1892.shp"


@st.cache_data(show_spinner="Cargando dataset de distritos...")
def cargar_dataframe() -> pd.DataFrame:
    """
    Carga el Excel principal y genera columnas derivadas.

    Columnas originales clave:
        UBIGEO, NOMBDEP, NOMBPROV, NOMBDIST, CAPITAL
        POB2007, POB2017, POB2025, PRY_2025
        TC_07_17  → TCM anual intercensal 2007-2017
        TC_17_25  → TCM anual intercensal 2017-2025
        TC_17_P25 → TCM con población proyectada 2025
        REGION_NAT, ANIO, AMB_INT, MODALIDAD, TIPOLOGIA

    Columnas derivadas:
        ES_CREACION    → True si ANIO no es nulo (distrito creado post-2002)
        TENDENCIA_0717 → "Crecimiento" / "Decrecimiento" / "Sin datos"
        TENDENCIA_1725 → idem para 2017-2025
        DOBLE_DECREC   → True si TCM negativa en ambos períodos
    """
    df = pd.read_excel(F_XLSX, engine="openpyxl")

    # Alinear UBIGEO a 6 dígitos con cero a la izquierda
    df["UBIGEO"] = df["UBIGEO"].astype(str).str.zfill(6)

    # Columnas derivadas
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


@st.cache_data(show_spinner="Cargando capa espacial...")
def cargar_geodataframe() -> gpd.GeoDataFrame:
    """
    Carga el shapefile de distritos y lo reproyecta a WGS84 (EPSG:4326)
    para compatibilidad con Folium.

    El shapefile original está en UTM zona 18S (EPSG:32718).
    Columnas: OBJECTID, UBIGEO, NOMBDEP, NOMBPROV, NOMBDIST, geometry
    """
    gdf = gpd.read_file(F_SHP)
    gdf["UBIGEO"] = gdf["UBIGEO"].astype(str).str.zfill(6)

    # Reproyectar a WGS84 (requerido por Folium/Leaflet)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    return gdf


@st.cache_data(show_spinner="Integrando datos espaciales y tabulares...")
def cargar_datos_integrados() -> gpd.GeoDataFrame:
    """
    Retorna GeoDataFrame con geometría (WGS84) + todas las variables del Excel.
    Unión por UBIGEO. Usado por el mapa coroplético.
    """
    df  = cargar_dataframe()
    gdf = cargar_geodataframe()

    cols_excel = [
        "UBIGEO", "POB2007", "POB2017", "POB2025", "PRY_2025",
        "TC_07_17", "TC_17_25", "TC_17_P25",
        "REGION_NAT", "ANIO", "AMB_INT", "MODALIDAD", "TIPOLOGIA",
        "ES_CREACION", "TENDENCIA_0717", "TENDENCIA_1725", "DOBLE_DECREC",
    ]

    gdf_merged = gdf.merge(
        df[cols_excel],
        on="UBIGEO",
        how="left",
    )
    return gdf_merged
