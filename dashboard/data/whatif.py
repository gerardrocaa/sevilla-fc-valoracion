"""Motor de computo para Modulo 4: Escenarios What-If.

Funciones puras sin dependencia de Streamlit.
Monte Carlo bootstrap, ausencia de jugador, bloque defensivo,
rotacion por fatiga y formacion alternativa.
"""

import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

from dashboard.config import (
    DIM_COLS,
    FORMATION_TEMPLATES,
    MATCHES,
    POSITION_COMPATIBILITY,
    POSITION_TO_PROFILE,
    PROFILE_WEIGHTS,
    WHATIF_DEFAULT_ITERATIONS,
    WHATIF_RANDOM_STATE,
)

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Motor base: distribuciones y Monte Carlo
# ---------------------------------------------------------------------------

def build_player_metric_distributions(scores_all: pd.DataFrame) -> dict:
    """Construye distribuciones empiricas por jugador y metrica.

    Args:
        scores_all: DataFrame con scores por jugador y partido.

    Returns:
        dict {jugador: {metrica: {mean, std, min, max, values, n}}}
    """
    distributions: dict = {}
    dim_cols = [c for c in DIM_COLS + ["composite_score"] if c in scores_all.columns]

    for player, pdata in scores_all.groupby("player_name"):
        distributions[player] = {}
        for col in dim_cols:
            vals = pdata[col].dropna().values
            if len(vals) == 0:
                continue
            distributions[player][col] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "values": vals.tolist(),
                "n": len(vals),
            }

    return distributions


def monte_carlo_simulate(
    distributions: dict,
    players: list,
    metrics: list,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
    method: str = "bootstrap",
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """Simula distribuciones de metricas con Monte Carlo.

    Args:
        distributions: output de build_player_metric_distributions.
        players: lista de jugadores a simular.
        metrics: lista de metricas a simular.
        n_iterations: numero de iteraciones.
        method: 'bootstrap' (remuestreo) o 'truncated_normal'.
        rng: generador de numeros aleatorios.

    Returns:
        DataFrame con columnas: player, metric, iteration, value.
    """
    if rng is None:
        rng = np.random.default_rng(WHATIF_RANDOM_STATE)

    rows = []
    for player in players:
        if player not in distributions:
            continue
        for metric in metrics:
            if metric not in distributions[player]:
                continue
            dist = distributions[player][metric]
            vals = np.array(dist["values"])

            if method == "bootstrap":
                # Remuestreo con reemplazo
                samples = rng.choice(vals, size=(n_iterations, len(vals)), replace=True)
                sim_means = samples.mean(axis=1)
            else:
                # Normal truncada
                mean, std = dist["mean"], dist["std"]
                if std == 0:
                    sim_means = np.full(n_iterations, mean)
                else:
                    raw = rng.normal(mean, std, size=n_iterations)
                    sim_means = np.clip(raw, dist["min"], dist["max"])

            for i, val in enumerate(sim_means):
                rows.append({
                    "player": player,
                    "metric": metric,
                    "iteration": i,
                    "value": float(val),
                })

    return pd.DataFrame(rows)


def summarize_simulations(
    simulations: pd.DataFrame,
    percentiles: list | None = None,
) -> pd.DataFrame:
    """Resume simulaciones con percentiles.

    Returns:
        DataFrame con columnas: player, metric, mean, P10, P25, P50, P75, P90.
    """
    if percentiles is None:
        percentiles = [10, 25, 50, 75, 90]

    if simulations.empty:
        return pd.DataFrame()

    grouped = simulations.groupby(["player", "metric"])["value"]
    summary = grouped.agg(["mean", "std"]).reset_index()

    for p in percentiles:
        summary[f"P{p}"] = grouped.quantile(p / 100).values

    return summary


# ---------------------------------------------------------------------------
# Escenario 1: Ausencia de jugador
# ---------------------------------------------------------------------------

def compute_player_event_contribution(
    dynamic_sev: pd.DataFrame,
    player: str,
) -> dict:
    """Calcula contribucion media del jugador por partido en dynamic events.

    Returns:
        dict con metricas de contribucion media por partido.
    """
    pdf = dynamic_sev[dynamic_sev["player_name"] == player]
    if pdf.empty:
        return {}

    per_match = pdf.groupby("match_id").agg(
        xthreat_sum=("player_targeted_xthreat", lambda s: s.sum()),
        pressing_count=("event_subtype", lambda s: (s.isin(["pressing", "counter_press", "recovery_press"])).sum()),
        runs_count=("event_type", lambda s: (s == "off_ball_run").sum()),
        pass_options=("event_type", lambda s: (s == "passing_option").sum()),
        total_events=("event_type", "count"),
        lead_to_shot=("lead_to_shot", lambda s: s.sum() if s.dtype == bool else s.astype(float).sum()),
    ).reset_index()

    return {
        "xthreat_mean": float(per_match["xthreat_sum"].mean()),
        "pressing_mean": float(per_match["pressing_count"].mean()),
        "runs_mean": float(per_match["runs_count"].mean()),
        "pass_options_mean": float(per_match["pass_options"].mean()),
        "events_mean": float(per_match["total_events"].mean()),
        "lead_to_shot_mean": float(per_match["lead_to_shot"].mean()),
        "n_matches": len(per_match),
    }


def find_positional_peers(
    aggregated: pd.DataFrame,
    player: str,
) -> list[str]:
    """Encuentra jugadores del mismo perfil posicional.

    Returns:
        Lista de nombres de pares posicionales (excluyendo al jugador).
    """
    player_row = aggregated[aggregated["player_name"] == player]
    if player_row.empty:
        return []

    profile = player_row.iloc[0].get("profile", "")
    if not profile:
        return []

    # Buscar jugadores con mismo perfil o perfil compatible
    compatible = POSITION_COMPATIBILITY.get(profile, [profile])
    peers = aggregated[
        (aggregated["profile"].isin(compatible))
        & (aggregated["player_name"] != player)
    ]["player_name"].tolist()

    return sorted(peers)


def simulate_player_absence(
    scores_all: pd.DataFrame,
    dynamic_sev: pd.DataFrame,
    aggregated: pd.DataFrame,
    absent_player: str,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Simula impacto de ausencia de un jugador.

    Returns:
        dict con baseline, simulado, redistribucion, supuestos.
    """
    rng = np.random.default_rng(WHATIF_RANDOM_STATE)

    # 1. Contribucion del ausente
    contribution = compute_player_event_contribution(dynamic_sev, absent_player)
    peers = find_positional_peers(aggregated, absent_player)

    # 2. Scores del equipo por partido
    dim_cols = [c for c in DIM_COLS + ["composite_score"] if c in scores_all.columns]
    team_by_match = scores_all.groupby("match_id")[dim_cols].mean().reset_index()

    # 3. Scores sin el jugador por partido
    without = scores_all[scores_all["player_name"] != absent_player]
    team_without = without.groupby("match_id")[dim_cols].mean().reset_index()

    # 4. Bootstrap baseline y simulado
    baseline_rows = []
    simulated_rows = []
    match_ids_with = team_by_match["match_id"].values
    match_ids_without = team_without["match_id"].values

    for _i in range(n_iterations):
        # Baseline: remuestreo de partidos con jugador
        idx_b = rng.choice(len(match_ids_with), size=len(match_ids_with), replace=True)
        baseline_sample = team_by_match.iloc[idx_b][dim_cols].mean()
        baseline_rows.append(baseline_sample.to_dict())

        # Simulado: remuestreo de partidos sin jugador
        idx_s = rng.choice(len(match_ids_without), size=len(match_ids_without), replace=True)
        simulated_sample = team_without.iloc[idx_s][dim_cols].mean()
        simulated_rows.append(simulated_sample.to_dict())

    baseline_df = pd.DataFrame(baseline_rows)
    simulated_df = pd.DataFrame(simulated_rows)

    # 5. Resumen con percentiles
    def _summarize(df):
        result = {}
        for col in dim_cols:
            result[col] = {
                "mean": float(df[col].mean()),
                "P25": float(df[col].quantile(0.25)),
                "P50": float(df[col].quantile(0.50)),
                "P75": float(df[col].quantile(0.75)),
            }
        return result

    baseline_summary = _summarize(baseline_df)
    simulated_summary = _summarize(simulated_df)

    # 6. Info del ausente
    absent_info = aggregated[aggregated["player_name"] == absent_player]
    absent_data = {}
    if not absent_info.empty:
        row = absent_info.iloc[0]
        absent_data = {
            "player_name": absent_player,
            "profile": row.get("profile", ""),
            "composite_score": float(row.get("composite_score", 0)),
            "total_minutes": float(row.get("total_minutes", 0)),
            "n_matches": int(row.get("n_matches", 0)),
        }

    # 7. Redistribucion entre pares
    redistribution = []
    if peers:
        peer_scores = aggregated[aggregated["player_name"].isin(peers)]
        total_score = peer_scores["composite_score"].sum()
        for _, pr in peer_scores.iterrows():
            weight = pr["composite_score"] / total_score if total_score > 0 else 1 / len(peers)
            redistribution.append({
                "player_name": pr["player_name"],
                "profile": pr.get("profile", ""),
                "composite_score": float(pr.get("composite_score", 0)),
                "weight": float(weight),
            })

    supuestos = [
        "Bootstrap con remuestreo a nivel de partido (N=6).",
        "Medias de equipo recalculadas excluyendo al jugador ausente.",
        "Redistribucion de contribucion proporcional al composite_score de pares posicionales.",
        "Se asume que los demas jugadores mantienen su rendimiento individual.",
        f"Pares posicionales identificados: {len(peers)} jugadores.",
        f"Iteraciones Monte Carlo: {n_iterations}.",
    ]

    return {
        "baseline": baseline_summary,
        "simulated": simulated_summary,
        "contribution": contribution,
        "absent_data": absent_data,
        "peers": peers,
        "redistribution": redistribution,
        "supuestos": supuestos,
    }


# ---------------------------------------------------------------------------
# Escenario 2: Bloque defensivo
# ---------------------------------------------------------------------------

def compute_block_metrics(
    dynamic_sev: pd.DataFrame,
    block_type: str,
) -> pd.DataFrame:
    """Calcula metricas de eficiencia defensiva para un tipo de bloque.

    Args:
        dynamic_sev: eventos dinamicos del Sevilla.
        block_type: 'high_block', 'medium_block', 'low_block'.

    Returns:
        DataFrame con metricas por partido para ese bloque.
    """
    engagements = dynamic_sev[dynamic_sev["event_type"] == "on_ball_engagement"]
    block_events = engagements[engagements["team_out_of_possession_phase_type"] == block_type]

    if block_events.empty:
        return pd.DataFrame()

    per_match = block_events.groupby("match_id").agg(
        n_events=("event_type", "count"),
        pressing_rate=("event_subtype", lambda s: (s.isin(["pressing", "counter_press", "recovery_press"])).sum() / max(len(s), 1)),
        pressing_chain_mean=("pressing_chain_length", lambda s: s.dropna().mean() if s.dropna().any() else 0),
        danger_neutralized=("player_targeted_xthreat", lambda s: -(s.dropna().sum()) if s.dropna().any() else 0),
        solidity=("end_type", lambda s: (s.isin(["direct_regain", "indirect_regain"])).sum() / max(len(s), 1)),
        recovery_rate=("end_type", lambda s: (s == "direct_regain").sum() / max(len(s), 1)),
    ).reset_index()

    per_match["block_type"] = block_type
    return per_match


def simulate_defensive_block(
    dynamic_sev: pd.DataFrame,
    block_types: list[str],
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Simula y compara metricas entre distintos bloques defensivos.

    Bootstrap a nivel de partido (eventos dentro de un partido correlacionados).

    Returns:
        dict con comparativa por bloque, datos por partido, supuestos.
    """
    rng = np.random.default_rng(WHATIF_RANDOM_STATE)
    metrics_cols = ["pressing_rate", "pressing_chain_mean", "danger_neutralized",
                    "solidity", "recovery_rate", "n_events"]

    all_block_data = {}
    block_summaries = {}

    for bt in block_types:
        per_match = compute_block_metrics(dynamic_sev, bt)
        all_block_data[bt] = per_match

        if per_match.empty or len(per_match) == 0:
            block_summaries[bt] = {m: {"mean": 0, "P25": 0, "P50": 0, "P75": 0, "n_matches": 0, "n_events_total": 0} for m in metrics_cols}
            continue

        # Bootstrap a nivel de partido
        boot_rows = []
        n_matches = len(per_match)
        for _ in range(n_iterations):
            idx = rng.choice(n_matches, size=n_matches, replace=True)
            sample = per_match.iloc[idx]
            boot_rows.append({m: float(sample[m].mean()) for m in metrics_cols if m in sample.columns})

        boot_df = pd.DataFrame(boot_rows)

        summary = {}
        for m in metrics_cols:
            if m not in boot_df.columns:
                summary[m] = {"mean": 0, "P25": 0, "P50": 0, "P75": 0}
                continue
            summary[m] = {
                "mean": float(boot_df[m].mean()),
                "P25": float(boot_df[m].quantile(0.25)),
                "P50": float(boot_df[m].quantile(0.50)),
                "P75": float(boot_df[m].quantile(0.75)),
            }
        summary["n_matches"] = n_matches
        summary["n_events_total"] = int(per_match["n_events"].sum())
        block_summaries[bt] = summary

    # Conteo global de eventos por bloque
    engagements = dynamic_sev[dynamic_sev["event_type"] == "on_ball_engagement"]
    block_counts = {}
    for bt in ["high_block", "medium_block", "low_block"]:
        block_counts[bt] = int((engagements["team_out_of_possession_phase_type"] == bt).sum())
    block_counts["total"] = len(engagements)

    supuestos = [
        "Bootstrap a nivel de partido (eventos dentro de un partido estan correlacionados).",
        "Se analizan solo eventos de tipo 'on_ball_engagement' del Sevilla.",
        "Filtro por 'team_out_of_possession_phase_type' para clasificar el bloque.",
        f"Iteraciones Monte Carlo: {n_iterations}.",
        f"Distribucion de bloques: {', '.join(f'{k}={v}' for k, v in block_counts.items() if k != 'total')}.",
        "Metricas: pressing_rate, cadena de pressing, peligro neutralizado, solidez, tasa de recuperacion.",
    ]

    return {
        "summaries": block_summaries,
        "per_match_data": {bt: df.to_dict("records") if not df.empty else [] for bt, df in all_block_data.items()},
        "block_counts": block_counts,
        "supuestos": supuestos,
    }


# ---------------------------------------------------------------------------
# Escenario 3: Rotacion por carga fisica
# ---------------------------------------------------------------------------

def project_fatigue_curve(
    physical: pd.DataFrame,
    player: str,
    fatigue_df: pd.DataFrame,
    n_future_matches: int = 6,
    rotation_frequency: int = 0,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Proyecta curva de fatiga futura con/sin rotacion.

    Args:
        physical: datos fisicos crudos.
        player: nombre del jugador (dyn_name).
        fatigue_df: DataFrame de fatiga existente (de M3).
        n_future_matches: partidos futuros a proyectar.
        rotation_frequency: 0 = sin rotacion, N = descansa cada N partidos.
        n_iterations: iteraciones MC.

    Returns:
        dict con curva proyectada, estadisticas.
    """
    rng = np.random.default_rng(WHATIF_RANDOM_STATE)

    # Datos historicos del jugador
    player_phys = physical[physical["dyn_name"] == player]
    if player_phys.empty:
        return {"curve": [], "error": f"Sin datos fisicos para {player}"}

    # Calcular carga por partido historica
    load_cols = ["Distance", "HSR Distance", "Sprint Distance"]
    available_load = [c for c in load_cols if c in player_phys.columns]
    if not available_load:
        return {"curve": [], "error": "Sin columnas de carga"}

    match_loads = player_phys[available_load].sum(axis=1).values
    load_mean = float(np.mean(match_loads))
    load_std = float(np.std(match_loads, ddof=1)) if len(match_loads) > 1 else 0.0

    # PSV-99 historico
    psv_vals = player_phys["PSV-99"].dropna().values if "PSV-99" in player_phys.columns else np.array([])
    psv_mean = float(np.mean(psv_vals)) if len(psv_vals) > 0 else 0.0

    # Fatiga actual (ultimo valor conocido)
    player_fatigue = fatigue_df[fatigue_df["dyn_name"] == player] if not fatigue_df.empty else pd.DataFrame()
    if not player_fatigue.empty:
        current_fatigue = float(player_fatigue["fatigue_index"].iloc[-1])
        current_load = float(player_fatigue["cumulative_load"].iloc[-1])
    else:
        current_fatigue = 0.0
        current_load = float(np.sum(match_loads))

    # Proyeccion Monte Carlo
    curves = []
    for _ in range(n_iterations):
        cum_load = current_load
        fatigue_series = [current_fatigue]

        for match_i in range(1, n_future_matches + 1):
            # Descansa si hay rotacion y toca
            if rotation_frequency > 0 and match_i % rotation_frequency == 0:
                match_load = 0.0
            else:
                if load_std > 0:
                    match_load = max(0, rng.normal(load_mean, load_std))
                else:
                    match_load = load_mean

            cum_load += match_load

            # Recalcular fatiga (formula simplificada de M3)
            load_max_projected = current_load + load_mean * n_future_matches
            load_norm = cum_load / load_max_projected if load_max_projected > 0 else 0

            # Fatiga crece con carga acumulada, decrece con descanso
            if match_load == 0:
                # Descanso: fatiga se reduce un 30%
                fatigue = fatigue_series[-1] * 0.7
            else:
                # Juega: fatiga crece
                fatigue = min(1.0, 0.35 * load_norm + 0.65 * fatigue_series[-1] * (1 + 0.05 * rng.standard_normal()))

            fatigue = float(np.clip(fatigue, 0, 1))
            fatigue_series.append(fatigue)

        curves.append(fatigue_series)

    curves_arr = np.array(curves)

    # Resumir
    curve_summary = []
    for j in range(n_future_matches + 1):
        vals = curves_arr[:, j]
        is_rest = rotation_frequency > 0 and j > 0 and j % rotation_frequency == 0
        curve_summary.append({
            "match": j,
            "label": "Actual" if j == 0 else f"+{j}",
            "mean": float(np.mean(vals)),
            "P25": float(np.percentile(vals, 25)),
            "P50": float(np.percentile(vals, 50)),
            "P75": float(np.percentile(vals, 75)),
            "P10": float(np.percentile(vals, 10)),
            "P90": float(np.percentile(vals, 90)),
            "is_rest": is_rest,
        })

    return {
        "curve": curve_summary,
        "load_mean": load_mean,
        "load_std": load_std,
        "psv_mean": psv_mean,
        "current_fatigue": current_fatigue,
        "current_load": current_load,
        "n_historical_matches": len(match_loads),
    }


def simulate_rotation(
    physical: pd.DataFrame,
    fatigue_df: pd.DataFrame,
    fatigue_stats: pd.DataFrame,
    risk_df: pd.DataFrame,
    player: str,
    rotation_frequency: int = 3,
    n_future_matches: int = 6,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Compara proyeccion con y sin rotacion.

    Returns:
        dict con curva baseline, curva con rotacion, comparativa.
    """
    baseline = project_fatigue_curve(
        physical, player, fatigue_df,
        n_future_matches=n_future_matches,
        rotation_frequency=0,
        n_iterations=n_iterations,
    )
    rotated = project_fatigue_curve(
        physical, player, fatigue_df,
        n_future_matches=n_future_matches,
        rotation_frequency=rotation_frequency,
        n_iterations=n_iterations,
    )

    if "error" in baseline or "error" in rotated:
        return {
            "baseline": baseline,
            "rotated": rotated,
            "error": baseline.get("error", rotated.get("error", "")),
        }

    # Riesgo actual del jugador
    player_risk = {}
    if not risk_df.empty:
        pr = risk_df[risk_df["dyn_name"] == player]
        if not pr.empty:
            player_risk = {
                "risk_level": pr.iloc[0].get("risk_level", ""),
                "risk_score": float(pr.iloc[0].get("risk_score", 0)),
            }

    # Fatiga stats
    player_stats = {}
    if not fatigue_stats.empty:
        ps = fatigue_stats[fatigue_stats["dyn_name"] == player]
        if not ps.empty:
            player_stats = {
                "slope": float(ps.iloc[0].get("slope", 0)),
                "r2": float(ps.iloc[0].get("r2", 0)),
            }

    # Pico de fatiga
    baseline_peak = max(p["P50"] for p in baseline["curve"])
    rotated_peak = max(p["P50"] for p in rotated["curve"])
    reduction_pct = ((baseline_peak - rotated_peak) / baseline_peak * 100) if baseline_peak > 0 else 0

    supuestos = [
        "Bootstrap de carga por partido basado en distribucion historica del jugador.",
        f"Carga media por partido: {baseline['load_mean']:,.0f}m (std: {baseline['load_std']:,.0f}m).",
        f"Frecuencia de rotacion: descansa cada {rotation_frequency} partidos." if rotation_frequency > 0 else "Sin rotacion.",
        "Descanso reduce fatiga un 30% (factor 0.7).",
        "Fatiga crece proporcionalmente a carga acumulada normalizada.",
        f"Iteraciones: {n_iterations}. Rango observado: {baseline['n_historical_matches']} partidos.",
    ]

    return {
        "baseline": baseline,
        "rotated": rotated,
        "player_risk": player_risk,
        "player_stats": player_stats,
        "peak_baseline": baseline_peak,
        "peak_rotated": rotated_peak,
        "reduction_pct": reduction_pct,
        "supuestos": supuestos,
    }


# ---------------------------------------------------------------------------
# Escenario 4: Formacion alternativa
# ---------------------------------------------------------------------------

def build_default_lineup(
    aggregated: pd.DataFrame,
    formation: str,
) -> list[dict]:
    """Asigna los mejores jugadores disponibles a cada posicion de la formacion.

    Args:
        aggregated: DataFrame con player_name, profile, composite_score.
        formation: clave de FORMATION_TEMPLATES (e.g., '4-3-3').

    Returns:
        Lista de dicts {player_name, position, profile, composite_score}.
    """
    template = FORMATION_TEMPLATES.get(formation)
    if template is None:
        return []

    available = aggregated.copy().sort_values("composite_score", ascending=False)
    assigned = set()
    lineup = []

    for position, count in template.items():
        compatible_profiles = POSITION_COMPATIBILITY.get(position, [position])
        candidates = available[
            (available["profile"].isin(compatible_profiles))
            & (~available["player_name"].isin(assigned))
        ]

        for i in range(count):
            if i < len(candidates):
                player = candidates.iloc[i]
                lineup.append({
                    "player_name": player["player_name"],
                    "position": position,
                    "profile": player["profile"],
                    "composite_score": float(player["composite_score"]),
                })
                assigned.add(player["player_name"])
            else:
                # No hay suficientes jugadores para esta posicion
                lineup.append({
                    "player_name": f"(vacante {position})",
                    "position": position,
                    "profile": position,
                    "composite_score": 0.0,
                })

    return lineup


def compute_formation_metrics(
    scores_all: pd.DataFrame,
    dynamic_sev: pd.DataFrame,
    lineup: list[dict],
    formation_name: str,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Calcula metricas de equipo para una formacion con su lineup.

    Returns:
        dict con metricas D1-D6 del equipo, cobertura espacial.
    """
    rng = np.random.default_rng(WHATIF_RANDOM_STATE)
    dim_cols = [c for c in DIM_COLS if c in scores_all.columns]

    player_names = [p["player_name"] for p in lineup if not p["player_name"].startswith("(vacante")]

    # Scores por jugador y partido
    player_scores = scores_all[scores_all["player_name"].isin(player_names)]

    # Recalcular composite con pesos de la NUEVA posicion
    recalculated = []
    for p in lineup:
        if p["player_name"].startswith("(vacante"):
            continue
        pdata = player_scores[player_scores["player_name"] == p["player_name"]]
        new_profile = p["position"]
        weights = PROFILE_WEIGHTS.get(new_profile, PROFILE_WEIGHTS.get(p["profile"], [1/6]*6))

        for _, row in pdata.iterrows():
            dim_values = [row.get(d, 0) for d in dim_cols]
            new_composite = sum(w * v for w, v in zip(weights, dim_values))
            entry = {d: row[d] for d in dim_cols if d in row.index}
            entry["player_name"] = p["player_name"]
            entry["match_id"] = row.get("match_id", "")
            entry["composite_score_new"] = float(new_composite)
            recalculated.append(entry)

    if not recalculated:
        return {"team_metrics": {}, "lineup": lineup, "formation": formation_name}

    recalc_df = pd.DataFrame(recalculated)

    # Bootstrap de metricas de equipo
    team_by_match = recalc_df.groupby("match_id").agg(
        {d: "mean" for d in dim_cols}
    ).reset_index()
    team_by_match["composite_mean"] = recalc_df.groupby("match_id")["composite_score_new"].mean().values

    boot_rows = []
    n_matches = len(team_by_match)
    if n_matches > 0:
        for _ in range(n_iterations):
            idx = rng.choice(n_matches, size=n_matches, replace=True)
            sample = team_by_match.iloc[idx]
            row = {d: float(sample[d].mean()) for d in dim_cols}
            row["composite_mean"] = float(sample["composite_mean"].mean())
            boot_rows.append(row)

    boot_df = pd.DataFrame(boot_rows) if boot_rows else pd.DataFrame()

    team_metrics = {}
    all_metric_cols = dim_cols + ["composite_mean"]
    for col in all_metric_cols:
        if col in boot_df.columns:
            team_metrics[col] = {
                "mean": float(boot_df[col].mean()),
                "P25": float(boot_df[col].quantile(0.25)),
                "P50": float(boot_df[col].quantile(0.50)),
                "P75": float(boot_df[col].quantile(0.75)),
            }

    # Cobertura espacial
    spatial = _compute_spatial_coverage(dynamic_sev, player_names)

    return {
        "team_metrics": team_metrics,
        "lineup": lineup,
        "formation": formation_name,
        "n_players": len(player_names),
        "spatial_coverage": spatial,
    }


def _compute_spatial_coverage(dynamic_sev: pd.DataFrame, players: list) -> dict:
    """Calcula distribucion de zonas para los jugadores del lineup."""
    pdf = dynamic_sev[dynamic_sev["player_name"].isin(players)]
    if pdf.empty or "channel" not in pdf.columns:
        return {}

    channel_dist = pdf["channel"].value_counts(normalize=True).to_dict()
    third_dist = pdf["third"].value_counts(normalize=True).to_dict() if "third" in pdf.columns else {}

    return {"channels": channel_dist, "thirds": third_dist}


def simulate_formation_comparison(
    scores_all: pd.DataFrame,
    aggregated: pd.DataFrame,
    dynamic_sev: pd.DataFrame,
    formation_a: str,
    formation_b: str,
    lineup_a: list[dict] | None = None,
    lineup_b: list[dict] | None = None,
    n_iterations: int = WHATIF_DEFAULT_ITERATIONS,
) -> dict:
    """Compara dos formaciones con lineups.

    Returns:
        dict con metricas A, metricas B, comparativa, supuestos.
    """
    if lineup_a is None:
        lineup_a = build_default_lineup(aggregated, formation_a)
    if lineup_b is None:
        lineup_b = build_default_lineup(aggregated, formation_b)

    metrics_a = compute_formation_metrics(scores_all, dynamic_sev, lineup_a, formation_a, n_iterations)
    metrics_b = compute_formation_metrics(scores_all, dynamic_sev, lineup_b, formation_b, n_iterations)

    # Comparativa
    comparison = {}
    dim_cols = [c for c in DIM_COLS + ["composite_mean"] if c in metrics_a.get("team_metrics", {})]
    for col in dim_cols:
        ma = metrics_a["team_metrics"].get(col, {})
        mb = metrics_b["team_metrics"].get(col, {})
        mean_a = ma.get("mean", 0)
        mean_b = mb.get("mean", 0)
        comparison[col] = {
            "formation_a": mean_a,
            "formation_b": mean_b,
            "diff": mean_b - mean_a,
            "diff_pct": ((mean_b - mean_a) / mean_a * 100) if mean_a != 0 else 0,
        }

    supuestos = [
        f"Formacion A: {formation_a} ({len(lineup_a)} posiciones).",
        f"Formacion B: {formation_b} ({len(lineup_b)} posiciones).",
        "Composite score recalculado con pesos de la NUEVA posicion.",
        "Bootstrap de metricas de equipo a nivel de partido.",
        "Jugadores asignados por mejor composite_score entre perfiles compatibles.",
        f"Iteraciones Monte Carlo: {n_iterations}.",
    ]

    return {
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "comparison": comparison,
        "supuestos": supuestos,
    }
