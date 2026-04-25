"""Pipeline de calculo extraido del Modulo 1.

Funciones puras sin dependencia de Streamlit.
Reproduce exactamente la logica del notebook Modulo1_Descripcion_Desempeno.ipynb.
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from dashboard.config import (
    D1_WEIGHTS,
    D2_WEIGHTS,
    D3_WEIGHTS,
    D4_WEIGHTS,
    D5_WEIGHTS,
    D6_WEIGHTS,
    DIM_COLS,
    MATCH_IDS,
    MATCHES,
    MIN_MINUTES,
    PHYS_TO_DYN,
    POSITION_TO_PROFILE,
    PROFILE_WEIGHTS,
)

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def per_90(count: float, minutes: float) -> float:
    if minutes <= 0:
        return 0.0
    return (count / minutes) * 90.0


def _get_sev_events(dynamic_sev: pd.DataFrame, event_type=None, event_subtype=None):
    mask = pd.Series(True, index=dynamic_sev.index)
    if event_type is not None:
        mask &= dynamic_sev["event_type"] == event_type
    if event_subtype is not None:
        if isinstance(event_subtype, list):
            mask &= dynamic_sev["event_subtype"].isin(event_subtype)
        else:
            mask &= dynamic_sev["event_subtype"] == event_subtype
    return dynamic_sev[mask].copy()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_dynamic_events(data_dir: Path) -> pd.DataFrame:
    dfs = []
    for mid in MATCH_IDS:
        fpath = data_dir / f"{mid}_dynamic_events.csv"
        if not fpath.exists():
            fpath = data_dir / f"{mid}_dynamic_events (1).csv"
        df = pd.read_csv(fpath, low_memory=False)
        df["match_id"] = mid
        dfs.append(df)
    dynamic_all = pd.concat(dfs, ignore_index=True)
    dynamic_sev = dynamic_all[dynamic_all["team_shortname"] == "Sevilla FC"].copy()
    return dynamic_sev


def load_physical_data(data_dir: Path) -> pd.DataFrame:
    physical = pd.read_csv(data_dir / "Datos fisicos de los partidos.csv", sep=";")
    physical["match_id"] = physical["Match ID"].astype(int)
    physical["dyn_name"] = physical["Player"].map(PHYS_TO_DYN)
    return physical


def load_espn_events(data_dir: Path) -> pd.DataFrame:
    espn_matches = {mid: m for mid, m in MATCHES.items() if m["espn_file"] is not None}
    dfs = []
    for mid, m in espn_matches.items():
        fpath = data_dir / m["espn_file"]
        df = pd.read_csv(fpath, low_memory=False)
        df = df.loc[:, ~df.columns.duplicated()]
        sev_mask = df["Team"].str.contains("Sev", case=False, na=False)
        df_sev = df[sev_mask].copy()
        df_sev["match_id"] = mid
        dfs.append(df_sev)
    return pd.concat(dfs, ignore_index=True)


def build_player_registry(data_dir: Path) -> pd.DataFrame:
    records = []
    for mid in MATCH_IDS:
        fpath = data_dir / f"{mid}_match.json"
        with open(fpath, "r") as f:
            match_data = json.load(f)

        if "Sevilla" in match_data["away_team"]["name"]:
            sev_team_id = match_data["away_team"]["id"]
        else:
            sev_team_id = match_data["home_team"]["id"]

        for p in match_data["players"]:
            if p["team_id"] != sev_team_id:
                continue
            role = p.get("player_role", {})
            pt = p.get("playing_time", {})
            total_pt = pt.get("total") if pt else None
            minutes_played = total_pt["minutes_played"] if total_pt else 0

            records.append({
                "match_id": mid,
                "player_id": p["id"],
                "player_name": p["short_name"],
                "full_name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                "position_acronym": role.get("acronym", "SUB"),
                "position_name": role.get("name", "Substitute"),
                "position_group": role.get("position_group", "Other"),
                "minutes_played": round(minutes_played, 1),
                "start_time": p.get("start_time"),
                "end_time": p.get("end_time"),
            })

    registry = pd.DataFrame(records)
    registry = registry[registry["minutes_played"] > 0].copy()
    registry["match_label"] = registry["match_id"].map(lambda x: MATCHES[x]["label"])
    registry["jornada"] = registry["match_id"].map(lambda x: MATCHES[x]["jornada"])
    registry["profile"] = registry["position_acronym"].map(POSITION_TO_PROFILE)
    registry["profile"] = registry["profile"].fillna("WM")
    return registry


# ---------------------------------------------------------------------------
# Dimension computations
# ---------------------------------------------------------------------------

def _build_qualifying(registry_scoring: pd.DataFrame) -> pd.DataFrame:
    return registry_scoring[registry_scoring["minutes_played"] >= MIN_MINUTES][
        ["player_name", "match_id", "minutes_played"]
    ].copy()


def compute_d1(qualifying, dynamic_sev, espn_sev, espn_match_ids):
    possessions = _get_sev_events(dynamic_sev, "player_possession")
    records = []

    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        pp = possessions[(possessions["player_name"] == player) & (possessions["match_id"] == mid)]

        targeted_xt = pp["player_targeted_xthreat"].dropna()
        mean_xthreat = targeted_xt.mean() if len(targeted_xt) > 0 else 0.0

        passes = pp[pp["pass_outcome"].notna()]
        pass_success_rate = (passes["pass_outcome"] == "successful").mean() if len(passes) > 0 else 0.0

        carries = (pp["carry"] == True).sum() if "carry" in pp.columns else 0
        carries_p90 = per_90(carries, minutes)

        line_break_opts = pp["n_passing_options_line_break"].dropna()
        mean_line_break = line_break_opts.mean() if len(line_break_opts) > 0 else 0.0

        fm_count = (pp["forward_momentum"] == True).sum()
        fm_rate = fm_count / len(pp) if len(pp) > 0 else 0.0

        xa_p90 = np.nan
        if mid in espn_match_ids:
            espn_player = espn_sev[
                (espn_sev["match_id"] == mid)
                & (espn_sev["toucher"].str.contains(
                    player.split()[-1] if len(player.split()) > 1 else player,
                    case=False, na=False,
                ))
            ]
            xa_p90 = per_90(espn_player["xA"].sum(), minutes) if len(espn_player) > 0 and espn_player["xA"].sum() > 0 else 0.0

        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d1_xthreat_mean": mean_xthreat, "d1_pass_success": pass_success_rate,
            "d1_carries_p90": carries_p90, "d1_line_break_opts": mean_line_break,
            "d1_forward_momentum": fm_rate, "d1_xa_p90": xa_p90,
        })
    return pd.DataFrame(records)


def compute_d2(qualifying, dynamic_sev, espn_sev, espn_match_ids):
    possessions = _get_sev_events(dynamic_sev, "player_possession")
    obr = _get_sev_events(dynamic_sev, "off_ball_run")
    records = []

    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        pp = possessions[(possessions["player_name"] == player) & (possessions["match_id"] == mid)]
        runs = obr[(obr["player_name"] == player) & (obr["match_id"] == mid)]

        lts_rate = pp["lead_to_shot"].mean() if len(pp) > 0 else 0.0

        shots = pp[pp["end_type"] == "shot"] if "end_type" in pp.columns else pd.DataFrame()
        shots_p90 = per_90(len(shots), minutes)

        dangerous_runs = runs[runs["dangerous"] == True]
        dangerous_runs_p90 = per_90(len(dangerous_runs), minutes)

        pen_runs = runs[runs["event_subtype"].isin(["behind", "run_ahead_of_the_ball"])]
        pen_runs_p90 = per_90(len(pen_runs), minutes)

        xg_p90 = np.nan
        if mid in espn_match_ids:
            espn_player = espn_sev[
                (espn_sev["match_id"] == mid)
                & (espn_sev["toucher"].str.contains(
                    player.split()[-1] if len(player.split()) > 1 else player,
                    case=False, na=False,
                ))
            ]
            xg_p90 = per_90(espn_player["xG"].sum(), minutes) if len(espn_player) > 0 and espn_player["xG"].sum() > 0 else 0.0

        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d2_lead_to_shot": lts_rate, "d2_shots_p90": shots_p90,
            "d2_dangerous_runs_p90": dangerous_runs_p90,
            "d2_penetrating_runs_p90": pen_runs_p90, "d2_xg_p90": xg_p90,
        })
    return pd.DataFrame(records)


def compute_d3(qualifying, dynamic_sev):
    obr = _get_sev_events(dynamic_sev, "off_ball_run")
    passing_options = _get_sev_events(dynamic_sev, "passing_option")
    records = []

    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        runs = obr[(obr["player_name"] == player) & (obr["match_id"] == mid)]
        po = passing_options[(passing_options["player_name"] == player) & (passing_options["match_id"] == mid)]

        runs_p90 = per_90(len(runs), minutes)

        hv_runs = runs[runs["event_subtype"].isin(["overlap", "underlap", "behind", "run_ahead_of_the_ball"])]
        hv_runs_p90 = per_90(len(hv_runs), minutes)

        targeted_po = po[po["targeted"] == True]
        mean_po_score = targeted_po["passing_option_score"].mean() if len(targeted_po) > 0 else (
            po["passing_option_score"].mean() if len(po) > 0 else 0.0
        )

        received = po[po["received"] == True]
        ris_rate = (received["received_in_space"] == True).mean() if len(received) > 0 else 0.0

        break_dl = (po["break_defensive_line"] == True).sum() if "break_defensive_line" in po.columns else 0
        push_dl = (po["push_defensive_line"] == True).sum() if "push_defensive_line" in po.columns else 0
        dl_rate = (break_dl + push_dl) / len(po) if len(po) > 0 else 0.0

        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d3_runs_p90": runs_p90, "d3_hv_runs_p90": hv_runs_p90,
            "d3_po_score": mean_po_score, "d3_received_space": ris_rate,
            "d3_line_break_rate": dl_rate,
        })
    return pd.DataFrame(records)


def compute_d4(qualifying, dynamic_sev, espn_sev, espn_match_ids):
    engagements = _get_sev_events(dynamic_sev, "on_ball_engagement")
    records = []

    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        obe = engagements[(engagements["player_name"] == player) & (engagements["match_id"] == mid)]

        eng_p90 = per_90(len(obe), minutes)
        in_chain = (obe["pressing_chain"] == True).sum()
        chain_rate = in_chain / len(obe) if len(obe) > 0 else 0.0

        stop_danger = (obe["stop_possession_danger"] == True).sum()
        reduce_danger = (obe["reduce_possession_danger"] == True).sum()
        danger_rate = (stop_danger + reduce_danger) / len(obe) if len(obe) > 0 else 0.0

        force_back = (obe["force_backward"] == True).sum()
        force_back_rate = force_back / len(obe) if len(obe) > 0 else 0.0

        beaten_poss = (obe["beaten_by_possession"] == True).sum()
        beaten_move = (obe["beaten_by_movement"] == True).sum()
        solidity = 1.0 - ((beaten_poss + beaten_move) / len(obe)) if len(obe) > 0 else 0.0

        tackles_int_p90 = np.nan
        if mid in espn_match_ids:
            espn_player = espn_sev[
                (espn_sev["match_id"] == mid)
                & (espn_sev["toucher"].str.contains(
                    player.split()[-1] if len(player.split()) > 1 else player,
                    case=False, na=False,
                ))
            ]
            if len(espn_player) > 0:
                tack = len(espn_player[espn_player["playType"] == "Tackle"])
                inter = len(espn_player[espn_player["playType"] == "Interception"])
                tackles_int_p90 = per_90(tack + inter, minutes)
            else:
                tackles_int_p90 = 0.0

        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d4_engagements_p90": eng_p90, "d4_pressing_chain": chain_rate,
            "d4_danger_neutralized": danger_rate, "d4_force_backward": force_back_rate,
            "d4_solidity": solidity, "d4_tackles_int_p90": tackles_int_p90,
        })
    return pd.DataFrame(records)


def compute_d5(qualifying, physical):
    records = []
    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        phys_row = physical[(physical["dyn_name"] == player) & (physical["match_id"] == mid)]

        if len(phys_row) == 0:
            records.append({
                "player_name": player, "match_id": mid, "minutes": minutes,
                "d5_mmin": np.nan, "d5_hsr_dist_p90": np.nan,
                "d5_sprints_p90": np.nan, "d5_high_accel_p90": np.nan,
                "d5_psv99": np.nan,
            })
            continue

        pr = phys_row.iloc[0]
        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d5_mmin": pr.get("M/min", np.nan),
            "d5_hsr_dist_p90": pr.get("HSR Distance P90", np.nan),
            "d5_sprints_p90": pr.get("Sprint Count P90", np.nan),
            "d5_high_accel_p90": pr.get("High Acceleration Count P90", np.nan),
            "d5_psv99": pr.get("PSV-99", np.nan),
        })
    return pd.DataFrame(records)


def compute_d6(qualifying, dynamic_sev):
    possessions = _get_sev_events(dynamic_sev, "player_possession")
    records = []

    for _, row in qualifying.iterrows():
        player = row["player_name"]
        mid = row["match_id"]
        minutes = row["minutes_played"]

        pp = possessions[(possessions["player_name"] == player) & (possessions["match_id"] == mid)]

        if len(pp) > 0 and "end_type" in pp.columns:
            losses = (pp["end_type"] == "possession_loss").sum()
            retention = 1.0 - (losses / len(pp))
        else:
            retention = 0.0

        passes = pp[pp["pass_outcome"].notna()]
        pass_accuracy = (passes["pass_outcome"] == "successful").mean() if len(passes) > 0 else 0.0

        one_touch = (pp["one_touch"] == True).sum() if "one_touch" in pp.columns else 0
        quick_pass = (pp["quick_pass"] == True).sum() if "quick_pass" in pp.columns else 0
        quick_rate = (one_touch + quick_pass) / len(pp) if len(pp) > 0 else 0.0

        targeted_xpc = pp["player_targeted_xpass_completion"].dropna()
        pass_selection = targeted_xpc.mean() if len(targeted_xpc) > 0 else 0.0

        records.append({
            "player_name": player, "match_id": mid, "minutes": minutes,
            "d6_retention": retention, "d6_pass_accuracy": pass_accuracy,
            "d6_quick_decision": quick_rate, "d6_pass_selection": pass_selection,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Normalization & scoring
# ---------------------------------------------------------------------------

def percentile_normalize(df: pd.DataFrame, metric_cols: list, group_col: str = "match_id") -> pd.DataFrame:
    df_norm = df.copy()
    for col in metric_cols:
        df_norm[f"{col}_norm"] = df_norm.groupby(group_col)[col].rank(
            method="average", pct=True, na_option="keep"
        )
    return df_norm


def compute_dimension_score(df: pd.DataFrame, weights: dict) -> list:
    scores = []
    for _, row in df.iterrows():
        available = {k: v for k, v in weights.items() if pd.notna(row.get(k, np.nan))}
        if not available:
            scores.append(np.nan)
            continue
        total_w = sum(available.values())
        score = sum(row[k] * (v / total_w) for k, v in available.items())
        scores.append(score)
    return scores


def merge_all_scores(qualifying, dynamic_sev, physical, espn_sev, registry_scoring):
    espn_match_ids = set(mid for mid, m in MATCHES.items() if m["espn_file"] is not None)

    df_d1 = compute_d1(qualifying, dynamic_sev, espn_sev, espn_match_ids)
    df_d2 = compute_d2(qualifying, dynamic_sev, espn_sev, espn_match_ids)
    df_d3 = compute_d3(qualifying, dynamic_sev)
    df_d4 = compute_d4(qualifying, dynamic_sev, espn_sev, espn_match_ids)
    df_d5 = compute_d5(qualifying, physical)
    df_d6 = compute_d6(qualifying, dynamic_sev)

    # Normalize
    d1_metrics = ["d1_xthreat_mean", "d1_pass_success", "d1_carries_p90",
                  "d1_line_break_opts", "d1_forward_momentum", "d1_xa_p90"]
    df_d1_norm = percentile_normalize(df_d1, d1_metrics)

    d2_metrics = ["d2_lead_to_shot", "d2_shots_p90", "d2_dangerous_runs_p90",
                  "d2_penetrating_runs_p90", "d2_xg_p90"]
    df_d2_norm = percentile_normalize(df_d2, d2_metrics)

    d3_metrics = ["d3_runs_p90", "d3_hv_runs_p90", "d3_po_score",
                  "d3_received_space", "d3_line_break_rate"]
    df_d3_norm = percentile_normalize(df_d3, d3_metrics)

    d4_metrics = ["d4_engagements_p90", "d4_pressing_chain", "d4_danger_neutralized",
                  "d4_force_backward", "d4_solidity", "d4_tackles_int_p90"]
    df_d4_norm = percentile_normalize(df_d4, d4_metrics)

    d5_metrics = ["d5_mmin", "d5_hsr_dist_p90", "d5_sprints_p90",
                  "d5_high_accel_p90", "d5_psv99"]
    df_d5_norm = percentile_normalize(df_d5, d5_metrics)

    d6_metrics = ["d6_retention", "d6_pass_accuracy", "d6_quick_decision", "d6_pass_selection"]
    df_d6_norm = percentile_normalize(df_d6, d6_metrics)

    # Dimension scores
    df_d1_norm["score_d1"] = compute_dimension_score(df_d1_norm, D1_WEIGHTS)
    df_d2_norm["score_d2"] = compute_dimension_score(df_d2_norm, D2_WEIGHTS)
    df_d3_norm["score_d3"] = compute_dimension_score(df_d3_norm, D3_WEIGHTS)
    df_d4_norm["score_d4"] = compute_dimension_score(df_d4_norm, D4_WEIGHTS)
    df_d5_norm["score_d5"] = compute_dimension_score(df_d5_norm, D5_WEIGHTS)
    df_d6_norm["score_d6"] = compute_dimension_score(df_d6_norm, D6_WEIGHTS)

    # Merge
    scores_all = qualifying.copy()
    for df_dim, score_col in [
        (df_d1_norm, "score_d1"), (df_d2_norm, "score_d2"), (df_d3_norm, "score_d3"),
        (df_d4_norm, "score_d4"), (df_d5_norm, "score_d5"), (df_d6_norm, "score_d6"),
    ]:
        scores_all = scores_all.merge(
            df_dim[["player_name", "match_id", score_col]],
            on=["player_name", "match_id"],
            how="left",
        )

    # Add profile
    profile_map = registry_scoring.set_index(["player_name", "match_id"])["profile"].to_dict()
    scores_all["profile"] = scores_all.apply(
        lambda r: profile_map.get((r["player_name"], r["match_id"]), "WM"), axis=1
    )

    return scores_all


def compute_composite(scores_all: pd.DataFrame) -> pd.DataFrame:
    def _composite(row):
        profile = row["profile"]
        if profile not in PROFILE_WEIGHTS:
            return np.nan
        weights = PROFILE_WEIGHTS[profile]
        dim_scores = [row.get(f"score_d{i+1}", np.nan) for i in range(6)]
        available = [(s, w) for s, w in zip(dim_scores, weights) if pd.notna(s)]
        if not available:
            return np.nan
        total_w = sum(w for _, w in available)
        return sum(s * (w / total_w) for s, w in available)

    scores_all = scores_all.copy()
    scores_all["composite_score"] = scores_all.apply(_composite, axis=1)
    # Add jornada/label for convenience
    scores_all["jornada"] = scores_all["match_id"].map(lambda x: MATCHES[x]["jornada"])
    scores_all["match_label"] = scores_all["match_id"].map(lambda x: MATCHES[x]["label"])
    return scores_all


def aggregate_by_player(scores_all: pd.DataFrame) -> pd.DataFrame:
    records = []
    dim_cols = DIM_COLS

    for player in scores_all["player_name"].unique():
        p_data = scores_all[scores_all["player_name"] == player]
        if p_data["composite_score"].isna().all():
            continue
        valid = p_data.dropna(subset=["composite_score"])
        total_minutes = valid["minutes_played"].sum()
        if total_minutes == 0:
            continue

        agg_score = np.average(valid["composite_score"], weights=valid["minutes_played"])

        dim_agg = {}
        for d in dim_cols:
            d_valid = valid.dropna(subset=[d])
            if len(d_valid) > 0:
                dim_agg[d] = np.average(d_valid[d], weights=d_valid["minutes_played"])
            else:
                dim_agg[d] = np.nan

        scores_list = valid["composite_score"].values
        std_dev = scores_list.std() if len(scores_list) > 1 else 0.0
        cv = std_dev / agg_score if agg_score > 0 else 0.0
        best_match = valid.loc[valid["composite_score"].idxmax(), "match_id"]
        worst_match = valid.loc[valid["composite_score"].idxmin(), "match_id"]
        main_profile = valid["profile"].mode().iloc[0]
        n_matches = len(valid)

        records.append({
            "player_name": player,
            "profile": main_profile,
            "n_matches": n_matches,
            "total_minutes": round(total_minutes, 0),
            "composite_score": round(agg_score, 4),
            "std_dev": round(std_dev, 4),
            "cv": round(cv, 4),
            "best_match": MATCHES[best_match]["label"],
            "worst_match": MATCHES[worst_match]["label"],
            **{k: round(v, 4) if pd.notna(v) else np.nan for k, v in dim_agg.items()},
        })

    return pd.DataFrame(records).sort_values("composite_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_full_pipeline(data_dir: str | Path) -> dict:
    data_dir = Path(data_dir)

    dynamic_sev = load_dynamic_events(data_dir)
    physical = load_physical_data(data_dir)
    espn_sev = load_espn_events(data_dir)
    registry = build_player_registry(data_dir)
    registry_scoring = registry[~registry["profile"].isin(["GK", "SUB"])].copy()

    qualifying = _build_qualifying(registry_scoring)

    scores_all = merge_all_scores(qualifying, dynamic_sev, physical, espn_sev, registry_scoring)
    scores_all = compute_composite(scores_all)
    aggregated = aggregate_by_player(scores_all)

    return {
        "scores_all": scores_all,
        "aggregated": aggregated,
        "physical": physical,
        "dynamic_sev": dynamic_sev,
        "espn_sev": espn_sev,
        "registry": registry,
        "registry_scoring": registry_scoring,
    }
