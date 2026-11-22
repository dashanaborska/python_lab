# Sport Results — Parallelism and Optimization

Лабораторна робота №9 з дисципліни «Професійний Python».
Тема: «Паралельність, багатопроцесність та оптимізація».
Варіант 9 — «Облік спортивних результатів».

## Опис

Профілювання та оптимізація аналітики великого масиву спортивних результатів:
рейтинг за індексом результативності, minimum, maximum, average, standard deviation і статистика категорій.

Реалізації:

- `analytics.py` — baseline на Python loops;
- `parallel.py` — `threading.Thread`, `ThreadPoolExecutor`, `ProcessPoolExecutor`, паралельний імпорт
  з декількох джерел, `Lock`, демонстрація race condition;
- `vectorized.py` — NumPy vectorization;
- `cache.py` — кеш рейтингу виду спорту/категорії з invalidation після додавання або зміни результату, `lru_cache`;
- `profiling.py` — `cProfile` і `tracemalloc`;
- `benchmarks/` — власний benchmark framework, CSV і графіки.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
sport-results
sport-results-profile 100000
python -m benchmarks.benchmark
python -m pytest -v
```

Результати benchmark: `benchmarks/results/benchmark_results.csv`, `execution_time.png`, `speedup.png`.

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
