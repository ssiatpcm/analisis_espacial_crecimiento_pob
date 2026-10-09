"""
utils/rendimiento.py
Utilidades para que el tablero responda rápido en Streamlit Cloud.
"""
import io

import geopandas as gpd
import pandas as pd
import streamlit as st


def geojson_liviano(gdf: gpd.GeoDataFrame, campos: list[str]) -> dict:
    """
    GeoJSON solo con las columnas que usa el tooltip/estilo + geometría.

    folium serializa TODAS las columnas del GeoDataFrame y las envía al
    navegador; recortarlas reduce el peso del mapa.
    """
    cols = list(dict.fromkeys([c for c in campos if c in gdf.columns]))
    return gdf[cols + ["geometry"]].__geo_interface__


def capa_puntos(m, df: pd.DataFrame, lon: str, lat: str,
                col_color: str, col_radio: str, col_tooltip: str,
                borde: str = "#ffffff", opacidad: float = 0.85):
    """
    Agrega todos los puntos como UNA sola capa GeoJSON.

    Crear un folium.CircleMarker por fila (≈1,900 capitales) genera miles de
    objetos que folium tarda ~5 s en convertir a HTML en cada ejecución.
    Una capa única con estilo por propiedad se genera en milisegundos y se
    ve igual (mismo color, tamaño y tooltip HTML).
    """
    import folium

    pts = df[[lon, lat, col_color, col_radio, col_tooltip]].dropna(subset=[lon, lat])
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(x), float(y)]},
                "properties": {"c": c, "r": float(r), "t": t},
            }
            for x, y, c, r, t in pts.itertuples(index=False, name=None)
        ],
    }
    folium.GeoJson(
        gj,
        marker=folium.CircleMarker(),
        style_function=lambda f: {
            "radius": f["properties"]["r"],
            "fillColor": f["properties"]["c"],
            "color": borde,
            "weight": 0.5,
            "fill": True,
            "fillOpacity": opacidad,
        },
        tooltip=folium.GeoJsonTooltip(fields=["t"], labels=False, sticky=False),
    ).add_to(m)
    return m


@st.cache_data(show_spinner=False)
def a_excel(df: pd.DataFrame, hoja: str = "Datos") -> bytes:
    """
    Excel en memoria, cacheado: openpyxl es lento y antes se regeneraba el
    archivo en cada interacción, aunque nadie pulsara «Descargar».
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=hoja)
    return buffer.getvalue()


@st.cache_data(show_spinner=False)
def a_csv(df: pd.DataFrame) -> str:
    return df.to_csv(index=False, encoding="utf-8-sig")
