"""Sequence models (RNN / LSTM) and a small custom network, as challengers.

Like `src/benchmark.py`, nothing here is imported by the forecast pipeline --
this module only produces evidence about whether a neural approach beats the
shipped gradient booster.

Why a sequence model is worth trying at all
-------------------------------------------
The production model predicts one hour from one feature row. Its residuals are
strongly autocorrelated (lag-1 ACF 0.81 against a white-noise band of +/-0.04),
which says errors arrive as multi-hour episodes -- whole weather events the NWP
got wrong -- rather than as independent per-hour noise.

What a sequence model may and may not do with that
--------------------------------------------------
It may *not* feed on its own recent errors: at 24-47 h lead the actual for hour
T-1 is as unknown as the actual for hour T. That is why the residual ACF decays
from 0.81 at lag 1 to 0.10 at lag 24 -- the lag-24 part is the only piece a
causal forecaster could ever observe.

What it *may* use is the shape of the weather forecast across the window, which
is known in full at issue time. That also makes a bidirectional encoder
legitimate here: reading the NWP sequence backwards uses no information that
post-dates the forecast. The production model only sees this shape through
hand-built lag and rolling columns; a recurrent net can learn it directly.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from src import config, metrics, train

SEQ_LEN = 48
TRAIN_STRIDE = 3      # overlapping windows; augmentation is what makes ~660 blocks trainable
EVAL_STRIDE = SEQ_LEN  # non-overlapping at evaluation, so every hour is predicted exactly once
BATCH_SIZE = 128
MAX_EPOCHS = 200
PATIENCE = 25
SEED = 42


# Apple's MPS backend segfaults on `nn.RNN`/`nn.LSTM` kernels in torch 2.14,
# so recurrent models run on CPU by default. The tensors here are small
# (~8.7k windows x 48 x 63), so CPU costs seconds, not minutes. Override with
# WINDAGENT_TORCH_DEVICE=mps once the upstream kernels are fixed.
_DEVICE_OVERRIDE = os.environ.get("WINDAGENT_TORCH_DEVICE")


def device(recurrent: bool = False) -> torch.device:
    if _DEVICE_OVERRIDE:
        return torch.device(_DEVICE_OVERRIDE)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available() and not recurrent:
        return torch.device("mps")
    return torch.device("cpu")


# --------------------------------------------------------------------------
# Time-series dataset preparation
# --------------------------------------------------------------------------
@dataclass
class Standardiser:
    """Feature imputation and scaling, fitted on training rows only."""

    median: np.ndarray = field(default=None)
    mean: np.ndarray = field(default=None)
    std: np.ndarray = field(default=None)

    def fit(self, x: np.ndarray) -> "Standardiser":
        self.median = np.nanmedian(x, axis=0)
        filled = np.where(np.isnan(x), self.median, x)
        self.mean = filled.mean(axis=0)
        self.std = filled.std(axis=0)
        self.std[self.std < 1e-8] = 1.0
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        filled = np.where(np.isnan(x), self.median, x)
        return (filled - self.mean) / self.std


def contiguous_runs(frame: pd.DataFrame) -> list[pd.DataFrame]:
    """Split a turbine's hourly series wherever an hour is missing.

    Windows must never straddle a gap: a sequence model would otherwise read a
    two-month outage as a one-hour step and learn a transition that never
    happens.
    """
    runs: list[pd.DataFrame] = []
    for _, group in frame.groupby("turbine", sort=False):
        ordered = group.sort_values("time").reset_index(drop=True)
        breaks = ordered["time"].diff() != pd.Timedelta("1h")
        for _, run in ordered.groupby(breaks.cumsum()):
            if len(run) >= SEQ_LEN:
                runs.append(run)
    return runs


def build_sequences(
    frame: pd.DataFrame,
    features: list[str],
    scaler: Standardiser,
    seq_len: int = SEQ_LEN,
    stride: int = TRAIN_STRIDE,
    require_target: bool = True,
):
    """Slice contiguous hourly runs into fixed-length windows.

    Returns tensors shaped (N, seq_len, F) for inputs and (N, seq_len) for
    targets, plus a mask marking hours whose production is actually known, and
    the wall-clock index of every predicted hour so results can be joined back
    to the other models' predictions.
    """
    xs, ys, masks, stamps, turbines = [], [], [], [], []
    for run in contiguous_runs(frame):
        values = scaler.transform(run[features].to_numpy(dtype=np.float32))
        target = run["power"].to_numpy(dtype=np.float32)
        known = ~np.isnan(target)
        times = run["time"].to_numpy()
        key = run["turbine"].iloc[0]

        for start in range(0, len(run) - seq_len + 1, stride):
            end = start + seq_len
            window_mask = known[start:end]
            if require_target and window_mask.sum() < seq_len // 2:
                continue  # mostly-missing windows teach nothing
            xs.append(values[start:end])
            ys.append(np.nan_to_num(target[start:end]))
            masks.append(window_mask)
            stamps.append(times[start:end])
            turbines.append(np.full(seq_len, key))

    if not xs:
        raise RuntimeError("no sequences could be built")
    return (
        torch.from_numpy(np.stack(xs)),
        torch.from_numpy(np.stack(ys)),
        torch.from_numpy(np.stack(masks)),
        np.stack(stamps),
        np.stack(turbines),
    )


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
class RecurrentForecaster(nn.Module):
    """Vanilla RNN or LSTM over the forecast window, one power value per hour."""

    def __init__(self, n_features: int, hidden: int = 96, layers: int = 2,
                 cell: str = "lstm", bidirectional: bool = False, dropout: float = 0.15):
        super().__init__()
        rnn_cls = {"rnn": nn.RNN, "lstm": nn.LSTM}[cell]
        self.rnn = rnn_cls(
            input_size=n_features, hidden_size=hidden, num_layers=layers,
            batch_first=True, bidirectional=bidirectional,
            dropout=dropout if layers > 1 else 0.0,
        )
        width = hidden * (2 if bidirectional else 1)
        self.head = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 64), nn.GELU(), nn.Linear(64, 1))

    def forward(self, x):
        out, _ = self.rnn(x)
        # Sigmoid keeps output inside [0, 1] by construction -- power is
        # physically bounded, so the network should not have to learn that.
        return torch.sigmoid(self.head(out)).squeeze(-1)


class SmallNet(nn.Module):
    """Custom feed-forward network: a few hidden layers, no recurrence.

    The control for the sequence experiment. If this matches the RNNs, then
    whatever they gained came from capacity rather than from temporal
    modelling, and the sequence framing is not what mattered.
    """

    def __init__(self, n_features: int, widths: tuple[int, ...] = (256, 128, 64), dropout: float = 0.15):
        super().__init__()
        layers: list[nn.Module] = []
        previous = n_features
        for width in widths:
            layers += [nn.Linear(previous, width), nn.BatchNorm1d(width), nn.GELU(), nn.Dropout(dropout)]
            previous = width
        layers.append(nn.Linear(previous, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        flat = x.reshape(-1, x.shape[-1])
        return torch.sigmoid(self.net(flat)).reshape(x.shape[0], x.shape[1])


ARCHITECTURES = {
    "rnn":    lambda f: RecurrentForecaster(f, cell="rnn", hidden=64, layers=2, dropout=0.25),
    "lstm":   lambda f: RecurrentForecaster(f, cell="lstm", hidden=64, layers=2, dropout=0.25),
    "bilstm": lambda f: RecurrentForecaster(f, cell="lstm", hidden=48, layers=2,
                                            bidirectional=True, dropout=0.25),
    "smallnet": lambda f: SmallNet(f, widths=(128, 64, 32), dropout=0.20),
    # Deliberately tiny. With ~660 genuinely independent sequences behind the
    # window count, capacity is the enemy here, not the constraint.
    "tinynet": lambda f: SmallNet(f, widths=(64, 32), dropout=0.10),
    "micronet": lambda f: SmallNet(f, widths=(32,), dropout=0.05),
}


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------
def masked_loss(prediction, target, mask):
    """Huber loss over observed hours only.

    Huber rather than MSE because curtailment and outages put genuine outliers
    in the target; squared error would let a handful of them steer the fit.
    """
    per_hour = nn.functional.huber_loss(prediction, target, reduction="none", delta=0.15)
    weighted = per_hour * mask
    return weighted.sum() / mask.sum().clamp(min=1.0)


def fit_network(name: str, train_tensors, valid_tensors, verbose: bool = True):
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    dev = device(recurrent=name in {"rnn", "lstm", "bilstm"})

    x_tr, y_tr, m_tr = (t.to(dev) for t in train_tensors[:3])
    x_va, y_va, m_va = (t.to(dev) for t in valid_tensors[:3])

    net = ARCHITECTURES[name](x_tr.shape[-1]).to(dev)
    # Overlapping windows make the sample count flattering: at stride 3 two
    # neighbouring windows share 45 of 48 hours, so ~8.7k windows carry only
    # ~660 independent sequences. A small learning rate and real weight decay
    # are what keep that from being memorised in the first few epochs.
    optimiser = torch.optim.AdamW(net.parameters(), lr=6e-4, weight_decay=3e-3)
    schedule = torch.optim.lr_scheduler.ReduceLROnPlateau(optimiser, factor=0.5, patience=6)
    loader = DataLoader(TensorDataset(x_tr, y_tr, m_tr), batch_size=BATCH_SIZE, shuffle=True)

    best_loss, best_state, stale = float("inf"), None, 0
    for epoch in range(MAX_EPOCHS):
        net.train()
        for xb, yb, mb in loader:
            optimiser.zero_grad()
            loss = masked_loss(net(xb), yb, mb)
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            optimiser.step()

        net.eval()
        with torch.no_grad():
            prediction = net(x_va)
            # Select on validation MAE, the metric actually reported. Selecting
            # on the training loss instead would pick whichever epoch best fits
            # Huber's particular treatment of outliers.
            validation = ((prediction - y_va).abs() * m_va).sum().item() / m_va.sum().clamp(min=1).item()
        schedule.step(validation)

        if validation < best_loss - 1e-5:
            best_loss, stale = validation, 0
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            stale += 1
            if stale >= PATIENCE:
                break
        if verbose and epoch % 10 == 0:
            print(f"    epoch {epoch:3d}  valid {validation:.5f}  best {best_loss:.5f}")

    net.load_state_dict(best_state)
    net.eval()
    return net, best_loss, epoch + 1


def predict_hours(net, tensors) -> pd.DataFrame:
    """Flatten window predictions back into one row per forecast hour."""
    x, _, mask, stamps, turbines = tensors
    target_device = next(net.parameters()).device
    with torch.no_grad():
        prediction = net(x.to(target_device)).cpu().numpy()
    return pd.DataFrame({
        "turbine": turbines.reshape(-1),
        "time": pd.to_datetime(stamps.reshape(-1)),
        "pred": prediction.reshape(-1),
        "known": mask.numpy().reshape(-1),
    })


# --------------------------------------------------------------------------
# Experiment
# --------------------------------------------------------------------------
def day_ahead_series(frame: pd.DataFrame) -> pd.DataFrame:
    """The constant-24h-lead hourly series, which is what a window slides over.

    `previous_day1` is a fixed 24 h offset from each target hour, so these rows
    form one continuous series at a single lead -- unlike a mix of leads, where
    a window would silently splice forecasts of different quality together.
    """
    return frame[frame["lead_hours"] < 48].sort_values(["turbine", "time"]).reset_index(drop=True)


REFERENCE_CACHE = config.ARTIFACT_DIR / "reference_day_ahead.parquet"


def reference_predictions(refresh: bool = False) -> pd.DataFrame:
    """Baseline (LightGBM) predictions on the same hold-out hours.

    Produced in a separate interpreter: PyTorch and LightGBM each bring their
    own OpenMP runtime, and on macOS hosting both in one process segfaults as
    soon as LightGBM parallelises. The subprocess never imports torch, so the
    two runtimes never meet.
    """
    if refresh or not REFERENCE_CACHE.exists():
        subprocess.run(
            [sys.executable, "-c",
             "from src import benchmark;"
             "benchmark.dump_reference_predictions("
             f"r'{REFERENCE_CACHE}', candidate=('lightgbm','lightgbm_l1'))"],
            check=True, cwd=str(config.ROOT),
        )
    return pd.read_parquet(REFERENCE_CACHE)


def prepare_fold_local(valid_start="2025-10-01", valid_end="2026-01-31"):
    """Chronological split plus the power-curve prior, without importing LightGBM."""
    from src import dataset

    pooled = train.load_pooled()
    labelled = pooled[pooled["issue_time"] <= pd.Timestamp(train.TRAIN_ISSUE_END)]
    tr = labelled[labelled["issue_time"] < valid_start].copy()
    va = labelled[(labelled["issue_time"] >= valid_start) & (labelled["issue_time"] < valid_end)].copy()
    curve = dataset.fit_effective_power_curve(tr)
    return dataset.attach_power_curve_prior(tr, curve), dataset.attach_power_curve_prior(va, curve)


def run_experiment(architectures: list[str], verbose: bool = True) -> dict:
    tr_raw, va_raw = prepare_fold_local()
    features = train.FEATURE_COLUMNS

    tr_series, va_series = day_ahead_series(tr_raw), day_ahead_series(va_raw)
    scaler = Standardiser().fit(tr_series[features].to_numpy(dtype=np.float32))

    train_tensors = build_sequences(tr_series, features, scaler, stride=TRAIN_STRIDE)
    valid_tensors = build_sequences(va_series, features, scaler, stride=EVAL_STRIDE, require_target=False)
    if verbose:
        print(f"train windows {tuple(train_tensors[0].shape)} | "
              f"valid windows {tuple(valid_tensors[0].shape)}")

    # Reference: the production booster, scored on the very same hours.
    reference = reference_predictions(refresh=True)

    results, predictions = {}, {}
    for name in architectures:
        if verbose:
            print(f"\n-- {name} --")
        net, best, epochs = fit_network(name, train_tensors, valid_tensors, verbose)
        hourly = predict_hours(net, valid_tensors).rename(columns={"pred": name})
        predictions[name] = hourly[["turbine", "time", name]]
        results[name] = {"epochs": epochs, "best_valid_loss": best,
                         "parameters": sum(p.numel() for p in net.parameters())}

    merged = reference
    for name, frame in predictions.items():
        merged = merged.merge(frame, on=["turbine", "time"], how="left")
    baselines = [c for c in ("lightgbm", "lightgbm_l1") if c in reference.columns]
    scored = merged.dropna(subset=["power", *baselines, *architectures])

    table = []
    for name in [*baselines, *architectures]:
        m = metrics.point_metrics(scored["power"], scored[name])
        row = {"model": name, **{k: m[k] for k in ("mae", "rmse", "r2", "bias")}}
        if name in results:
            row["params"] = results[name]["parameters"]
            row["epochs"] = results[name]["epochs"]
        table.append(row)

    report = pd.DataFrame(table)
    if verbose:
        print(f"\n{'='*74}\nDAY-AHEAD HOLD-OUT (24-47 h), identical {len(scored):,} hours for every model")
        print(report.to_string(index=False, float_format=lambda v: f"{v:9.4f}"))
        base = report[report.model.isin(baselines)].mae.min()
        best_nn = report[~report.model.isin(baselines)].sort_values("mae").iloc[0]
        print(f"\nbest network: {best_nn['model']} MAE {best_nn['mae']:.4f} vs LightGBM {base:.4f} "
              f"({100*(1-best_nn['mae']/base):+.2f}%)")
        print("=" * 74)

    out = config.REPORT_DIR / "deep_comparison.json"
    out.write_text(json.dumps({"table": table, "detail": results,
                               "eval_hours": int(len(scored))}, indent=2, default=float))
    if verbose:
        print(f"Wrote {out}")
    return {"table": table, "detail": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train sequence models as challengers")
    parser.add_argument("--models", nargs="+", default=["rnn", "lstm", "bilstm"],
                        choices=sorted(ARCHITECTURES))
    args = parser.parse_args()
    run_experiment(args.models)


if __name__ == "__main__":
    main()
