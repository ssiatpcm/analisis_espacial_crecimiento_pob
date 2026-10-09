# analisis_espacial_crecimiento_pob
De acuerdo con la Ley de Demarcación y Organización Territorial y su reglamento, uno de los criterios técnicos para sustentar las acciones de demarcación territorial corresponde a la variable poblacional. En tal sentido, el uso de esta variable es crucial para el análisis de las acciones de demarcación territorial a cargo de la SDOT y GORE.

## Rendimiento de los mapas

Los mapas usan geometrías simplificadas en `data/processed/*.parquet` (≈5 MB en lugar de ≈73 MB del shapefile original). Si se actualizan los shapefiles de `data/`, regenerar esas capas antes de subir los cambios:

```bash
pip install topojson
python scripts/preparar_geometrias.py
```
