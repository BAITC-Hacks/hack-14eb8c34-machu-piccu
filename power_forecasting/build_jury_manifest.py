"""Maintainer command: inventory the explicitly included jury artifacts, not raw caches."""
import argparse
import json
from pathlib import Path

from judge import fingerprint


def build(root):
    registry = json.loads((root / "models/model_registry.json").read_text(encoding="utf-8"))
    run = registry["run_id"]
    explicit = ["config.yaml", "ml_config.json", "requirements-jury.txt", "requirements-ml.txt",
                "data/final/feature_columns.json", "data/final/run_config.json",
                "data/final/training_dataset.parquet", "data/final/competition_features.parquet",
                "data/final/offline_test_with_targets.parquet", "data/final/training_weather_dataset.parquet",
                "data/processed/scada_hourly.parquet", "models/environment.json", "models/feature_groups.json",
                "models/final_features.json", "models/model_registry.json", "reports/validation_folds.csv",
                "reports/model_leaderboard.csv", "reports/ml_summary.json",
                "predictions/final_forecast.parquet", "predictions/final_forecast.csv", "predictions/validation_predictions.parquet"]
    files = {root / name for name in explicit}
    files.update((root / "models" / run).glob("*"))
    files.update((root / "experiments" / run).rglob("*"))
    files.update(root.glob("*.py"))
    files.update((root / "src").glob("*.py"))
    files.update((root / "tests").glob("*.py"))
    records = []
    for path in sorted(files):
        if path.is_dir():
            continue
        if not path.is_file():
            raise FileNotFoundError(path)
        mode = "text_lf" if path.suffix in {".json", ".yaml", ".csv", ".txt", ".py", ".md"} else "binary"
        records.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                        "hash_mode": mode, "sha256": fingerprint(path, mode)})
    manifest = {"schema_version": 1, "run_id": run, "purpose": "Offline jury inference and chronological validation replay",
                "text_hash_rule": "Replace CRLF bytes with LF before SHA-256; binary files hashed unchanged",
                "files": records}
    (root / "jury_bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "reports/ml_active_run.json").write_text(json.dumps({"run_id": run, "run_directory": "experiments/" + run}, indent=2), encoding="utf-8")
    print(f"Manifest: {len(records)} files, {sum(row['bytes'] for row in records):,} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    build(parser.parse_args().root.resolve())
