"""Motor de computo para Modulo 3: Inferencia Predictiva.

Funciones puras sin dependencia de Streamlit.
Clustering, fatiga, riesgo de lesion y correlaciones.
"""

import json
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from dashboard.config import (
    ACWR_THRESHOLDS,
    CLUSTERING_FEATURES,
    CLUSTERING_FEATURES_PHYSICAL,
    CORRELATION_PAIRS,
    DIM_LABELS,
    LOAD_SPIKE_THRESHOLD,
    MATCHES,
    PSV99_DROP_THRESHOLD,
)

warnings.filterwarnings("ignore")

RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def run_clustering(
    aggregated: pd.DataFrame,
    physical: pd.DataFrame,
    mode: str = "tactical",
    max_k: int = 6,
) -> dict:
    """Ejecuta K-Means clustering sobre jugadores.

    Args:
        aggregated: DataFrame con scores D1-D6 por jugador.
        physical: DataFrame con metricas fisicas por jugador/partido.
        mode: 'tactical' (solo D1-D6) o 'physical' (D1-D6 + fisicas).
        max_k: K maximo a probar.

    Returns:
        dict con 'labels_df', 'meta', 'centers'.
    """
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    df = aggregated.copy()
    features = list(CLUSTERING_FEATURES)

    if mode == "physical" and not physical.empty:
        phys_agg = physical.groupby("dyn_name")[CLUSTERING_FEATURES_PHYSICAL].mean().reset_index()
        df = df.merge(phys_agg, left_on="player_name", right_on="dyn_name", how="inner")
        features = features + [f for f in CLUSTERING_FEATURES_PHYSICAL if f in df.columns]

    # Drop rows with NaN in feature columns
    df = df.dropna(subset=features)
    if len(df) < 4:
        return _empty_clustering(df)

    X = df[features].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find optimal k via silhouette
    max_k = min(max_k, len(df) - 1)
    best_k, best_score = 2, -1
    scores = {}
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        scores[k] = sil
        if sil > best_score:
            best_score = sil
            best_k = k

    # Fit final model
    km_final = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
    labels = km_final.fit_predict(X_scaled)

    # PCA 2D
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coords = pca.fit_transform(X_scaled)

    # Build labels df
    labels_df = df[["player_name", "profile"]].copy()
    if "dyn_name" in df.columns:
        labels_df["dyn_name"] = df["dyn_name"]
    labels_df["cluster"] = labels
    labels_df["pc1"] = coords[:, 0]
    labels_df["pc2"] = coords[:, 1]
    for feat in CLUSTERING_FEATURES:
        if feat in df.columns:
            labels_df[feat] = df[feat].values

    # Cluster descriptive labels based on dominant dimension
    cluster_labels = {}
    dim_names = list(DIM_LABELS.values())
    for c in range(best_k):
        mask = labels == c
        if mask.sum() == 0:
            cluster_labels[c] = f"Cluster {c}"
            continue
        means = X_scaled[mask].mean(axis=0)[:len(CLUSTERING_FEATURES)]
        dominant_idx = int(np.argmax(means))
        dominant_dim = dim_names[dominant_idx] if dominant_idx < len(dim_names) else f"D{dominant_idx + 1}"
        cluster_labels[c] = f"C{c}: {dominant_dim}"

    labels_df["cluster_label"] = labels_df["cluster"].map(cluster_labels)

    # Centers in original scale
    centers_scaled = km_final.cluster_centers_
    centers_original = scaler.inverse_transform(centers_scaled)
    centers_df = pd.DataFrame(centers_original[:, :len(CLUSTERING_FEATURES)], columns=CLUSTERING_FEATURES)
    centers_df["cluster"] = range(best_k)
    centers_df["cluster_label"] = [cluster_labels[c] for c in range(best_k)]

    meta = {
        "n_clusters": best_k,
        "silhouette": round(best_score, 4),
        "variance_explained": round(float(pca.explained_variance_ratio_.sum()), 4),
        "n_players": len(df),
        "mode": mode,
        "silhouette_scores": {str(k): round(v, 4) for k, v in scores.items()},
        "cluster_labels": cluster_labels,
    }

    return {"labels_df": labels_df, "meta": meta, "centers": centers_df}


def _empty_clustering(df: pd.DataFrame) -> dict:
    labels_df = df[["player_name", "profile"]].copy()
    labels_df["cluster"] = 0
    labels_df["pc1"] = 0.0
    labels_df["pc2"] = 0.0
    labels_df["cluster_label"] = "C0"
    for feat in CLUSTERING_FEATURES:
        if feat in df.columns:
            labels_df[feat] = df[feat].values
    meta = {"n_clusters": 1, "silhouette": 0.0, "variance_explained": 0.0,
            "n_players": len(df), "mode": "tactical", "silhouette_scores": {},
            "cluster_labels": {0: "C0"}}
    centers = df[CLUSTERING_FEATURES].mean().to_frame().T if len(df) > 0 else pd.DataFrame()
    if not centers.empty:
        centers["cluster"] = 0
        centers["cluster_label"] = "C0"
    return {"labels_df": labels_df, "meta": meta, "centers": centers}


# ---------------------------------------------------------------------------
# Fatiga
# ---------------------------------------------------------------------------

def compute_fatigue_index(physical: pd.DataFrame) -> pd.DataFrame:
    """Calcula indice de fatiga por jugador y partido.

    Returns:
        DataFrame con columnas: dyn_name, match_id, jornada, fatigue_index,
        cumulative_load, psv99, psv99_pct_change, hsr_pct_change.
    """
    if physical.empty:
        return pd.DataFrame()

    df = physical.copy()
    df["jornada"] = df["match_id"].map(lambda x: MATCHES.get(x, {}).get("jornada", ""))
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    df["jornada_idx"] = df["jornada"].map(lambda j: jornada_order.index(j) if j in jornada_order else -1)
    df = df.sort_values(["dyn_name", "jornada_idx"])

    results = []
    for player, pdata in df.groupby("dyn_name"):
        pdata = pdata.sort_values("jornada_idx")

        # Cumulative load = sum(Distance + HSR Distance + Sprint Distance)
        load_cols = ["Distance", "HSR Distance", "Sprint Distance"]
        available_load = [c for c in load_cols if c in pdata.columns]
        if not available_load:
            continue

        pdata = pdata.copy()
        pdata["match_load"] = pdata[available_load].sum(axis=1)
        pdata["cumulative_load"] = pdata["match_load"].cumsum()

        # PSV-99 change
        psv_col = "PSV-99"
        if psv_col in pdata.columns:
            pdata["psv99"] = pdata[psv_col]
            pdata["psv99_pct_change"] = pdata[psv_col].pct_change() * 100
        else:
            pdata["psv99"] = np.nan
            pdata["psv99_pct_change"] = 0.0

        # HSR change
        hsr_col = "HSR Distance"
        if hsr_col in pdata.columns:
            pdata["hsr_pct_change"] = pdata[hsr_col].pct_change() * 100
        else:
            pdata["hsr_pct_change"] = 0.0

        # Fatigue index: weighted combination [0, 1]
        # Component 1: PSV-99 drop (capped)
        psv_drop = pdata["psv99_pct_change"].clip(lower=-30, upper=0).abs() / 30.0
        # Component 2: HSR reduction (capped)
        hsr_drop = pdata["hsr_pct_change"].clip(lower=-50, upper=0).abs() / 50.0
        # Component 3: Cumulative load (normalized within player)
        load_max = pdata["cumulative_load"].max()
        load_norm = pdata["cumulative_load"] / load_max if load_max > 0 else 0

        fatigue = (0.35 * psv_drop.fillna(0) + 0.30 * hsr_drop.fillna(0) + 0.35 * load_norm).clip(0, 1)

        for _, row in pdata.iterrows():
            idx = pdata.index.get_loc(row.name)
            results.append({
                "dyn_name": player,
                "match_id": row["match_id"],
                "jornada": row["jornada"],
                "fatigue_index": round(fatigue.iloc[idx], 4),
                "cumulative_load": round(row["cumulative_load"], 1),
                "match_load": round(row["match_load"], 1),
                "psv99": round(row["psv99"], 1) if pd.notna(row["psv99"]) else None,
                "psv99_pct_change": round(row["psv99_pct_change"], 2) if pd.notna(row["psv99_pct_change"]) else None,
                "hsr_pct_change": round(row["hsr_pct_change"], 2) if pd.notna(row["hsr_pct_change"]) else None,
            })

    return pd.DataFrame(results) if results else pd.DataFrame()


def compute_fatigue_model_stats(fatigue_df: pd.DataFrame) -> pd.DataFrame:
    """Regresion lineal de fatiga vs jornada por jugador.

    Returns:
        DataFrame: dyn_name, r2, slope, p_value, ci_lower, ci_upper.
    """
    if fatigue_df.empty:
        return pd.DataFrame()

    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    results = []
    for player, pdata in fatigue_df.groupby("dyn_name"):
        pdata = pdata.copy()
        pdata["jornada_idx"] = pdata["jornada"].map(lambda j: jornada_order.index(j) if j in jornada_order else -1)
        pdata = pdata[pdata["jornada_idx"] >= 0].sort_values("jornada_idx")

        if len(pdata) < 3:
            results.append({"dyn_name": player, "r2": np.nan, "slope": np.nan,
                            "p_value": np.nan, "ci_lower": np.nan, "ci_upper": np.nan,
                            "n_matches": len(pdata)})
            continue

        x = pdata["jornada_idx"].values.astype(float)
        y = pdata["fatigue_index"].values.astype(float)
        res = stats.linregress(x, y)
        r2 = res.rvalue ** 2

        # 95% CI for slope
        n = len(x)
        se = res.stderr
        t_crit = stats.t.ppf(0.975, n - 2)
        ci_lower = res.slope - t_crit * se
        ci_upper = res.slope + t_crit * se

        results.append({
            "dyn_name": player,
            "r2": round(r2, 4),
            "slope": round(res.slope, 4),
            "p_value": round(res.pvalue, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "n_matches": n,
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Riesgo de lesion
# ---------------------------------------------------------------------------

def compute_injury_risk(physical: pd.DataFrame) -> pd.DataFrame:
    """Calcula riesgo de lesion por jugador.

    Analiza toda la serie temporal de cada jugador (no solo ultimo partido).
    Jugadores con solo 1 partido se excluyen (sin datos comparativos).

    Señales de riesgo evaluadas en cada transicion entre partidos:
    - ACWR: carga del partido / media de partidos previos
    - Caida PSV-99: descenso sostenido de velocidad maxima
    - Pico de carga: subida brusca de carga entre partidos consecutivos
    - Tendencia PSV-99: pendiente negativa a lo largo de la serie
    - Ratio sprint alto: proporcion de sprint sobre distancia total

    Returns:
        DataFrame: dyn_name, risk_level, risk_score, acwr, sprint_ratio,
        psv99_change_pct, load_change_pct, risk_factors, n_matches.
    """
    if physical.empty:
        return pd.DataFrame()

    df = physical.copy()
    df["jornada"] = df["match_id"].map(lambda x: MATCHES.get(x, {}).get("jornada", ""))
    jornada_order = ["J10", "J16", "J18", "J23", "J30", "J37"]
    df["jornada_idx"] = df["jornada"].map(lambda j: jornada_order.index(j) if j in jornada_order else -1)
    df = df.sort_values(["dyn_name", "jornada_idx"])

    load_cols = ["Distance", "HSR Distance", "Sprint Distance"]
    available_load = [c for c in load_cols if c in df.columns]

    results = []
    for player, pdata in df.groupby("dyn_name"):
        pdata = pdata.sort_values("jornada_idx").copy()
        n_matches = len(pdata)

        if not available_load:
            continue

        pdata["match_load"] = pdata[available_load].sum(axis=1)

        # Skip players with only 1 match — no comparison possible
        if n_matches < 2:
            results.append({
                "dyn_name": player,
                "risk_level": "sin_datos",
                "risk_score": np.nan,
                "acwr": np.nan,
                "sprint_ratio": np.nan,
                "psv99_change_pct": np.nan,
                "load_change_pct": np.nan,
                "risk_factors": "Solo 1 partido — sin datos comparativos",
                "n_matches": n_matches,
            })
            continue

        factors = []
        risk_components = []

        # --- 1. ACWR across all transitions (max risk) ---
        acwr_values = []
        for i in range(1, n_matches):
            current_load = pdata["match_load"].iloc[i]
            prior_mean = pdata["match_load"].iloc[:i].mean()
            acwr_i = current_load / prior_mean if prior_mean > 0 else 1.0
            acwr_values.append(acwr_i)

        lo, hi = ACWR_THRESHOLDS
        acwr_violations = [a for a in acwr_values if a < lo or a > hi]
        worst_acwr = max(acwr_values, key=lambda a: abs(a - 1.0)) if acwr_values else 1.0

        if acwr_violations:
            severity = len(acwr_violations) / len(acwr_values)
            risk_components.append(0.3 * min(severity * 2, 1.0))
            worst_v = max(acwr_violations, key=lambda a: abs(a - 1.0))
            factors.append(f"ACWR={worst_v:.2f} fuera de [{lo},{hi}] en {len(acwr_violations)}/{len(acwr_values)} transiciones")

        # --- 2. PSV-99 drops across series ---
        psv_col = "PSV-99"
        psv_changes = []
        worst_psv_change = 0.0
        if psv_col in pdata.columns:
            psv_vals = pdata[psv_col].values
            for i in range(1, len(psv_vals)):
                if psv_vals[i - 1] > 0:
                    pct = ((psv_vals[i] - psv_vals[i - 1]) / psv_vals[i - 1]) * 100
                    psv_changes.append(pct)

            drops = [c for c in psv_changes if c < -PSV99_DROP_THRESHOLD]
            if drops:
                worst_psv_change = min(drops)
                severity = len(drops) / len(psv_changes) if psv_changes else 0
                risk_components.append(0.25 * min(severity * 2, 1.0))
                factors.append(f"PSV-99 cayó >{PSV99_DROP_THRESHOLD}% en {len(drops)}/{len(psv_changes)} transiciones (peor: {worst_psv_change:.1f}%)")

            # Trend: overall PSV-99 declining?
            if len(psv_vals) >= 3:
                psv_trend = (psv_vals[-1] - psv_vals[0]) / psv_vals[0] * 100 if psv_vals[0] > 0 else 0
                if psv_trend < -8:
                    risk_components.append(0.15)
                    factors.append(f"Tendencia PSV-99: {psv_trend:.1f}% en la serie")

        # --- 3. Load spikes across series ---
        load_changes = []
        worst_load_change = 0.0
        load_vals = pdata["match_load"].values
        for i in range(1, len(load_vals)):
            if load_vals[i - 1] > 0:
                pct = ((load_vals[i] - load_vals[i - 1]) / load_vals[i - 1]) * 100
                load_changes.append(pct)

        spikes = [c for c in load_changes if c > LOAD_SPIKE_THRESHOLD]
        if spikes:
            worst_load_change = max(spikes)
            severity = len(spikes) / len(load_changes) if load_changes else 0
            risk_components.append(0.2 * min(severity * 2, 1.0))
            factors.append(f"Carga subió >{LOAD_SPIKE_THRESHOLD}% en {len(spikes)}/{len(load_changes)} transiciones (peor: {worst_load_change:.1f}%)")

        # --- 4. High cumulative load ---
        total_load = pdata["match_load"].sum()
        avg_load_per_match = pdata["match_load"].mean()
        load_cv = pdata["match_load"].std() / avg_load_per_match if avg_load_per_match > 0 else 0
        if load_cv > 0.25:
            risk_components.append(0.1)
            factors.append(f"Variabilidad de carga alta (CV={load_cv:.2f})")

        # --- 5. Sprint ratio ---
        sprint_ratio = 0.0
        if "Sprint Distance" in pdata.columns and "Distance" in pdata.columns:
            sprint_ratio = (pdata["Sprint Distance"].mean() / pdata["Distance"].mean() * 100) if pdata["Distance"].mean() > 0 else 0

        # --- Aggregate risk score ---
        risk_score = min(sum(risk_components), 1.0)

        if risk_score < 0.33:
            risk_level = "bajo"
        elif risk_score < 0.66:
            risk_level = "medio"
        else:
            risk_level = "alto"

        results.append({
            "dyn_name": player,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 3),
            "acwr": round(worst_acwr, 3),
            "sprint_ratio": round(sprint_ratio, 2),
            "psv99_change_pct": round(worst_psv_change, 2) if worst_psv_change != 0 else round(psv_changes[-1], 2) if psv_changes else 0.0,
            "load_change_pct": round(worst_load_change, 2) if worst_load_change != 0 else round(load_changes[-1], 2) if load_changes else 0.0,
            "risk_factors": "; ".join(factors) if factors else "Ninguno",
            "n_matches": n_matches,
        })

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Correlaciones
# ---------------------------------------------------------------------------

def _prepare_dynamic_for_correlations(dynamic_sev: pd.DataFrame) -> pd.DataFrame:
    """Prepara columnas derivadas necesarias para los pares de correlacion."""
    df = dynamic_sev.copy()

    # Numeric pressure (ordinal encoding)
    pressure_map = {"no_pressure": 0, "very_low": 1, "low": 1, "low_pressure": 1,
                    "medium": 2, "medium_pressure": 2,
                    "high": 3, "high_pressure": 3,
                    "very_high": 4, "very_high_pressure": 4}
    if "overall_pressure_start" in df.columns:
        df["pressure_numeric"] = df["overall_pressure_start"].map(pressure_map)

    # Loss of possession binary
    if "end_type" in df.columns:
        df["end_type_loss"] = (df["end_type"] == "possession_loss").astype(float)
        df["end_type_recovery"] = (df["end_type"].isin(
            ["direct_regain", "indirect_regain"]
        )).astype(float)

    # Boolean to numeric
    for col in ["forward_momentum", "lead_to_shot"]:
        if col in df.columns:
            df[f"{col}_num"] = df[col].astype(float)

    return df


def compute_correlations(dynamic_sev: pd.DataFrame) -> pd.DataFrame:
    """Calcula correlaciones para pares configurados.

    Returns:
        DataFrame: var_x, var_y, label_x, label_y, pearson, spearman,
        statistic, p_value, n_obs, significant, ci_lower, ci_upper, interpretation.
    """
    if dynamic_sev.empty:
        return pd.DataFrame()

    df = _prepare_dynamic_for_correlations(dynamic_sev)
    results = []

    for pair in CORRELATION_PAIRS:
        var_x = pair["var_x"]
        var_y = pair["var_y"]

        if var_x not in df.columns or var_y not in df.columns:
            continue

        valid = df[[var_x, var_y]].dropna()
        if len(valid) < 10:
            continue

        x = valid[var_x].astype(float)
        y = valid[var_y].astype(float)

        # Pearson
        try:
            pearson_r, pearson_p = stats.pearsonr(x, y)
        except Exception:
            pearson_r, pearson_p = np.nan, np.nan

        # Spearman
        try:
            spearman_r, spearman_p = stats.spearmanr(x, y)
        except Exception:
            spearman_r, spearman_p = np.nan, np.nan

        # Use Spearman as primary (more robust for non-normal data)
        stat = spearman_r if pd.notna(spearman_r) else pearson_r
        p_val = spearman_p if pd.notna(spearman_p) else pearson_p

        # Bootstrap 95% CI
        n = len(x)
        ci_lower, ci_upper = _bootstrap_ci(x.values, y.values, n_boot=500)

        # Interpretation
        abs_r = abs(stat) if pd.notna(stat) else 0
        if abs_r < 0.1:
            interp = "Despreciable"
        elif abs_r < 0.3:
            interp = "Débil"
        elif abs_r < 0.5:
            interp = "Moderada"
        elif abs_r < 0.7:
            interp = "Fuerte"
        else:
            interp = "Muy fuerte"

        direction = "positiva" if (pd.notna(stat) and stat > 0) else "negativa"
        interp = f"{interp} {direction}"

        results.append({
            "var_x": pair["label_x"],
            "var_y": pair["label_y"],
            "pearson": round(pearson_r, 4) if pd.notna(pearson_r) else None,
            "spearman": round(spearman_r, 4) if pd.notna(spearman_r) else None,
            "statistic": round(stat, 4) if pd.notna(stat) else None,
            "p_value": round(p_val, 6) if pd.notna(p_val) else None,
            "n_obs": n,
            "significant": bool(pd.notna(p_val) and p_val < 0.05),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "interpretation": interp,
            "raw_var_x": var_x,
            "raw_var_y": var_y,
        })

    return pd.DataFrame(results)


def _bootstrap_ci(x: np.ndarray, y: np.ndarray, n_boot: int = 500, alpha: float = 0.05) -> tuple:
    """Bootstrap confidence interval for Spearman correlation."""
    rng = np.random.default_rng(RANDOM_STATE)
    n = len(x)
    boot_corrs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            r, _ = stats.spearmanr(x[idx], y[idx])
            if pd.notna(r):
                boot_corrs.append(r)
        except Exception:
            pass

    if not boot_corrs:
        return (0.0, 0.0)

    boot_arr = np.array(boot_corrs)
    lo = float(np.percentile(boot_arr, 100 * alpha / 2))
    hi = float(np.percentile(boot_arr, 100 * (1 - alpha / 2)))
    return (round(lo, 4), round(hi, 4))


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------

def run_inference_pipeline(
    scores_all: pd.DataFrame,
    aggregated: pd.DataFrame,
    physical: pd.DataFrame,
    dynamic_sev: pd.DataFrame,
) -> dict:
    """Ejecuta todo el pipeline de inferencia M3.

    Returns:
        dict con claves: clustering, fatigue, fatigue_stats, risk, correlations.
    """
    # Clustering
    clustering = run_clustering(aggregated, physical, mode="tactical")

    # Fatiga
    fatigue = compute_fatigue_index(physical)
    fatigue_stats = compute_fatigue_model_stats(fatigue) if not fatigue.empty else pd.DataFrame()

    # Riesgo
    risk = compute_injury_risk(physical)

    # Correlaciones
    correlations = compute_correlations(dynamic_sev)

    return {
        "clustering": clustering,
        "fatigue": fatigue,
        "fatigue_stats": fatigue_stats,
        "risk": risk,
        "correlations": correlations,
    }
