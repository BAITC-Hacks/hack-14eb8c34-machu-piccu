"""Report held-out predictions only; distinguish model selection from final test."""
import json

import numpy as np
import pandas as pd

from .ml_data import ROOT, REPORTS, TARGET, KEYS, dump_json, md_table
from .ml_models import metric_values
from .ml_experiments import load_oof


def comparison(label, before, after):
    return {"comparison": label, "MAE_before": before, "MAE_after": after, "ratio_after_before": after / before,
            "absolute_improvement": before - after, "relative_improvement_pct": (1 - after / before) * 100}


def grouped_metrics(frame, columns):
    rows = []
    for key, part in frame.groupby(columns, observed=True, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        rows.append(dict(zip(columns, key)) | metric_values(part[TARGET], part.prediction))
    return pd.DataFrame(rows)


def write_reports(train, comp, folds, groups, config, results, selected, architecture_ref, run_dir):
    leaderboard = pd.DataFrame(results).sort_values(["MAE", "std_fold_MAE"]).reset_index(drop=True)
    leaderboard.insert(0, "rank", np.arange(1, len(leaderboard) + 1))
    leaderboard.to_csv(REPORTS / "model_leaderboard.csv", index=False)
    display = ["rank", "model", "feature_group", "architecture", "variant", "feature_count", "MAE", "RMSE", "nMAE", "Bias", "MAE_D1", "MAE_D2", "MAE_turbine_1", "MAE_turbine_2", "mean_fold_MAE", "std_fold_MAE", "training_time"]
    intro = "# Power model leaderboard\n\nAll values are outer walk-forward predictions on identical rows across October 2025–January 2026 (months selected from actual coverage). No random split or training scores. Lower MAE is better.\n\n"
    intro += "nMAE = MAE / (1 − 0) = MAE for the observed normalized [0,1] scale; nMAE_pct = 100 × MAE (percentage points of normalized full scale, not relative error divided by observed power). Bias = prediction − target. RMSE gives extra weight to large errors.\n\n"
    intro += "Rank is pooled row-weighted MAE; mean/std across months are reported separately. Final policy may select a smaller configuration within the declared near-best band. Full206 is benchmark-only unless its gain over compact features exceeds 2%.\n\n"
    (REPORTS / "model_leaderboard.md").write_text(intro + md_table(leaderboard[display]), encoding="utf-8")
    fold_metrics = []
    granular = []
    for result in results:
        oof = load_oof(run_dir, result["id"])
        fm = grouped_metrics(oof, ["fold"])
        fm.insert(0, "experiment_id", result["id"])
        fold_metrics.append(fm)
        for columns in [["horizon_bucket"], ["turbine_id"], ["turbine_id", "horizon_bucket"], ["lead_hours"]]:
            gm = grouped_metrics(oof, columns)
            gm.insert(0, "scope", "+".join(columns))
            gm.insert(0, "experiment_id", result["id"])
            granular.append(gm)
    pd.concat(fold_metrics, ignore_index=True).to_csv(REPORTS / "model_fold_metrics.csv", index=False)
    pd.concat(granular, ignore_index=True).to_csv(REPORTS / "model_segment_metrics.csv", index=False)
    curve = leaderboard[(leaderboard.model.isin(["CatBoost", "LightGBM"])) &
                        (leaderboard.feature_group.str.startswith("Top") | leaderboard.feature_group.isin(["CORE", "Full206"])) &
                        (leaderboard.variant == "default") & (leaderboard.architecture == "global")].copy()
    curve["requested_feature_count"] = curve.feature_group.map(lambda v: int(v[3:]) if v.startswith("Top") else len(groups[v]))
    curve["set_label"] = curve.feature_group.replace({"Top30": "SELECTED / Top30", "Full206": "FULL safe benchmark"})
    curve = curve.rename(columns={"MAE": "validation_MAE", "RMSE": "validation_RMSE", "MAE_D1": "D1_MAE", "MAE_D2": "D2_MAE"})
    curve[["model", "set_label", "requested_feature_count", "feature_count", "validation_MAE", "validation_RMSE", "D1_MAE", "D2_MAE"]].sort_values(["model", "feature_count"]).to_csv(REPORTS / "feature_count_experiment.csv", index=False)
    # Controlled weather ablation uses one algorithm / identical settings.
    anchor = leaderboard[(leaderboard.model == "LightGBM") & (leaderboard.architecture == "global") & (leaderboard.variant == "default")].set_index("feature_group")
    single_name = anchor.loc[["ECMWF", "GFS", "ICON"]].MAE.idxmin()
    single = float(anchor.loc[single_name, "MAE"])
    strategies = []
    for group in config["feature_groups"]:
        row = anchor.loc[group]
        strategies.append({"Weather Strategy": group, "model": "LightGBM (same settings)", "D1 MAE": row.MAE_D1,
                           "D2 MAE": row.MAE_D2, "Overall MAE": row.MAE,
                           "ratio_vs_best_single": row.MAE / single,
                           "Improvement vs best single provider (%)": (1 - row.MAE / single) * 100})
    weather_table = pd.DataFrame(strategies)
    weather_table.to_csv(REPORTS / "multi_weather_value.csv", index=False)
    comparisons = []
    for before, after in [("ECMWF", "GFS"), ("ECMWF", "ICON"), (single_name, "Simple"), (single_name, "Weighted"),
                          ("Weighted", "All"), ("All", "All_Disagreement"), ("Full_No_Performance", "Full")]:
        comparisons.append(comparison(f"LightGBM: {before} -> {after}", anchor.loc[before, "MAE"], anchor.loc[after, "MAE"]))
    for architecture in ["horizon", "turbine", "horizon_turbine"]:
        alternative = leaderboard[(leaderboard.model == architecture_ref["model"]) & (leaderboard.feature_group == architecture_ref["feature_group"]) &
                                  (leaderboard.variant == architecture_ref["variant"]) & (leaderboard.architecture == architecture)].iloc[0]
        comparisons.append(comparison(f"{architecture_ref['id']} -> {architecture}", architecture_ref["MAE"], alternative.MAE))
    ablation = pd.DataFrame(comparisons)
    ablation.to_csv(REPORTS / "ablation_study.csv", index=False)
    ablation_text = "# Ablation study\n\nPositive improvement = lower error; negative = worse. Ratios below 1 are better. Weather comparisons keep learner, hyperparameters, folds and observation rows identical.\n\n"
    ablation_text += md_table(ablation) + "\n\n## Multi-Weather Agent value\n\n" + md_table(weather_table)
    ablation_text += "\n\nFull is compact Full Agent (24 features), not Full206. Full_No_Performance removes the three explicit wind MAE 30d predictors only. The weighted wind forecast still indirectly uses past performance in BOTH configurations: this comparison measures incremental value of exposing history to ML, not removal of every historical dependency.\n\n"
    ablation_text += "Best single provider is chosen by aggregate overall MAE, not a favorable month. D1/D2 provider winners may differ. Individual-provider groups use that provider's temperature; all-provider groups use simple mean temperature. Differences reflect these documented feature strategies, not a clean causal weather-source intervention.\n"
    (REPORTS / "ablation_study.md").write_text(ablation_text, encoding="utf-8")
    chosen_parts = []
    for horizon, choice in selected.items():
        oof = load_oof(run_dir, choice["id"])
        part = oof[oof.horizon_bucket == horizon].copy()
        part["selected_experiment"] = choice["id"]
        chosen_parts.append(part)
    policy = pd.concat(chosen_parts).sort_values("row_id").reset_index(drop=True)
    expected_rows = sorted(np.concatenate([f["valid"] for f in folds]))
    if list(policy.row_id) != expected_rows:
        raise ValueError("Selected policy does not have exactly the common OOF rows")
    (ROOT / "predictions").mkdir(exist_ok=True)
    policy.to_parquet(ROOT / "predictions/validation_predictions.parquet", index=False)
    overall = metric_values(policy[TARGET], policy.prediction)
    horizon_metrics = grouped_metrics(policy, ["horizon_bucket"])
    turbine_metrics = grouped_metrics(policy, ["turbine_id", "horizon_bucket"])
    month_metrics = grouped_metrics(policy, ["fold"])
    baseline = leaderboard[leaderboard.model.isin(["HistoricalMean", "HistoricalMedian", "Persistence"])].sort_values("MAE").iloc[0]
    ratios = pd.DataFrame([comparison("Selected ML vs best simple baseline: " + baseline.model, baseline.MAE, overall["MAE"]),
                          comparison("Selected ML vs best controlled single-provider ML: " + single_name, single, overall["MAE"])])
    ratios.to_csv(REPORTS / "power_model_ratios.csv", index=False)
    # Daily paired block bootstrap is descriptive; model selection still used these months.
    base_oof = load_oof(run_dir, baseline.id).set_index("row_id").loc[policy.row_id]
    difference = np.abs(base_oof.prediction.to_numpy() - policy[TARGET].to_numpy()) - np.abs(policy.prediction.to_numpy() - policy[TARGET].to_numpy())
    dates = pd.to_datetime(policy.target_time).dt.floor("D")
    daily = pd.DataFrame({"date": dates, "delta": difference}).groupby("date").agg(total=("delta", "sum"), n=("delta", "size"))
    rng = np.random.default_rng(config["seed"])
    indices = rng.integers(0, len(daily), size=(1000, len(daily)))
    bootstrap = daily.total.to_numpy()[indices].sum(axis=1) / daily.n.to_numpy()[indices].sum(axis=1)
    interval = np.quantile(bootstrap, [.025, .975]).tolist()
    # Error analysis, using outcomes only for evaluation bins, never model input.
    analysis = policy.copy()
    metadata = train.loc[analysis.row_id]
    for col in ["target_hour", "wind_speed_100m_mean", "wind_speed_models_std"]:
        analysis[col] = metadata[col].to_numpy()
    analysis["wind_regime"] = pd.cut(analysis.wind_speed_100m_mean, [-np.inf, 3, 6, 10, 15, np.inf], labels=["<3", "3-6", "6-10", "10-15", ">=15"])
    analysis["power_regime"] = pd.cut(analysis[TARGET], [-np.inf, .05, .25, .75, .95, np.inf], labels=["<=.05", ".05-.25", ".25-.75", ".75-.95", ">.95"])
    analysis["disagreement_regime"] = pd.cut(analysis.wind_speed_models_std, [-np.inf, 1, 2, 3, np.inf], labels=["<1", "1-2", "2-3", ">=3"])
    analysis["absolute_error"] = np.abs(analysis.prediction - analysis[TARGET])
    rho = analysis[["absolute_error", "wind_speed_models_std"]].corr(method="spearman").iloc[0, 1]
    error_text = "# Error analysis: selected policy OOF\n\nThese are selection-fold forecasts, not training fit or February test. Power bins use actual target only for post-hoc evaluation.\n\n"
    error_tables = []
    for columns in [["horizon_bucket"], ["turbine_id"], ["turbine_id", "horizon_bucket"], ["target_hour"], ["fold"], ["wind_regime"], ["power_regime"], ["disagreement_regime"], ["lead_hours"]]:
        table = grouped_metrics(analysis, columns)
        error_text += "## " + " / ".join(columns) + "\n\n" + md_table(table) + "\n\n"
        table["scope"] = "+".join(columns)
        error_tables.append(table)
    error_text += f"Spearman correlation between forecast wind disagreement and absolute power error: {rho:.4f}. This is a descriptive association, not causation; wind regime, turbine and temporal autocorrelation can confound it. No assumption of positive relationship is imposed.\n"
    (REPORTS / "error_analysis.md").write_text(error_text, encoding="utf-8")
    pd.concat(error_tables, ignore_index=True).to_csv(REPORTS / "error_analysis.csv", index=False)
    selection_rows = [{"horizon": h, "configuration": choice["id"], "features": choice["feature_count"], "validation_MAE": choice[f"MAE_{h}"]} for h, choice in selected.items()]
    summary = {"overall": overall, "horizon": horizon_metrics.to_dict("records"), "selection": selection_rows,
               "best_baseline": baseline.id, "ratio_vs_baseline": overall["MAE"] / baseline.MAE,
               "relative_improvement_vs_baseline_pct": (1 - overall["MAE"] / baseline.MAE) * 100,
               "paired_daily_bootstrap_MAE_improvement_95pct_interval": interval,
               "disagreement_error_spearman": float(rho), "validation_rows": len(policy), "experiments": len(results)}
    dump_json(REPORTS / "ml_summary.json", summary)
    final_table = leaderboard.head(10)[["id", "MAE", "RMSE", "nMAE", "Bias", "MAE_D1", "MAE_D2"]].rename(columns={"id": "Configuration"})
    final_table = pd.concat([pd.DataFrame([{"Configuration": "Selected routing policy", **{k: overall[k] for k in ["MAE", "RMSE", "nMAE", "Bias"]},
                                         "MAE_D1": horizon_metrics.set_index("horizon_bucket").loc["D1", "MAE"],
                                         "MAE_D2": horizon_metrics.set_index("horizon_bucket").loc["D2", "MAE"]}]), final_table], ignore_index=True)
    report = "# Итоговый ML-отчёт: прогноз нормализованной мощности\n\n" + md_table(final_table) + "\n\n"
    report += f"## 1. Dataset\n\n{len(train):,} строк обучения; {len(comp):,} competition-строк; две турбины. Target: normalized_active_power. Источники Parquet не изменены. Offline February файл не загружался для обучения или отбора. Диапазон target подтверждён также по исходному подготовленному hourly SCADA. Подробности: ml_data_audit.md.\n\n"
    report += "## 2. Validation methodology\n\nПоследние четыре календарных месяца с достаточным покрытием выбраны автоматически. Split по target_time одновременно для всех турбин и D1/D2. Перед каждым месяцем модель обучается только на метках, доступных строго раньше самого раннего forecast_issue_time этого месяца; пограничные часы исключены. Параметры early stopping определяются во внутреннем последнем 21-дневном участке прошлого с дополнительным availability purge; затем модель переобучается на всём разрешённом outer train. Outer validation не используется для early stopping.\n\n"
    report += md_table(pd.read_csv(REPORTS / "validation_folds.csv")) + "\n\n"
    report += "## 3. Leakage prevention\n\nНикаких случайных split, future backfill, actual weather, eval_* или raw timestamps в X. Категории и статистический отбор признаков обучаются только на прошлом. Дубликаты D1/D2 не пересекают границы. Weather-performance признаки validation пересчитаны в отдельном ML view только по наблюдениям до проверочного месяца с availability < issue; исходные weather файлы и pipeline не менялись. Это имитирует отсутствие новых SCADA-ответов в феврале. История внутри train остаётся point-in-time online.\n\n"
    report += "## 4. Baselines и ratios\n\nСреднее/медиана turbine × hour рассчитаны на уникальных исторических наблюдениях, чтобы D1/D2 не удваивали один target. Persistence использует только доступное до issue наблюдение из предыдущих месяцев, поэтому стареет внутри месяца: это честная offline-версия, не online persistence с доступом к проверочным ответам.\n\n"
    report += md_table(leaderboard[leaderboard.model.isin(["HistoricalMean", "HistoricalMedian", "Persistence"])][["model", "MAE", "RMSE", "MAE_D1", "MAE_D2"]]) + "\n\n" + md_table(ratios) + "\n\n"
    report += f"Описательный 95% интервал выигрыша MAE против baseline при paired bootstrap по UTC-дням: [{interval[0]:.5f}, {interval[1]:.5f}]. Он не корректирует перебор моделей и не заменяет независимый test.\n\n"
    report += "## 5. Weather provider comparison\n\nОдинаковый LightGBM, одинаковые параметры и folds; Full = 24 компактных признака агента.\n\n" + md_table(weather_table) + "\n\n"
    report += f"## 6. Model tournament\n\nВыполнено {len(results)} конфигураций × {len(folds)} одинаковых outer folds. CatBoost, LightGBM, XGBoost × 8 погодных групп, CORE, компактные наборы, Full206 benchmark, tuning и архитектуры. Все параметры, stopping iterations и OOF сохранены в experiments/{run_dir.name}; сводка model_leaderboard.csv/.md, детализация model_fold_metrics.csv и model_segment_metrics.csv. Полный 206-признаковый набор не является моделью по умолчанию.\n\n"
    report += "## 7. D1 vs D2\n\nВыбор по совокупности четырёх месяцев, отдельно по горизонтам, с предпочтением общей модели при выигрыше менее 0.5%.\n\n" + md_table(pd.DataFrame(selection_rows)) + "\n\n"
    report += "## 8. Turbine strategy\n\nДля одного и того же лучшего global learner/group/parameters проверены global, separate horizons, separate turbines, separate horizons × turbines. При близком MAE выбирается более простая архитектура.\n\n" + md_table(turbine_metrics) + "\n\n"
    report += "## 9. Ablation study и компактность\n\nЧисленные сравнения: ablation_study.md/.csv. Кривая размера: feature_count_experiment.csv (Top10/15/20/30/50 и Full). Ранжирование и корреляции получены только на первом outer train, затем заморожены. Финальный набор: models/final_features.json; описание final_feature_selection.md.\n\n" + md_table(ablation) + "\n\n"
    report += "## 10. Hyperparameter tuning\n\nТолько top-3 компактных конфигурации после турнира: по два контролируемых варианта (regularized/richer), максимум 800 деревьев. Inner chronological early stopping, MAE loss и MAE evaluation; случайного CV нет. Все fitted параметры сохранены по fold.\n\n"
    report += "## 11. Winning model\n\n" + md_table(pd.DataFrame(selection_rows)) + "\n\nФинальные refit используют все допустимые исторические метки. Для ранних forecast_issue_time соревнования создаются дополнительные as-of checkpoints: нельзя применить модель, обученную на конце января, к прогнозу, выпущенному до этих наблюдений. Registry выбирает checkpoint с train_max_available < issue. Число деревьев — медиана inner-stopping результатов четырёх folds, а не подбор на феврале.\n\n"
    report += "## 12. Feature importance\n\nfeature_importance.csv/.png: нормализованная native importance финальных моделей. shap_importance.csv: native Tree SHAP на 128 исторических строках на модель, только описательно; эти значения не использовались для отбора на outer validation. Коррелирующие признаки могут делить importance.\n\n"
    report += f"## 13. Error analysis\n\nerror_analysis.md/.csv: horizon, turbine, час, месяц, lead, режим ветра, мощности, disagreement. Spearman(disagreement, |power error|) = {rho:.4f}. Связь не является доказательством причинности.\n\n" + md_table(month_metrics) + "\n\n"
    report += "## 14. Competition forecast\n\npredictions/final_forecast.parquet и .csv: 2 688 строк, ключи входа, prediction, selected model/group и checkpoint. predict.py проверяет порядок/наличие признаков, кодирование категорий, finite и [0,1], количество/уникальность ключей, доступность меток модели на issue и hashes. model_registry.json задаёт маршрутизацию D1/D2 и при необходимости турбин. Февральских targets нет — февральские метрики не заявляются.\n\n"
    report += "## 15. Limitations\n\n"
    report += "- Все четыре месяца использованы для выбора моделей/признаков. Это out-of-fold validation, но не независимый финальный test; selection optimism возможен.\n- Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value. Принята согласованная fixed lead-time методология, не точное воспроизведение snapshot одного NWP-run.\n- UTC+5 — ранее inferred metadata; inference использовал период 2024–2025, включающий часть проверочных месяцев. В этом этапе timezone принят как зафиксированный input contract, не переоценивался. Поэтому end-to-end validation не является полностью независимой проверкой inference timezone. Для строго независимой оценки нужно внешнее подтверждение timezone или fold-local inference.\n- SCADA availability = конец часа + 60 минут — допущение исходного pipeline. Отсутствуют высота датчика, флаги ограничения генерации/аварий и подтверждённая паспортная мощность.\n- nMAE нормируется на диапазон [0,1], не на среднее фактической мощности. MAE ×100 — процентные пункты нормализованной шкалы; трактовка как доля nameplate capacity требует подтверждения оператора.\n- Ранние периоды без полноценной погоды исключены исходным pipeline. Missing SCADA-часы не заполняются.\n- Отбор/тюнинг ограничен CPU-бюджетом и указанным набором вариантов; глобальная оптимальность не заявляется.\n- Model ensemble не добавлен по умолчанию: основной результат — компактные интерпретируемые individual models.\n\n"
    report += "## Reproduction\n\n`python train.py` — аудит, resume-enabled tournament, final refits, inference. `python predict.py` — только загрузка финальных моделей и прогноз. Seed/threads: ml_config.json; точные версии: requirements-ml.txt и models/environment.json. Run fingerprint включает исходные Parquet, ML-код и версии; старые experiment results сохраняются отдельно.\n\n"
    report += "Официальные API обучения: [CatBoost fit](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor_fit), [LightGBM](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMRegressor.html), [XGBoost](https://xgboost.readthedocs.io/en/stable/python/python_api.html).\n"
    (REPORTS / "final_ml_report.md").write_text(report, encoding="utf-8")


def final_feature_report(groups, final_map, importance, selected, run_dir):
    union = sorted(set(sum(final_map.values(), [])))
    values = importance.set_index("feature").importance.to_dict()
    reasons = {}
    ranking = json.loads((run_dir / "feature_ranking.json").read_text(encoding="utf-8"))
    for decision in ranking["decisions"]:
        reasons[decision["feature"]] = decision["reason"] if not decision["selected_candidate"] else "Not required by the chosen compact validation configuration"
    rows = []
    for feature in union:
        if feature == "turbine_id":
            source, meaning = "SCADA identifier", "Categorical turbine identity; captures turbine differences"
        elif feature == "lead_hours":
            source, meaning = "Forecast schedule", "Lead from issue to target, hours"
        elif feature.startswith(("hour_", "day_of_year_")):
            source, meaning = "Target local calendar", "Cyclic hour or annual phase"
        elif "mae_30d" in feature:
            source, meaning = "Past available SCADA + archived forecasts", "Provider wind MAE in past 30-day availability window"
        elif feature.startswith("ensemble_"):
            source, meaning = "Historical-performance weighted weather", "Weighted forecast; direction expressed by sine/cosine"
        elif "models_std" in feature or "dispersion" in feature:
            source, meaning = "Archived providers", "Cross-provider disagreement"
        else:
            source = next((p.upper() for p in ["ecmwf", "gfs", "icon"] if feature.startswith(p + "_")), "Archived weather aggregate")
            if "wind_speed_100m" in feature:
                meaning = "100m forecast wind speed (m/s): proxy for inflow near turbine operating height"
            elif "wind_speed_10m" in feature:
                meaning = "10m forecast wind speed (m/s): near-surface regime, complementary to 100m flow"
            elif "wind_direction" in feature:
                meaning = "Sine/cosine component of forecast direction: directional terrain and wake regimes, no raw angle discontinuity"
            elif "gust" in feature:
                meaning = "Forecast gust speed (m/s): turbulent / gusty wind regime proxy"
            elif "pressure" in feature:
                meaning = "Forecast surface pressure (hPa): air-density / synoptic regime proxy"
            elif "humidity" in feature:
                meaning = "Forecast relative humidity (%): air-mass / moisture regime proxy, not proof of icing"
            elif "temperature" in feature:
                meaning = "Forecast temperature (C): air-density / seasonal operating regime proxy"
            else:
                meaning = "Forecast availability or quality indicator"
        rows.append({"feature": feature, "source": source, "meaning": meaning,
                     "reason_for_inclusion": "Part of near-best compact walk-forward configuration; physically interpretable", "importance": values.get(feature, 0)})
    used = pd.DataFrame(rows).sort_values("importance", ascending=False)
    removed = pd.DataFrame([{"removed_feature": c, "reason_for_removal": reasons.get(c, "Not in the winning compact configuration")} for c in groups["Full206"] if c not in union])
    used.to_csv(REPORTS / "final_selected_features.csv", index=False)
    removed.to_csv(REPORTS / "final_removed_features.csv", index=False)
    text = "# Final feature selection\n\n"
    text += f"Final union: {len(union)} features; per-route counts: { {key: len(value) for key, value in final_map.items()} }. models/final_features.json contains only actual predictors.\n\n"
    text += "Native final importance is descriptive, not the data used to select features. Selection ranking was fitted on first-fold historical train only; subset choice used aggregate walk-forward validation. Full206 remained a benchmark.\n\n"
    text += "## CORE vs SELECTED vs FULL\n\n" + md_table(pd.read_csv(REPORTS / "feature_count_experiment.csv")) + "\n\n"
    text += "## Selected features\n\n" + md_table(used) + "\n\n## Removed safe candidates\n\n" + md_table(removed)
    text += "\n\nUnsafe/technical columns excluded before selection are listed separately in feature_safety_report.md and ml_excluded_features.csv. Small measured gains do not establish statistical significance.\n"
    (REPORTS / "final_feature_selection.md").write_text(text, encoding="utf-8")
    safety = REPORTS / "feature_safety_report.md"
    existing = safety.read_text(encoding="utf-8").split("\n\n## USED FEATURES — FINAL MODEL")[0]
    safety.write_text(existing + "\n\n## USED FEATURES — FINAL MODEL\n\n" + md_table(used) +
                      "\n\nThe other safe candidates were benchmark/selection inputs only; final_removed_features.csv records why each was omitted.\n", encoding="utf-8")
