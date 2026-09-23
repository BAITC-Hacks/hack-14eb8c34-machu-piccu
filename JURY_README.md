# Ветка для оценки жюри

Начните с [power_forecasting/JURY_GUIDE.md](power_forecasting/JURY_GUIDE.md).

В `power_forecasting/` включены **обученные модели, подготовленные Parquet, прогноз, результаты всех 53 экспериментов и проверки**. После установки зависимостей не требуется погода из интернета или ручной перенос файлов.

```bash
cd power_forecasting
python -m pip install -r requirements-jury.txt
python judge.py
python judge.py --retrain-winner
python -m src.run_tests
```

Рекомендуется чистое виртуальное окружение Python 3.12; команды его создания для Windows/Linux/macOS находятся в руководстве.

`judge.py` проверяет артефакты, пересчитывает метрики сохранённых OOF-прогнозов и заново выполняет inference. `--retrain-winner` дополнительно переобучает победителя на четырёх временных folds.

**Не путайте два решения:** root WindAgent и этот изолированный ML-модуль используют разные timezone/horizon assumptions. Root код не изменён, сравнение метрик между ними без унификации методологии некорректно. Февральских targets нет; проверяется воспроизводимость и предшествующая временная validation, а не подтверждённая точность февраля.
