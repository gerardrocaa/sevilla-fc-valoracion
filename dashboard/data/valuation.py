"""Modulo 5: Valoracion Multidimensional - Calculo puro.

Combina rendimiento deportivo con factores comerciales y de mercado
para producir un score integral (0-100) por jugador.

Dimensiones:
  1. Rendimiento Deportivo (datos reales - composite score M1)
  2. Condicion Fisica (datos reales - M3 fisico + fatiga + riesgo)
  3. Valor de Mercado (datos externos - archivo CSV)
  4. Impacto Comercial (datos externos - archivo CSV)
  5. Fiabilidad Medica (datos externos - archivo CSV)

Las dimensiones 3-5 requieren un archivo CSV con datos reales:
  dashboard/data/external/datos_externos_jugadores.csv

Si el archivo no existe, esas dimensiones se calculan como 0.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Carga de datos externos (archivo CSV proporcionado por el usuario)
# ---------------------------------------------------------------------------

_EXTERNAL_CSV = Path(__file__).resolve().parent / "external" / "datos_externos_jugadores.csv"

# Columnas esperadas en el CSV externo:
# player_name, market_value_m, age, contract_years,
# instagram_followers_k,
# injuries_2y, days_missed, recurring_injury (true/false)

_EXTERNAL_DATA: dict[str, dict] | None = None


def _load_external_data() -> dict[str, dict]:
    """Lee el CSV externo y devuelve un dict {player_name: {...}}."""
    global _EXTERNAL_DATA
    if _EXTERNAL_DATA is not None:
        return _EXTERNAL_DATA

    if not _EXTERNAL_CSV.exists():
        _EXTERNAL_DATA = {}
        return _EXTERNAL_DATA

    df = pd.read_csv(_EXTERNAL_CSV)
    if "player_name" not in df.columns:
        _EXTERNAL_DATA = {}
        return _EXTERNAL_DATA

    result = {}
    for _, row in df.iterrows():
        name = row["player_name"]
        result[name] = {
            "market_value_m": float(row.get("market_value_m", 0) or 0),
            "age": int(row.get("age", 0) or 0),
            "contract_years": int(row.get("contract_years", 0) or 0),
            "instagram_followers_k": float(row.get("instagram_followers_k", 0) or 0),
            "injuries_2y": int(row.get("injuries_2y", 0) or 0),
            "days_missed": int(row.get("days_missed", 0) or 0),
            "recurring_injury": str(row.get("recurring_injury", "false")).lower() in ("true", "1", "si", "yes"),
        }

    _EXTERNAL_DATA = result
    return _EXTERNAL_DATA


def _get_external(player_name: str) -> dict | None:
    """Devuelve datos externos del jugador o None si no existe."""
    data = _load_external_data()
    return data.get(player_name)


def has_external_data() -> bool:
    """Indica si hay datos externos cargados."""
    return len(_load_external_data()) > 0


def get_external_coverage(player_names: list[str]) -> dict:
    """Devuelve estadisticas de cobertura de datos externos."""
    data = _load_external_data()
    covered = [p for p in player_names if p in data]
    return {
        "total": len(player_names),
        "covered": len(covered),
        "missing": [p for p in player_names if p not in data],
        "has_data": len(data) > 0,
    }


def _percentile_rank(series: pd.Series) -> pd.Series:
    """Rango percentil (0-100) de una serie."""
    return series.rank(pct=True) * 100


# ---------------------------------------------------------------------------
# Sub-scores (cada uno devuelve Series 0-100)
# ---------------------------------------------------------------------------

def compute_rendimiento_score(aggregated: pd.DataFrame) -> pd.Series:
    """D1: Score basado en composite_score con penalizacion por CV alto."""
    base = aggregated["composite_score"] * 100
    # Penalizar inconsistencia: CV > 0.3 reduce el score hasta un 15%
    cv = aggregated["cv"].fillna(0)
    penalty = np.where(cv > 0.3, np.minimum((cv - 0.3) * 50, 15), 0)
    return (base - penalty).clip(0, 100)


def compute_fisico_score(
    aggregated: pd.DataFrame,
    physical: pd.DataFrame,
    fatigue: pd.DataFrame,
    risk: pd.DataFrame,
) -> pd.Series:
    """D2: Percentil fisico + resiliencia fatiga + ajuste riesgo."""
    scores = pd.Series(50.0, index=aggregated.index, name="score_fisico")

    if physical.empty:
        return scores

    # Score D5 ya normalizado 0-1 en aggregated
    if "score_d5" in aggregated.columns:
        scores = aggregated["score_d5"].fillna(0.5) * 100

    # Ajuste por fatiga: jugadores con menor fatiga media ganan puntos
    if not fatigue.empty and "fatigue_index" in fatigue.columns:
        name_col = "dyn_name" if "dyn_name" in fatigue.columns else "player_name"
        fat_mean = fatigue.groupby(name_col)["fatigue_index"].mean()
        for i, row in aggregated.iterrows():
            pname = row.get("player_name", "")
            if pname in fat_mean.index:
                fi = fat_mean[pname]
                scores.iloc[i] += (0.5 - fi) * 20  # +-10 puntos

    # Ajuste por riesgo de lesion
    if not risk.empty and "risk_score" in risk.columns:
        name_col = "dyn_name" if "dyn_name" in risk.columns else "player_name"
        risk_map = risk.set_index(name_col)["risk_score"]
        for i, row in aggregated.iterrows():
            pname = row.get("player_name", "")
            if pname in risk_map.index:
                rs = risk_map[pname]
                scores.iloc[i] -= rs * 10  # Penalizar hasta 10 pts

    return scores.fillna(50).clip(0, 100)


def compute_mercado_score(aggregated: pd.DataFrame) -> pd.Series:
    """D3: Eficiencia valor/rendimiento + factor edad + contrato.

    Requiere datos externos. Si no hay, devuelve 0.
    """
    if not has_external_data():
        return pd.Series(0.0, index=aggregated.index, name="score_mercado")

    scores = []
    for _, row in aggregated.iterrows():
        ext = _get_external(row["player_name"])
        if ext is None or ext["market_value_m"] == 0:
            scores.append(0.0)
            continue

        mv = ext["market_value_m"]
        age = ext["age"]
        contract = ext["contract_years"]
        perf = row["composite_score"]

        # Eficiencia: rendimiento por millon invertido (normalizado)
        efficiency = (perf / max(mv, 0.5)) * 10
        efficiency_score = min(efficiency * 30, 60)

        # Factor edad: pico 23-28, decae suavemente
        if age == 0:
            age_bonus = 10
        elif 23 <= age <= 28:
            age_bonus = 20
        elif age < 23:
            age_bonus = 15 + (age - 18) * 1
        else:
            age_bonus = max(20 - (age - 28) * 3, 0)

        # Factor contrato: mas anos = mas control
        contract_bonus = min(contract * 4, 20)

        scores.append(min(efficiency_score + age_bonus + contract_bonus, 100))

    return pd.Series(scores, index=aggregated.index, name="score_mercado")


def compute_comercial_score(aggregated: pd.DataFrame) -> pd.Series:
    """D4: Percentil seguidores Instagram.

    Requiere datos externos. Si no hay, devuelve 0.
    """
    if not has_external_data():
        return pd.Series(0.0, index=aggregated.index, name="score_comercial")

    ig_vals = []
    for _, row in aggregated.iterrows():
        ext = _get_external(row["player_name"])
        ig_vals.append(ext["instagram_followers_k"] if ext else 0)

    ig = pd.Series(ig_vals, index=aggregated.index)

    # Si todos son 0, no hay datos utiles
    if ig.sum() == 0:
        return pd.Series(0.0, index=aggregated.index, name="score_comercial")

    return _percentile_rank(ig).clip(0, 100)


def compute_medico_score(aggregated: pd.DataFrame) -> pd.Series:
    """D5: 100 - penalizaciones por historial de lesiones.

    Requiere datos externos. Si no hay, devuelve 0.
    """
    if not has_external_data():
        return pd.Series(0.0, index=aggregated.index, name="score_medico")

    scores = []
    for _, row in aggregated.iterrows():
        ext = _get_external(row["player_name"])
        if ext is None:
            scores.append(0.0)
            continue

        base = 100.0
        base -= ext["injuries_2y"] * 10
        base -= min(ext["days_missed"] * 0.3, 20)
        if ext["recurring_injury"]:
            base -= 15
        scores.append(max(base, 0))

    return pd.Series(scores, index=aggregated.index, name="score_medico")


# ---------------------------------------------------------------------------
# Resumen de jugador
# ---------------------------------------------------------------------------

def generate_player_summary(
    player_row: pd.Series,
    team_medians: pd.Series,
) -> dict:
    """Genera fortalezas y areas de mejora de un jugador.

    Args:
        player_row: Fila del DataFrame de valoracion con los 5 sub-scores.
        team_medians: Medianas del equipo para los 5 sub-scores.

    Returns:
        {"fortalezas": [...], "mejora": [...]}
    """
    dims = ["score_rendimiento", "score_fisico", "score_mercado", "score_comercial", "score_medico"]
    labels = {
        "score_rendimiento": "Rendimiento Deportivo",
        "score_fisico": "Condicion Fisica",
        "score_mercado": "Valor de Mercado",
        "score_comercial": "Impacto Comercial",
        "score_medico": "Fiabilidad Medica",
    }

    # Filtrar dimensiones que tienen datos (score > 0 en al menos algun jugador)
    active_dims = [d for d in dims if team_medians.get(d, 0) > 0]
    if not active_dims:
        active_dims = ["score_rendimiento", "score_fisico"]

    fortalezas = []
    mejora = []

    for d in active_dims:
        val = player_row.get(d, 0)
        med = team_medians.get(d, 0)
        diff = val - med
        if diff > 10:
            fortalezas.append(f"{labels[d]} ({val:.0f} vs {med:.0f} equipo)")
        elif diff < -10:
            mejora.append(f"{labels[d]} ({val:.0f} vs {med:.0f} equipo)")

    if not fortalezas:
        best = max(active_dims, key=lambda d: player_row.get(d, 0))
        fortalezas.append(f"{labels[best]} ({player_row.get(best, 0):.0f})")
    if not mejora:
        worst = min(active_dims, key=lambda d: player_row.get(d, 100))
        mejora.append(f"{labels[worst]} ({player_row.get(worst, 0):.0f})")

    return {"fortalezas": fortalezas, "mejora": mejora}


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------

def run_valuation_pipeline(
    aggregated: pd.DataFrame,
    physical: pd.DataFrame,
    fatigue: pd.DataFrame,
    risk: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula los 5 sub-scores para todos los jugadores.

    Returns:
        DataFrame con columnas: player_name, profile, score_rendimiento,
        score_fisico, score_mercado, score_comercial, score_medico.
        Si hay datos externos, incluye columnas adicionales.
    """
    df = aggregated[["player_name", "profile", "composite_score", "cv", "n_matches", "total_minutes"]].copy()

    df["score_rendimiento"] = compute_rendimiento_score(aggregated).values
    df["score_fisico"] = compute_fisico_score(aggregated, physical, fatigue, risk).values
    df["score_mercado"] = compute_mercado_score(aggregated).values
    df["score_comercial"] = compute_comercial_score(aggregated).values
    df["score_medico"] = compute_medico_score(aggregated).values

    # Anadir datos externos si existen
    ext_cols = ["market_value_m", "age", "contract_years", "instagram_followers_k",
                "injuries_2y", "days_missed"]
    has_ext = has_external_data()
    if has_ext:
        for col in ext_cols:
            vals = []
            for p in df["player_name"]:
                ext = _get_external(p)
                vals.append(ext.get(col, None) if ext else None)
            df[col] = vals
    else:
        for col in ext_cols:
            df[col] = None

    df["has_external_data"] = [_get_external(p) is not None for p in df["player_name"]]

    return df


def compute_integral_score(
    valuation_df: pd.DataFrame,
    weights: dict,
) -> pd.DataFrame:
    """Aplica pesos configurables y genera el score integral.

    Args:
        valuation_df: DataFrame de run_valuation_pipeline.
        weights: Dict con pesos por dimension (deben sumar 100).

    Returns:
        DataFrame con columna integral_score anadida.
    """
    df = valuation_df.copy()
    total = sum(weights.values())
    if total == 0:
        total = 1

    df["integral_score"] = (
        df["score_rendimiento"] * weights.get("rendimiento", 0)
        + df["score_fisico"] * weights.get("fisico", 0)
        + df["score_mercado"] * weights.get("mercado", 0)
        + df["score_comercial"] * weights.get("comercial", 0)
        + df["score_medico"] * weights.get("medico", 0)
    ) / total

    df = df.sort_values("integral_score", ascending=False).reset_index(drop=True)
    return df
