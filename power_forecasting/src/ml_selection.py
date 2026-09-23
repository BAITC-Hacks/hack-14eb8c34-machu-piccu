"""Feature ranking uses only the first outer training interval, never outer outcomes."""
import re

import numpy as np
import pandas as pd

from .ml_data import ROOT, REPORTS, dump_json, md_table
from .ml_models import fit_learner, encode_transform


def native_importance(bundle):
    model = bundle["model"]
    name = bundle["model_name"]
    if name == "CatBoost":
        values = model.get_feature_importance()
    elif name == "LightGBM":
        values = model.booster_.feature_importance(importance_type="gain")
    else:
        values = model.feature_importances_
    output = {}
    for col, value in zip(bundle["schema"]["encoded_features"], values):
        raw = col.split("__cat_")[0]
        output[raw] = output.get(raw, 0) + float(value)
    total = sum(output.values())
    return {key: val / total if total else 0.0 for key, val in output.items()}


def select_candidates(train, groups, config, output_dir):
    path = output_dir / "feature_ranking.json"
    if path.exists():
        import json
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        print("Ranking safe feature candidates on first-fold historical training only", flush=True)
        bundle = fit_learner(train, groups["Full206"], "LightGBM", config)
        importance = native_importance(bundle)
        numeric = train[groups["Full206"]].select_dtypes(include=["number", "bool"]).astype(float)
        corr = numeric.corr().abs()
        protected = ["turbine_id", "lead_hours"]
        order = protected + sorted([c for c in groups["Full206"] if c not in protected], key=lambda c: (-importance.get(c, 0), c))
        kept, decisions = [], []
        for col in order:
            values = train[col]
            reason = None
            dominant = values.value_counts(dropna=False, normalize=True).max()
            if col not in protected:
                if values.isna().mean() > config["selection_max_missing_fraction"]:
                    reason = "Excessive missingness on first training interval"
                elif dominant >= config["selection_near_constant_fraction"]:
                    reason = "Constant / near-constant on first training interval"
                elif col in ["horizon_bucket", "archive_nominal_lead_hours", "target_hour", "target_day_of_week", "target_month", "target_day_of_year"]:
                    reason = "Redundant horizon or raw calendar; use lead and cyclic time"
                elif re.search(r"wind_direction_(10m|100m)$", col) or re.search(r"wind_direction_(10m|100m)_mean$", col):
                    reason = "Raw angle replaced by sine/cosine"
                elif re.search(r"_(wind|temperature)_(mae|rmse|bias|n)_\d+d$", col) and not col.endswith("wind_mae_30d"):
                    reason = "Redundant rolling metric; retain only provider wind MAE 30d"
                elif col in corr:
                    duplicates = [c for c in kept if c in corr and corr.at[col, c] > config["selection_correlation_threshold"]]
                    if duplicates:
                        reason = "Strongly correlated training-only proxy for " + duplicates[0]
            if reason is None:
                kept.append(col)
            decisions.append({"feature": col, "importance_training_only": importance.get(col, 0),
                              "selected_candidate": reason is None, "reason": reason or "Ranked safe candidate"})
        payload = {"training_max_target": str(train.target_time.max()), "ranking_model": "LightGBM",
                   "ranked_candidates": kept, "decisions": decisions, "pilot_iterations": bundle["iterations"]}
        dump_json(path, payload)
    for count in config["feature_count_grid"]:
        groups[f"Top{count}"] = payload["ranked_candidates"][:count]
    groups["SELECTED"] = payload["ranked_candidates"][:30]
    pd.DataFrame(payload["decisions"]).to_csv(REPORTS / "feature_selection_training_only.csv", index=False)
    dump_json(ROOT / "models/feature_groups.json", groups)
    (REPORTS / "feature_selection_methodology.md").write_text(
        "# Feature selection methodology\n\n"
        f"Ranking fitted only on first-fold training: latest target {payload['training_max_target']}. No outer validation or competition targets used.\n\n"
        "CORE is physically motivated, fixed in advance (21 features). Compact Full adds provider quality flags (24). Full206 is a reference benchmark, never the default final set.\n\n"
        "Training-only native LightGBM importance ranks candidates. Missingness >60%, dominant value >=99.5%, redundant raw angles/calendars, rolling windows/metrics other than wind MAE 30d are removed. Absolute training-only pairwise correlation >0.98 removes lower-ranked proxies. Turbine and lead are protected for routing/identity. Selection is frozen before scoring any outer month.\n\n"
        "Top-N means up to N eligible predictors; requested and actual counts are both reported. Top50 may contain fewer than 50 if the safety/redundancy filters leave fewer candidates. No unsafe or redundant columns are added merely to reach a count. The same ranked list is used in every fold.\n\n"
        "The 0.5% relative-MAE near-best band favors fewer features and simpler architecture. More than 35 features require at least 2% relative reduction versus the best compact candidate. These are practical thresholds, not statistical significance claims.\n\n"
        + md_table(pd.DataFrame(payload["decisions"])), encoding="utf-8")
    return groups
