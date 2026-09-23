# Проверка проекта жюри

Ветка: `feature/jury-ready`. Проверяемая ML-часть — **power_forecasting/**.

В комплект включены подготовленные данные, финальные модели, прогноз и out-of-fold результаты всех 53 конфигураций. После установки Python-зависимостей проверка работает без интернета, API-ключей и скачивания погоды. Git LFS не требуется.

## 1. Быстрый запуск — Windows PowerShell

Нужны Git и Python 3.12:

```powershell
git clone --branch feature/jury-ready https://github.com/BAITC-Hacks/hack-14eb8c34-machu-piccu.git
cd hack-14eb8c34-machu-piccu/power_forecasting
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-jury.txt
.\.venv\Scripts\python.exe judge.py
```

Если `py` отсутствует, используйте `python -m venv .venv`, предварительно убедившись, что `python --version` показывает 3.12.

## 2. Linux / macOS

```bash
git clone --branch feature/jury-ready https://github.com/BAITC-Hacks/hack-14eb8c34-machu-piccu.git
cd hack-14eb8c34-machu-piccu/power_forecasting
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-jury.txt
.venv/bin/python judge.py
```

Для LightGBM на Linux требуется OpenMP runtime (обычно libgomp1), на macOS — libomp. Основная проверенная среда — Windows x64 / Python 3.12; переносимость на другие ОС не выдаётся за проверенную. Python-зависимости требуют интернет только при первой установке. Сам inference и replay сети не используют.

## 3. Что проверяет judge.py

1. Целостность всех необходимых артефактов по manifest SHA-256. Для текстов нормализуются окончания строк LF/CRLF, для Parquet и моделей — точное побайтное совпадение.
2. Версии библиотек; при несовпадении — понятная ошибка с командой установки.
3. Совпадение ключей/targets out-of-fold прогнозов с исходным training dataset для всех 53 конфигураций. MAE/RMSE считаются заново из сохранённых прогнозов.
4. Загрузка четырёх сохранённых LightGBM checkpoints и повторное получение всех 2 688 февральских прогнозов.
5. Сопоставление нового прогноза с сохранённым эталоном, диапазон [0,1] и доступность обучающих меток на момент каждого forecast issue.

**Важно:** базовая команда заново считает метрики сохранённых out-of-fold прогнозов, а не заново обучает все 53 конфигурации. Она не применяет обученную на январе финальную модель к октябрю для получения «красивых» метрик.

Результат проверки: `jury_results/verification.json` и сообщения PASS в консоли. Прогноз: `predictions/final_forecast.csv` и `.parquet`.

Только проверить файлы, без установки библиотек:

```bash
python judge.py --check-only
```

## 4. Честное повторное обучение победителя

В активированном окружении или через явный путь к его Python:

```bash
python judge.py --retrain-winner
python -m src.run_tests
```

`--retrain-winner` действительно переобучает LightGBM на каждом из четырёх временных folds. Early stopping использует только внутренний прошлый период. Weather-performance признаки проверочного месяца не получают его SCADA-наблюдений. Полученные OOF predictions сравниваются с оригиналом; численная разница больше 1e-8 вызывает ошибку, а не замалчивается.

Проверочные месяцы: октябрь, ноябрь, декабрь 2025 и январь 2026. Модели не обучаются на данных после первого forecast issue проверочного месяца. Все повторы D1/D2 одного target остаются на одной стороне split.

## 5. Полный турнир и произвольное переобучение

```bash
python -m pip install -r requirements-ml.txt
python train.py
python predict.py
```

Турнир включает CatBoost/LightGBM/XGBoost, weather-группы, 10/15/20/30/50/206 признаков, tuning и разделение по турбинам/горизонтам. Совместимый сохранённый run может возобновляться из кэша. На другой платформе/версиях изменится fingerprint, и обучение выполнится заново. `judge.py --retrain-winner` — способ гарантированно проверить свежую тренировку победителя без ожидания полного турнира.

`train.py` меняет модели и отчёты. Для аудита именно опубликованного результата запускайте judge.py **до** самостоятельного изменения конфигурации/переобучения; экспериментируйте в отдельном клоне. Manifest специально обнаруживает изменения артефактов.

## 6. Ключевые результаты

| Показатель | Значение |
|---|---:|
| Модель | LightGBM, общая для двух турбин и D1/D2 |
| Количество признаков | 15 |
| MAE D1 | 0.142337 |
| MAE D2 | 0.158751 |
| MAE overall | 0.150544 |
| RMSE overall | 0.228134 |
| MAE / MAE лучшего простого baseline | 0.500381 |

MAE × 100 = процентные пункты нормализованной шкалы, **не accuracy**. 0.500381 — отношение ошибок, приблизительно двукратное снижение относительно исторической медианы turbine × hour.

## 7. Что читать

- [Итоговый ML-отчёт](reports/final_ml_report.md).
- [Leaderboard](reports/model_leaderboard.md).
- [Ablation study](reports/ablation_study.md).
- [Отбор признаков](reports/final_feature_selection.md).
- [Timezone decision](reports/timezone_decision.md).
- [Registry моделей](models/model_registry.json).

joblib может исполнять код при загрузке: запускайте только модели из доверенной версии этого репозитория. Manifest обнаруживает случайную подмену файлов, но не является цифровой подписью доверенного автора.

## 8. Методология и ограничения

- Февральские targets отсутствуют. Указанные метрики — chronological model-selection validation на предыдущих месяцах, не независимый финальный test. Использование тех же месяцев для отбора вносит selection optimism.
- Previous Runs API provides forecasts at fixed historical lead-time offsets but does not expose exact historical API publication timestamps for every individual value.
- Timezone UTC+5 ранее inferred, не подтверждён оператором. Его upstream inference включал часть проверочного периода; строго независимой end-to-end проверкой timezone эти ML-метрики не являются.
- В корне репозитория находится **другое решение WindAgent** с UTC+6 и другими горизонтами. Его метрики/прогнозы нельзя непосредственно сравнивать или смешивать с этим модулем.
- Здесь lead_hours = 1–48, D1=1–24, D2=25–48, weather archive nominal offsets =24/48h. 2 688 строк включают обе версии прогноза одного target. Это не автоматическая замена 1 344-строчного submission корневого решения.
- SCADA availability = конец часа + 60 минут — явное допущение. Три ранних as-of модели не дают будущим январским меткам попасть в ранние прогнозы февраля.
- Ветка делает компактный ML-эксперимент проверяемым, но не объявляет его интегрированным с root agent и не меняет существующий agent pipeline.

Кэш HTTP, 296-МБ дублирующий CSV и локальные зависимости не включены: для этой оценки они не нужны. Исходные SCADA уже находятся в корневом dataset/ и повторно не копируются; добавленные Parquet содержат подготовленные обучающие данные и доступны получателям этой ветки.
