"""Read-only SCADA audit. Does not infer timezone or impute missing data."""
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "Статистическое время"
NUMERIC = {
    "wind_speed": "Средняя скорость ветра(m/s)",
    "normalized_active_power": "Нормализованная активная мощность",
    "temperature": "Средняя температура окружающей среды(°C)",
}


def load_config():
    # JSON syntax is a strict YAML 1.2 subset. No optional YAML parser needed.
    return json.loads((ROOT / "config.yaml").read_text(encoding="utf-8"))


def inspect_file(path, turbine_id):
    values = {key: [] for key in NUMERIC}
    nulls = Counter()
    invalid_numeric = Counter()
    times, invalid_times = [], []
    ids = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        required = {TIMESTAMP, *NUMERIC.values()}
        if not required.issubset(columns or []):
            raise ValueError(f"Missing required SCADA columns in {path.name}")
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            if None in row:
                raise ValueError(f"Malformed CSV row {row_count}: {path.name}")
            ids.append(row.get("ID"))
            for col in columns:
                nulls[col] += int(not (row.get(col) or "").strip())
            try:
                times.append(datetime.strptime(row[TIMESTAMP], "%Y-%m-%d %H:%M:%S"))
            except (ValueError, TypeError):
                invalid_times.append(row_count)
            for key, col in NUMERIC.items():
                try:
                    value = float(row[col])
                    if not math.isfinite(value):
                        raise ValueError("Non-finite number")
                    values[key].append(value)
                except (ValueError, TypeError):
                    invalid_numeric[col] += 1
    unique = sorted(set(times))
    if len(unique) < 2:
        raise ValueError(f"Insufficient timestamps in {path.name}")
    gaps = [(b - a).total_seconds() for a, b in zip(unique, unique[1:])]
    cadence = Counter(gaps).most_common(1)[0][0]
    on_grid = all((t - unique[0]).total_seconds() % cadence == 0 for t in unique)
    expected = int((unique[-1] - unique[0]).total_seconds() / cadence) + 1
    hourly = Counter(t.replace(minute=0, second=0) for t in times)
    hours_expected = int((unique[-1].replace(minute=0, second=0) - unique[0].replace(minute=0, second=0)).total_seconds() / 3600) + 1
    return {
        "turbine_id": turbine_id, "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "format": "CSV, comma delimiter, UTF-8, decimal point",
        "columns": columns, "rows": row_count,
        "timestamp_min": unique[0].isoformat(), "timestamp_max": unique[-1].isoformat(),
        "timezone": None, "timestamp_convention": None,
        "turbine_id_column": "turbine_id" in columns,
        "null_cells": dict(nulls), "invalid_numeric": dict(invalid_numeric),
        "invalid_timestamp_rows": invalid_times,
        "duplicate_timestamps": len(times) - len(unique),
        "duplicate_ids": len(ids) - len(set(ids)),
        "sorted_timestamps": times == sorted(times),
        "cadence_seconds": cadence, "all_on_cadence_grid": on_grid,
        "expected_timestamps": expected,
        "missing_timestamps": expected - len(unique) if on_grid else None,
        "missing_timestamp_pct": 100 * (expected - len(unique)) / expected if on_grid else None,
        "empty_hours": hours_expected - len(hourly),
        "hour_sample_counts": dict(sorted(Counter(hourly.values()).items())),
        "max_gap_hours": max(gaps) / 3600,
        "ranges": {key: {"min": min(v), "max": max(v)} if v else None for key, v in values.items()},
        "competition_rows": sum(t >= datetime(2026, 2, 1) and t < datetime(2026, 3, 1) for t in times),
    }


def main():
    config = load_config()
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    results = [inspect_file(ROOT / filename, turbine_id) for turbine_id, filename in config["input_files"].items()]
    (reports / "input_data_profile.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Анализ исходных SCADA данных", "",
        "Сформирован скриптом `python -m src.input_data`. Исходные файлы не изменяются.", "",
        "Timezone в CSV отсутствует. Pipeline оценивает offset по архивным прогнозам; результат в timezone_decision.md. Параметр timezone в config.yaml — fallback при неоднозначности.",
        "Не установлено, обозначает timestamp начало или конец интервала, и с какой задержкой публикуется наблюдение.",
        "Эти параметры необходимы для честной оценки прошлых ошибок провайдеров.", "",
        "Данные начинаются 11 марта 2023, а не 1 марта. Несмотря на имена файлов, февральских значений 2026 нет.", "",
        "Столбцы: " + "; ".join(f"`{col}`" for col in results[0]["columns"]), "",
        "ID — номер записи; turbine_id назначается явным соответствием имени файла в config.yaml.", "",
        "| Показатель | turbine_1 | turbine_2 |", "|---|---:|---:|"]
    for label, key in [("Строк", "rows"), ("Начало", "timestamp_min"), ("Конец", "timestamp_max"),
                       ("Основной шаг, сек", "cadence_seconds"), ("Дубликаты времени", "duplicate_timestamps"),
                       ("Пропущено временных точек", "missing_timestamps"), ("Полностью пустые часы", "empty_hours"),
                       ("Наибольший разрыв, часов", "max_gap_hours"), ("Строк за февраль 2026", "competition_rows")]:
        lines.append(f"| {label} | {results[0][key]} | {results[1][key]} |")
    for key, label in [("wind_speed", "Ветер, м/с"), ("temperature", "Температура, °C"), ("normalized_active_power", "Мощность, нормализованная")]:
        ranges = [f"{r['ranges'][key]['min']} … {r['ranges'][key]['max']}" for r in results]
        lines.append(f"| {label} | {ranges[0]} | {ranges[1]} |")
    lines += ["", "Подробные количества null, некорректных значений, распределение числа измерений в часе и SHA256 файлов сохранены в `input_data_profile.json`.", "",
        "Мощность дана в нормализованных единицах. Формула нормализации, номинальная мощность и высота датчика ветра документально не определены.",
        "Нельзя объявлять сумму двух нормализованных значений физической мощностью станции без этих сведений.",
        "Почасовое среднее шести измерений — возможная схема агрегации; она требует подтверждения смысла timestamp. Пропуски не заполнялись.", ""]
    (reports / "input_data_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({r["turbine_id"]: {k: r[k] for k in ["rows", "timestamp_min", "timestamp_max", "missing_timestamps", "duplicate_timestamps", "ranges"]} for r in results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
