"""Capa de cacheo para Streamlit.

Usa @st.cache_data con disco como fallback para evitar recalcular el pipeline completo.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.config import CACHE_DIR, DATA_DIR
from dashboard.data.pipeline import (
    load_dynamic_events,
    load_physical_data,
    run_full_pipeline,
)


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def invalidate_cache():
    """Borra archivos de cache y limpia cache de Streamlit."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.csv"):
            f.unlink()
        for f in CACHE_DIR.glob("*.json"):
            if f.name != ".gitignore":
                f.unlink()
    st.cache_data.clear()


@st.cache_data(ttl=3600, show_spinner="Calculando scores...")
def _run_pipeline():
    result = run_full_pipeline(DATA_DIR)
    # Persist to disk
    _ensure_cache_dir()
    result["scores_all"].to_csv(CACHE_DIR / "scores_all.csv", index=False)
    result["aggregated"].to_csv(CACHE_DIR / "aggregated.csv", index=False)
    result["physical"].to_csv(CACHE_DIR / "physical.csv", index=False)
    return result


def _load_from_cache_or_compute():
    """Intenta leer de cache en disco; si no existe, computa."""
    cache_scores = CACHE_DIR / "scores_all.csv"
    cache_agg = CACHE_DIR / "aggregated.csv"
    cache_phys = CACHE_DIR / "physical.csv"

    if cache_scores.exists() and cache_agg.exists() and cache_phys.exists():
        return {
            "scores_all": pd.read_csv(cache_scores),
            "aggregated": pd.read_csv(cache_agg),
            "physical": pd.read_csv(cache_phys),
        }
    return _run_pipeline()


def load_scores() -> pd.DataFrame:
    data = _load_from_cache_or_compute()
    return data["scores_all"]


def load_aggregated() -> pd.DataFrame:
    data = _load_from_cache_or_compute()
    return data["aggregated"]


def load_physical() -> pd.DataFrame:
    data = _load_from_cache_or_compute()
    return data["physical"]


@st.cache_data(ttl=3600, show_spinner="Cargando eventos dinamicos...")
def load_dynamic() -> pd.DataFrame:
    return load_dynamic_events(DATA_DIR)


@st.cache_data(ttl=3600, show_spinner="Cargando datos fisicos crudos...")
def load_physical_raw() -> pd.DataFrame:
    return load_physical_data(DATA_DIR)


# ---------------------------------------------------------------------------
# M3: Inferencia - Cache
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Calculando inferencia...")
def _run_inference():
    """Ejecuta pipeline de inferencia y guarda en cache."""
    from dashboard.data.inference import run_inference_pipeline

    base = _load_from_cache_or_compute()
    dynamic_sev = load_dynamic()
    physical_raw = load_physical_raw()

    result = run_inference_pipeline(
        scores_all=base["scores_all"],
        aggregated=base["aggregated"],
        physical=physical_raw,
        dynamic_sev=dynamic_sev,
    )

    _ensure_cache_dir()
    clustering = result["clustering"]
    clustering["labels_df"].to_csv(CACHE_DIR / "clustering_labels.csv", index=False)
    clustering["centers"].to_csv(CACHE_DIR / "clustering_centers.csv", index=False)
    with open(CACHE_DIR / "clustering_meta.json", "w") as f:
        json.dump(clustering["meta"], f, indent=2)

    if not result["fatigue"].empty:
        result["fatigue"].to_csv(CACHE_DIR / "fatigue.csv", index=False)
    if not result["fatigue_stats"].empty:
        result["fatigue_stats"].to_csv(CACHE_DIR / "fatigue_stats.csv", index=False)
    if not result["risk"].empty:
        result["risk"].to_csv(CACHE_DIR / "risk.csv", index=False)
    if not result["correlations"].empty:
        result["correlations"].to_csv(CACHE_DIR / "correlations.csv", index=False)

    return result


def _load_inference_from_cache_or_compute():
    """Lee inferencia de disco si existe, si no computa."""
    cache_cl = CACHE_DIR / "clustering_labels.csv"
    cache_meta = CACHE_DIR / "clustering_meta.json"

    if cache_cl.exists() and cache_meta.exists():
        labels_df = pd.read_csv(cache_cl)
        centers = pd.read_csv(CACHE_DIR / "clustering_centers.csv") if (CACHE_DIR / "clustering_centers.csv").exists() else pd.DataFrame()
        with open(cache_meta) as f:
            meta = json.load(f)

        fatigue = pd.read_csv(CACHE_DIR / "fatigue.csv") if (CACHE_DIR / "fatigue.csv").exists() else pd.DataFrame()
        fatigue_stats = pd.read_csv(CACHE_DIR / "fatigue_stats.csv") if (CACHE_DIR / "fatigue_stats.csv").exists() else pd.DataFrame()
        risk = pd.read_csv(CACHE_DIR / "risk.csv") if (CACHE_DIR / "risk.csv").exists() else pd.DataFrame()
        correlations = pd.read_csv(CACHE_DIR / "correlations.csv") if (CACHE_DIR / "correlations.csv").exists() else pd.DataFrame()

        return {
            "clustering": {"labels_df": labels_df, "meta": meta, "centers": centers},
            "fatigue": fatigue,
            "fatigue_stats": fatigue_stats,
            "risk": risk,
            "correlations": correlations,
        }

    return _run_inference()


def load_clustering() -> dict:
    data = _load_inference_from_cache_or_compute()
    return data["clustering"]


def load_fatigue() -> pd.DataFrame:
    data = _load_inference_from_cache_or_compute()
    return data["fatigue"]


def load_fatigue_stats() -> pd.DataFrame:
    data = _load_inference_from_cache_or_compute()
    return data["fatigue_stats"]


def load_risk() -> pd.DataFrame:
    data = _load_inference_from_cache_or_compute()
    return data["risk"]


def load_correlations() -> pd.DataFrame:
    data = _load_inference_from_cache_or_compute()
    return data["correlations"]


# ---------------------------------------------------------------------------
# M4: What-If - Cache de distribuciones
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Preparando distribuciones...")
def load_whatif_distributions() -> dict:
    """Cachea distribuciones empiricas para escenarios What-If."""
    from dashboard.data.whatif import build_player_metric_distributions

    return build_player_metric_distributions(load_scores())


# ---------------------------------------------------------------------------
# M5: Valoracion Multidimensional - Cache
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Calculando valoración...")
def _run_valuation():
    """Ejecuta pipeline de valoracion y guarda en cache."""
    from dashboard.data.valuation import run_valuation_pipeline

    base = _load_from_cache_or_compute()
    inference = _load_inference_from_cache_or_compute()

    result = run_valuation_pipeline(
        aggregated=base["aggregated"],
        physical=base["physical"],
        fatigue=inference["fatigue"],
        risk=inference["risk"],
    )

    _ensure_cache_dir()
    result.to_csv(CACHE_DIR / "valuation.csv", index=False)
    return result


def _load_valuation_from_cache_or_compute() -> pd.DataFrame:
    """Lee valoracion de disco si existe, si no computa."""
    cache_val = CACHE_DIR / "valuation.csv"
    if cache_val.exists():
        return pd.read_csv(cache_val)
    return _run_valuation()


def load_valuation() -> pd.DataFrame:
    return _load_valuation_from_cache_or_compute()
