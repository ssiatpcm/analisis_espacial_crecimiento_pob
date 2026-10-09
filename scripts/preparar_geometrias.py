"""
scripts/preparar_geometrias.py
Genera versiones livianas de las capas para el tablero web.

Se ejecuta UNA SOLA VEZ en local (o cuando cambien los shapefiles):

    pip install topojson
    python scripts/preparar_geometrias.py

Salidas (se suben al repositorio):
    data/processed/distritos_simpl.parquet
    data/processed/creaciones_simpl.parquet

Por qué:
    El shapefile original de distritos tiene ~1.7 millones de vértices
    (≈73 MB en GeoJSON). Folium envía ese GeoJSON al navegador cada vez que
    se dibuja el mapa, lo que causa demoras de 30 s o más. A escala nacional
    (zoom 5–10) una tolerancia de 100 m es imperceptible.

Método:
    Simplificación topológica (arcos compartidos, TopoJSON): los límites
    entre distritos vecinos se simplifican una sola vez, así no aparecen
    huecos ni traslapes entre polígonos, a diferencia de GeoSeries.simplify().
"""
from pathlib import Path

import geopandas as gpd
import topojson as tp

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "processed"
OUT.mkdir(parents=True, exist_ok=True)

CRS_METRICO = 32718      # UTM 18S: la tolerancia se expresa en metros
TOLERANCIA_M = 100       # metros
PRECISION = 1e-5         # ≈1 m en grados: recorta decimales del GeoJSON


def simplificar(gdf: gpd.GeoDataFrame, tolerancia: float) -> gpd.GeoDataFrame:
    gdf = gdf.to_crs(CRS_METRICO)
    topo = tp.Topology(gdf, prequantize=False, toposimplify=tolerancia)
    out = topo.to_gdf()
    out = out.set_crs(CRS_METRICO, allow_override=True).to_crs(4326)
    out["geometry"] = out.geometry.make_valid().set_precision(PRECISION)
    return out


def resumen(nombre, antes, despues):
    va = int(antes.geometry.count_coordinates().sum())
    vd = int(despues.geometry.count_coordinates().sum())
    mb_a = len(antes.to_crs(4326).to_json()) / 1e6
    mb_d = len(despues.to_json()) / 1e6
    print(f"{nombre}: {va:,} → {vd:,} vértices · GeoJSON {mb_a:.1f} → {mb_d:.1f} MB")


# ── Distritos (1,892) ───────────────────────────────────────────────────────
dist = gpd.read_file(DATA / "total_distritos_1892.shp")
dist["UBIGEO"] = dist["UBIGEO"].astype(str).str.zfill(6)
dist = dist[["UBIGEO", "NOMBDEP", "NOMBPROV", "NOMBDIST", "geometry"]]
dist_s = simplificar(dist, TOLERANCIA_M)
resumen("Distritos", dist, dist_s)
dist_s.to_parquet(OUT / "distritos_simpl.parquet")

# ── Creaciones post-2002 y distritos de origen (112) ───────────────────────
crea = gpd.read_file(DATA / "totalcreaciones_dist2002.shp")
crea["UBIGEO"] = crea["UBIGEO"].astype(str).str.zfill(6)
crea = crea[["UBIGEO", "tipo", "geometry"]]
# Menor tolerancia: son pocos polígonos y se observan con más zoom
crea_s = simplificar(crea, 50)
resumen("Creaciones", crea, crea_s)
crea_s.to_parquet(OUT / "creaciones_simpl.parquet")

print("Listo →", OUT)
