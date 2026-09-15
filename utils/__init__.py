"""utils — Módulos utilitarios del tablero SSIAT"""
from .calculo_tcm import calcular_tcm, calcular_tcm_dataframe, proyectar_poblacion
from .normativa import evaluar_cumplimiento, calcular_brecha, evaluar_dataframe, COLORES_ESTADO

__all__ = [
    "calcular_tcm", "calcular_tcm_dataframe", "proyectar_poblacion",
    "evaluar_cumplimiento", "calcular_brecha", "evaluar_dataframe", "COLORES_ESTADO",
]
