"""
utils/calculo_tcm.py
Tasa de Crecimiento Medio (TCM) anual intercensal.
TCM = [(Af / Ai)^(1/n) - 1] × 100
"""
import numpy as np
import pandas as pd


def calcular_tcm(pob_inicial: float, pob_final: float, n_anios: int) -> float:
    if pob_inicial <= 0 or pob_final <= 0 or n_anios <= 0:
        return np.nan
    return ((pob_final / pob_inicial) ** (1 / n_anios) - 1) * 100


def calcular_tcm_dataframe(
    df: pd.DataFrame,
    col_ini: str,
    col_fin: str,
    n_anios: int,
    col_resultado: str = "TCM",
) -> pd.DataFrame:
    df = df.copy()
    df[col_resultado] = df.apply(
        lambda r: calcular_tcm(r[col_ini], r[col_fin], n_anios), axis=1
    )
    return df


def proyectar_poblacion(pob_base: float, tcm_pct: float, n_anios: int) -> float:
    if np.isnan(tcm_pct) or pob_base <= 0:
        return np.nan
    return pob_base * ((1 + tcm_pct / 100) ** n_anios)


def clasificar_tendencia(tcm: float) -> str:
    if np.isnan(tcm):
        return "Sin datos"
    if tcm >= 1.5:
        return "Crecimiento alto (>=1.5%)"
    if tcm >= 0.5:
        return "Crecimiento moderado (0.5-1.5%)"
    if tcm >= 0.0:
        return "Crecimiento bajo (0-0.5%)"
    if tcm >= -2.5:
        return "Decrecimiento leve (-2.5 a 0%)"
    if tcm >= -5.0:
        return "Decrecimiento moderado (-5 a -2.5%)"
    return "Decrecimiento severo (<-5%)"
