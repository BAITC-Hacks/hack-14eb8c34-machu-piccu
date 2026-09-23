"""Infer a fixed UTC offset using train-only wind observations and archived D1 forecasts."""
import json
import numpy as np
import pandas as pd
from .input_data import ROOT


def infer_timezone(local, weather, config):
    start = pd.Timestamp(config["timezone_inference_start"])
    end = min(pd.Timestamp(config["timezone_inference_end"]) + pd.Timedelta(days=1), pd.Timestamp(config["competition_start"]))
    local = local[(local.target_local_time >= start) & (local.target_local_time < end)]
    rows = []
    for turbine, group in local.groupby("turbine_id"):
        obs = group.set_index("target_local_time").eval_actual_wind_speed
        archive = weather[(weather.turbine_id == turbine) & (weather.archive_day == 1)].set_index("target_time")
        for model in config["weather_models"]:
            reference = archive[f"{model}_wind_speed_100m"]
            aligned = {}
            for offset in range(-6, 7):
                utc = (obs.index - pd.Timedelta(hours=offset)).tz_localize("UTC")
                aligned[offset] = reference.reindex(utc).to_numpy()
            values = np.column_stack(list(aligned.values()))
            # All offsets use exactly the same local observation rows.
            common = np.isfinite(values).all(axis=1) & np.isfinite(obs.to_numpy())
            common &= ((values >= 0) & (values <= 75)).all(axis=1)
            common &= (obs.to_numpy() >= 0) & (obs.to_numpy() <= 75)
            for period, period_mask in [("all", np.ones(len(obs), dtype=bool))] + [(str(year), obs.index.year == year) for year in sorted(set(obs.index.year))]:
                mask = common & period_mask
                actual = obs.to_numpy()[mask]
                for offset, predicted in aligned.items():
                    predicted = predicted[mask]
                    error = predicted - actual
                    n = len(actual)
                    corr = np.corrcoef(actual, predicted)[0, 1] if n >= 2 and np.std(predicted) and np.std(actual) else np.nan
                    rows.append({"turbine_id": turbine, "model": model, "period": period, "offset_hours": offset,
                        "samples": n, "correlation": corr, "MAE": np.mean(np.abs(error)) if n else np.nan,
                        "RMSE": np.sqrt(np.mean(error ** 2)) if n else np.nan})
    result = pd.DataFrame(rows)
    result.to_csv(ROOT / "reports/timezone_inference.csv", index=False)
    valid = result[(result.period == "all") & (result.samples >= config["timezone_inference_min_samples"])].dropna(subset=["correlation", "MAE", "RMSE"])
    aggregate = []
    for offset, group in valid.groupby("offset_hours"):
        aggregate.append({"offset_hours": int(offset), **{key: float(np.average(group[key], weights=group.samples)) for key in ["correlation", "MAE", "RMSE"]}, "samples": int(group.samples.sum())})
    ranking = pd.DataFrame(aggregate)
    if len(ranking):
        ranking = ranking.sort_values("correlation", ascending=False)
    ranking.to_csv(ROOT / "reports/timezone_ranking.csv", index=False)
    # UTC is the explicit neutral fallback in config; never infer Kazakhstan timezone from geography.
    fallback = pd.Timestamp("2025-01-01", tz=config["timezone"]).utcoffset().total_seconds() / 3600
    selected, status, gap, improvement = fallback, "assumed", None, None
    if len(ranking) >= 2:
        best, runner = ranking.iloc[0], ranking.iloc[1]
        gap = float(best.correlation - runner.correlation)
        improvement = float((runner.RMSE - best.RMSE) / max(runner.RMSE, 1e-8))
        if gap >= config["timezone_inference_min_correlation_gap"] and improvement >= config["timezone_inference_min_rmse_improvement"] and best.MAE <= runner.MAE:
            selected, status = int(best.offset_hours), "inferred"
    decision = {"selected_offset_hours": selected, "timezone_status": status,
        "fallback_timezone": config["timezone"], "reference": "D1 archived wind_speed_100m, ECMWF/GFS/ICON",
        "inference_start": str(start), "inference_end_exclusive": str(end), "correlation_gap": gap,
        "relative_rmse_improvement": improvement,
        "best_candidate_offset": int(ranking.iloc[0].offset_hours) if len(ranking) else None,
        "limitation": "Statistical alignment only: forecast phase errors and sensor height may confound offsets. One fixed offset is used. No competition observations used."}
    (ROOT / "reports/timezone_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    lines = ["# Выбор временного сдвига SCADA", "", f"Выбран фиксированный UTC{selected:+g}; timezone_status={status}.",
        f"Лучший кандидат по корреляции: {decision['best_candidate_offset']}. Разрыв корреляции: {gap}; улучшение RMSE: {improvement}.", "",
        f"Калибровка: {start} <= SCADA local time < {end}. Февраль 2026 не использован.",
        "Проверены UTC−6 … UTC+6. Каждый offset сравнивается на одном и том же наборе часов для данной пары турбина/модель.",
        "Эталон — архивный D1 wind_speed_100m. Это прогноз с ошибкой, а не истинное время наблюдения. Высота SCADA-датчика неизвестна.",
        f"Правило inferred: минимум {config['timezone_inference_min_samples']} пар; отрыв корреляции >= {config['timezone_inference_min_correlation_gap']}, относительное улучшение RMSE >= {config['timezone_inference_min_rmse_improvement']}, MAE не хуже второго кандидата.",
        f"При неоднозначности используется config timezone={config['timezone']} и статус assumed. Географический пояс не подставляется.",
        "Статус verified не используется: внешнего подтверждения часов SCADA нет. По годам сохранены отдельные оценки; сезонная смена часов не моделируется.",
        "Выбор timezone — train-only оценка метаданных, а не online-признак. Поэтому ретроспектива не доказывает, что этот сдвиг был известен при самом раннем запуске.", "",
        "| UTC offset | correlation | MAE | RMSE |", "|---:|---:|---:|---:|"]
    for row in ranking.to_dict("records"):
        lines.append(f"| {row['offset_hours']:+g} | {row['correlation']:.6f} | {row['MAE']:.4f} | {row['RMSE']:.4f} |")
    (ROOT / "reports/timezone_decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return decision
