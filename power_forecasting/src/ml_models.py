"""Train-only encoding and inner-chronological early stopping for three learners."""
import time

import numpy as np
import pandas as pd

from .ml_data import TARGET


def metric_values(y, pred):
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    if not len(y) or not np.isfinite(y).all() or not np.isfinite(pred).all():
        raise ValueError("Metrics require finite paired predictions")
    error = pred - y
    mae = float(np.mean(np.abs(error)))
    mse = float(np.mean(error ** 2))
    variance = float(np.mean((y - y.mean()) ** 2))
    return {"n": len(y), "MAE": mae, "RMSE": float(np.sqrt(mse)), "nMAE": mae,
            "nMAE_pct": mae * 100, "Bias": float(error.mean()), "R2": 1 - mse / variance if variance > 0 else None}


def encode_fit(frame, features, model_name, category_columns):
    schema = {"features": list(features), "categories": {}, "native_categories": model_name == "CatBoost"}
    for col in features:
        if col in category_columns:
            schema["categories"][col] = sorted(frame[col].fillna("__MISSING__").astype(str).unique().tolist())
    data, unseen = encode_transform(frame, schema)
    schema["encoded_features"] = list(data.columns)
    return data, schema


def encode_transform(frame, schema):
    missing = set(schema["features"]) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required features: {sorted(missing)}")
    data, unseen = {}, {}
    for col in schema["features"]:
        if col in schema["categories"]:
            values = frame[col].fillna("__MISSING__").astype(str)
            vocab = schema["categories"][col]
            unseen[col] = int((~values.isin(vocab)).sum())
            if schema["native_categories"]:
                data[col] = values.to_numpy()
            else:
                for i, level in enumerate(vocab):
                    data[f"{col}__cat_{i}"] = (values == level).to_numpy(dtype=np.float32)
        else:
            series = pd.to_numeric(frame[col], errors="raise")
            values = series.to_numpy(dtype=np.float32, na_value=np.nan).copy()
            # Retain validity/availability as separate predictors, not invalid measurements.
            if col + "_valid" in frame:
                values[~frame[col + "_valid"].fillna(False).to_numpy(bool)] = np.nan
            values[~np.isfinite(values)] = np.nan
            data[col] = values
    result = pd.DataFrame(data, index=frame.index)
    if "encoded_features" in schema and list(result.columns) != schema["encoded_features"]:
        raise ValueError("Encoded feature order mismatch")
    return result, unseen


def model_parameters(name, config, variant="default", iterations=None):
    count = iterations or (config["max_iterations"] if variant == "default" else config["tuning_iterations"])
    if name == "CatBoost":
        params = dict(iterations=count, depth=6, learning_rate=.05, l2_leaf_reg=5,
                      loss_function="MAE", eval_metric="MAE", random_seed=config["seed"],
                      thread_count=config["threads"], verbose=False, allow_writing_files=False)
        if variant == "regularized":
            params.update(depth=5, learning_rate=.035, l2_leaf_reg=12)
        elif variant == "richer":
            params.update(depth=7, learning_rate=.04, l2_leaf_reg=8)
    elif name == "LightGBM":
        params = dict(n_estimators=count, num_leaves=31, max_depth=-1, learning_rate=.05,
                      min_child_samples=80, colsample_bytree=.9, subsample=.9, subsample_freq=1,
                      objective="regression_l1", reg_lambda=5, random_state=config["seed"],
                      n_jobs=config["threads"], deterministic=True, force_col_wise=True, verbosity=-1)
        if variant == "regularized":
            params.update(num_leaves=15, min_child_samples=120, learning_rate=.035, reg_lambda=12)
        elif variant == "richer":
            params.update(num_leaves=47, min_child_samples=60, learning_rate=.035, reg_lambda=8)
    elif name == "XGBoost":
        params = dict(n_estimators=count, max_depth=5, learning_rate=.05, min_child_weight=20,
                      subsample=.9, colsample_bytree=.9, reg_lambda=5, objective="reg:absoluteerror",
                      tree_method="hist", eval_metric="mae", random_state=config["seed"], n_jobs=config["threads"])
        if variant == "regularized":
            params.update(max_depth=4, min_child_weight=40, learning_rate=.035, reg_lambda=12)
        elif variant == "richer":
            params.update(max_depth=6, min_child_weight=15, learning_rate=.035, reg_lambda=8)
    else:
        raise ValueError(name)
    return params


def new_model(name, params):
    if name == "CatBoost":
        from catboost import CatBoostRegressor
        return CatBoostRegressor(**params)
    if name == "LightGBM":
        from lightgbm import LGBMRegressor
        return LGBMRegressor(**params)
    if name == "XGBoost":
        from xgboost import XGBRegressor
        return XGBRegressor(**params)
    raise ValueError(name)


def inner_split(train, config):
    start = train.target_time.max().normalize() - pd.Timedelta(days=config["inner_validation_days"] - 1)
    tail = train[train.target_time >= start]
    first_issue = tail.forecast_issue_time.min()
    core = train[(train.target_time < start) & (train.target_time + pd.Timedelta(hours=config["observation_delay_hours"]) < first_issue)]
    if len(core) < 1000 or len(tail) < 100:
        raise ValueError("Insufficient chronological inner training / stopping window")
    return core, tail


def fit_learner(train, features, name, config, variant="default", fixed_iterations=None):
    started = time.perf_counter()
    params = model_parameters(name, config, variant, fixed_iterations)
    stopping = {}
    if fixed_iterations is None:
        core, tail = inner_split(train, config)
        x_core, pilot_schema = encode_fit(core, features, name, config["category_columns"])
        x_tail, _ = encode_transform(tail, pilot_schema)
        pilot_params = dict(params)
        if name == "XGBoost":
            pilot_params["early_stopping_rounds"] = config["early_stopping_rounds"]
        pilot = new_model(name, pilot_params)
        if name == "CatBoost":
            pilot.fit(x_core, core[TARGET], cat_features=list(pilot_schema["categories"]),
                      eval_set=(x_tail, tail[TARGET]), early_stopping_rounds=config["early_stopping_rounds"], verbose=False)
            rounds = max(1, pilot.get_best_iteration() + 1)
        elif name == "LightGBM":
            import lightgbm as lgb
            pilot.fit(x_core, core[TARGET], eval_set=[(x_tail, tail[TARGET])], eval_metric="l1",
                      callbacks=[lgb.early_stopping(config["early_stopping_rounds"], verbose=False)])
            rounds = max(1, pilot.best_iteration_)
        else:
            pilot.fit(x_core, core[TARGET], eval_set=[(x_tail, tail[TARGET])], verbose=False)
            rounds = max(1, pilot.best_iteration + 1)
        stopping = {"inner_train_max_target": str(core.target_time.max()), "inner_valid_min_target": str(tail.target_time.min()),
                    "inner_first_issue": str(tail.forecast_issue_time.min()), "core_rows": len(core), "tail_rows": len(tail)}
    else:
        rounds = int(fixed_iterations)
    params = model_parameters(name, config, variant, rounds)
    model = new_model(name, params)
    x_train, schema = encode_fit(train, features, name, config["category_columns"])
    if name == "CatBoost":
        model.fit(x_train, train[TARGET], cat_features=list(schema["categories"]), verbose=False)
    else:
        model.fit(x_train, train[TARGET])
    return {"model": model, "schema": schema, "model_name": name, "parameters": params, "iterations": rounds,
            "training_seconds": time.perf_counter() - started, "stopping": stopping,
            "train_rows": len(train), "train_max_target": str(train.target_time.max()),
            "train_max_available": str((train.target_time + pd.Timedelta(hours=config["observation_delay_hours"])).max())}


def predict_learner(bundle, frame, bounds=(0, 1)):
    x, unseen = encode_transform(frame, bundle["schema"])
    result = np.asarray(bundle["model"].predict(x), float)
    if not np.isfinite(result).all():
        raise ValueError("Non-finite model output")
    return np.clip(result, *bounds), unseen


def segment_columns(architecture):
    return {"global": [], "horizon": ["horizon_bucket"], "turbine": ["turbine_id"],
            "horizon_turbine": ["horizon_bucket", "turbine_id"]}[architecture]


def segments(frame, architecture):
    cols = segment_columns(architecture)
    if not cols:
        return [("global", {}, frame)]
    output = []
    for key, part in frame.groupby(cols, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        output.append(("__".join(map(str, key)), dict(zip(cols, key)), part))
    return output


def subset(frame, match):
    mask = pd.Series(True, index=frame.index)
    for key, value in match.items():
        mask &= frame[key] == value
    return frame.loc[mask]
