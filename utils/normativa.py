"""
utils/normativa.py
Umbrales mínimos de población por tipología distrital.
Marco: TUO DS 134-2025-PCM · Art. 14 · Ley N.° 27795
"""
import numpy as np
import pandas as pd

UMBRALES_TIPOLOGIA: dict = {
    "A2":   2_000,
    "A3.1": 4_000,
    "A3.2": 6_000,
    "AB":   8_000,
    "B1":  12_000,
    "B2":  20_000,
    "B3":  50_000,
}


def obtener_umbral(tipologia: str):
    return UMBRALES_TIPOLOGIA.get(str(tipologia).strip().upper())


def evaluar_cumplimiento(pob: float, tipologia: str) -> str:
    umbral = obtener_umbral(tipologia)
    if umbral is None:
        return "Sin tipo"
    if np.isnan(pob) or pob <= 0:
        return "Incumple"
    ratio = pob / umbral
    if ratio >= 1.0:
        return "Cumple"
    if ratio >= 0.80:
        return "Riesgo"
    return "Incumple"


def calcular_brecha(pob: float, tipologia: str) -> float:
    umbral = obtener_umbral(tipologia)
    if umbral is None or np.isnan(pob):
        return np.nan
    return pob - umbral


def evaluar_dataframe(
    df: pd.DataFrame,
    col_pob: str,
    col_tipo: str,
    col_estado: str = "estado_normativo",
    col_brecha: str = "brecha_pob",
) -> pd.DataFrame:
    df = df.copy()
    df[col_estado] = df.apply(
        lambda r: evaluar_cumplimiento(r[col_pob], r[col_tipo]), axis=1
    )
    df[col_brecha] = df.apply(
        lambda r: calcular_brecha(r[col_pob], r[col_tipo]), axis=1
    )
    return df


COLORES_ESTADO: dict = {
    "Cumple":   "#10B981",
    "Riesgo":   "#F59E0B",
    "Incumple": "#EF4444",
    "Sin tipo": "#9CA3AF",
}
