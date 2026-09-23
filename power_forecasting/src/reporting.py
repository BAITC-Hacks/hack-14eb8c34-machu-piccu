"""Deterministic coverage, error, feature-missingness, and dataset reports."""
import hashlib
import json
import numpy as np
import pandas as pd
from .input_data import ROOT
from .validation import LIMITATION


def write_reports(frame, weather, train, competition, offline, features, config, decision, validation):
    directory = ROOT / "reports"
    coverage = []
    for (turbine, day), group in weather.groupby(["turbine_id", "archive_day"]):
        for model in config["weather_models"]:
            for variable in config["weather_variables"]:
                col = f"{model}_{variable}"
                valid = group[col].notna()
                stamps = group.loc[valid, "target_time"]
                coverage.append({"model": model, "model_id": config["model_ids"][model], "turbine_id": turbine,
                    "archive_day": day, "nominal_lead_hours": day * 24, "variable": variable,
                    "earliest_available_date": stamps.min() if len(stamps) else pd.NaT,
                    "latest_available_date": stamps.max() if len(stamps) else pd.NaT,
                    "non_null_values": int(valid.sum()), "requested_values": len(group), "coverage_pct": 100 * valid.mean(),
                    "coverage_scope": "within_requested_download_interval_not_global_archive_bounds"})
    pd.DataFrame(coverage).to_csv(directory / "weather_coverage_report.csv", index=False)
    pd.DataFrame({"feature": features, "all_missing_pct": frame[features].isna().mean().to_numpy() * 100,
        "training_missing_pct": train[features].isna().mean().to_numpy() * 100,
        "competition_missing_pct": competition[features].isna().mean().to_numpy() * 100}).to_csv(directory / "feature_missingness.csv", index=False)
    metrics = []
    data = frame[(frame.dataset_split == "train") & frame.eval_actual_wind_speed.notna()]
    common = data[[f"{m}_wind_speed_100m_valid" for m in config["weather_models"]]].all(axis=1)
    for scope, sample in [("available_rows", data), ("common_rows", data.loc[common])]:
        groupings = [("all", sample)] + list(sample.groupby("turbine_id"))
        for turbine, subset in groupings:
            for horizon, group in subset.groupby("horizon_bucket"):
                sources = [(m.upper(), f"{m}_wind_speed_100m", f"{m}_temperature_2m") for m in config["weather_models"]]
                sources += [("Simple Ensemble", "wind_speed_100m_mean", "temperature_2m_mean"), ("Weighted Ensemble", "ensemble_wind_speed_100m", "ensemble_temperature_2m")]
                for label, wind, temp in sources:
                    wind_values = group[wind]
                    temp_values = group[temp]
                    if label.lower() in config["weather_models"]:
                        wind_values = wind_values.where(group[f"{wind}_valid"])
                        temp_values = temp_values.where(group[f"{temp}_valid"])
                    error = wind_values - group.eval_actual_wind_speed
                    temp_error = temp_values - group.eval_actual_temperature
                    metrics.append({"scope": scope, "turbine_id": turbine, "horizon_bucket": horizon, "model": label,
                        "n": int(error.notna().sum()), "coverage_pct": error.notna().mean() * 100,
                        "wind_mae": error.abs().mean(), "wind_rmse": np.sqrt((error ** 2).mean()), "wind_bias": error.mean(),
                        "temperature_mae": temp_error.abs().mean(), "temperature_bias": temp_error.mean()})
    metrics = pd.DataFrame(metrics)
    metrics.to_csv(directory / "weather_provider_metrics.csv", index=False)
    frame[[f"{m}_weight" for m in config["weather_models"]]].describe().to_csv(directory / "ensemble_weight_distribution.csv")
    counts = frame.groupby(["dataset_split", "turbine_id", "horizon_bucket", "lead_hours"]).size().rename("rows").reset_index()
    counts.to_csv(directory / "dataset_row_counts.csv", index=False)
    summary = {"status": "DATASETS_GENERATED_AND_VALIDATED", "master_rows": len(frame), "training_rows": len(train),
        "competition_rows": len(competition), "offline_test_rows": len(offline), "feature_columns": len(features),
        "train_target_min_utc": str(train.target_time.min()), "train_target_max_utc": str(train.target_time.max()),
        "competition_target_min_local": str(competition.target_local_time.min()), "competition_target_max_local": str(competition.target_local_time.max()),
        "unique_target_timestamps": frame.target_time.nunique(), "turbines": frame.turbine_id.nunique(),
        "D1_rows": int((frame.horizon_bucket == "D1").sum()), "D2_rows": int((frame.horizon_bucket == "D2").sum()),
        "train_schedule_rows": int((frame.dataset_split == "train").sum()),
        "train_excluded_rows": int(((frame.dataset_split == "train") & ~frame.training_eligible).sum()),
        "timezone": decision, "validation": validation,
        "provider_usable_pct_master": {m: float(frame[f"{m}_quality_ok"].mean() * 100) for m in config["weather_models"]},
        "provider_usable_pct_training": {m: float(train[f"{m}_quality_ok"].mean() * 100) for m in config["weather_models"]},
        "provider_usable_pct_competition": {m: float(competition[f"{m}_quality_ok"].mean() * 100) for m in config["weather_models"]},
        "offline_targets_present": int(offline.normalized_active_power.notna().sum()),
        "limitation": LIMITATION}
    (directory / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Итоговый датасет погоды для HackAlem", "", "Parquet-файлы сформированы. Модель мощности не обучалась.", "",
        f"Всего строк в полном аудиторском dataset: {len(frame):,}. В training_dataset: {len(train):,}. Competition: {len(competition):,}. Offline test: {len(offline):,}.",
        f"Признаков в allowlist: {len(features)}. Турбин: {summary['turbines']}. Уникальных target timestamps: {summary['unique_target_timestamps']}.",
        f"Полный период target local time: {frame.target_local_time.min()} – {frame.target_local_time.max()}.",
        f"Training target UTC: {train.target_time.min()} – {train.target_time.max()}. Competition local: {competition.target_local_time.min()} – {competition.target_local_time.max()}.",
        f"D1: {summary['D1_rows']:,}; D2: {summary['D2_rows']:,}. По lead_hours, турбине и split: dataset_row_counts.csv.",
        f"Исключено из обучающего export: {summary['train_excluded_rows']:,} строк без полноценной SCADA-метки или без хотя бы одного провайдера с тремя основными погодными переменными. Все строки сохранены в master; ключи и причины — training_exclusions.csv.", "",
        f"UTC offset {decision['selected_offset_hours']:+g}; timezone_status={decision['timezone_status']}. Проверка: timezone_inference.csv, timezone_decision.md.",
        f"Offline test с известным target: {summary['offline_targets_present']} строк. Февральские метки не выдуманы.", "",
        "## Покрытие провайдеров", "", "Quality usable = валидные wind100m, direction100m, temperature, без API error или пропущенного target hour.", "",
        "| Модель | Master, % | Training, % | Competition, % |", "|---|---:|---:|---:|"]
    for m in config["weather_models"]:
        lines.append(f"| {m.upper()} | {summary['provider_usable_pct_master'][m]:.2f} | {summary['provider_usable_pct_training'][m]:.2f} | {summary['provider_usable_pct_competition'][m]:.2f} |")
    lines += ["", "Coverage каждой переменной и номинального lead: weather_coverage_report.csv. Первые и последние даты относятся только к запрошенному интервалу, не ко всему архиву провайдера.",
        "Missing каждого признака: feature_missingness.csv. Веса: ensemble_weight_distribution.csv. Журнал всех запросов и хеши ответов: weather_request_manifest.csv.", "",
        "## Сравнение погоды на общих часах", "", "Ретроспективная оценка по train SCADA, одинаковые часы для всех моделей. Не является независимым holdout-тестом модели мощности. Bias = forecast − observation, ветер в м/с. Высота SCADA-датчика неизвестна.", "",
        "| Weather model | Wind MAE D1 | Wind MAE D2 | Coverage D1/D2, % | Bias D1/D2 |", "|---|---:|---:|---|---|"]
    table = metrics[(metrics.scope == "common_rows") & (metrics.turbine_id == "all")]
    for model in table.model.unique():
        by_day = table[table.model == model].set_index("horizon_bucket")
        a, b = by_day.loc["D1"], by_day.loc["D2"]
        lines.append(f"| {model} | {a.wind_mae:.4f} | {b.wind_mae:.4f} | {a.coverage_pct:.1f}/{b.coverage_pct:.1f} | {a.wind_bias:.4f}/{b.wind_bias:.4f} |")
    lines += ["", "Показатели по каждой турбине, температуру, RMSE и оценку на всех доступных строках см. weather_provider_metrics.csv.", "",
        "## Проверка утечек и ограничения", "", f"Проверено {validation['rows_checked']:,} строк: {validation['status']}.",
        "Rolling окна используют только outcome с observation_available_time строго меньше issue_time. Февральские наблюдения исключены из расчёта весов независимо от наличия offline targets.",
        "Обучающий export и competition export не содержат eval_actual_* и производных от будущей SCADA. Используйте feature_columns.json как явный список X.",
        LIMITATION, "",
        "Это согласованное методологическое ограничение, не blocker. D1/D2 — фиксированные offsets 24/48 ч, а lead_hours — отдельный горизонт строки внутри суточного расписания. Точное время публикации или source run не заявляется.",
        "Тесты и их актуальный результат: tests_report.json (после python -m src.run_tests).", ""]
    (directory / "dataset_report.md").write_text("\n".join(lines), encoding="utf-8")
    (directory / "point_in_time_validation.md").write_text("# Проверка point in time\n\n" + json.dumps(validation, ensure_ascii=False, indent=2) + "\n\nПроверены порядок issue/target, lead, D1/D2, nominal reference, ключи, граница split, последний доступный outcome для каждой rolling-метрики и feature allowlist.\n\nТесты мутаций будущих данных и edge cases: tests_report.json.\n", encoding="utf-8")
    outputs = []
    for path in sorted((ROOT / "data/final").glob("*.parquet")):
        outputs.append({"file": path.name, "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (directory / "output_manifest.json").write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    return summary
