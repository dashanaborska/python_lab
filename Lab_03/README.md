# Sport Results — Streaming

Лабораторна робота №3 з дисципліни «Професійний Python».
Тема: «Ітератори, генератори та потокова обробка даних».
Варіант 9 — «Потокова обробка спортивних результатів».

## Input

CSV-файл із полями:

```text
athlete,sport,result,category,timestamp
```

Невеликий приклад з помилковими рядками — `data/sample.csv`.
Великі набори (100 000 – 1 000 000 записів) генеруються командою `sport-results-generate` у `data/generated/`.

## Pipeline

```text
CSV -> read_rows() -> clean_rows() -> validate() -> parse_rows()
    -> filter_records() -> normalize() -> batching / aggregation -> result
```

Реалізовано:

- streaming validation спортивних результатів з підрахунком invalid records;
- фільтрацію за видом спорту та категорією;
- найкращий результат і streaming average;
- рейтинг результатів (`heapq.nlargest` по потоку);
- pairwise аналіз зміни послідовних результатів;
- batching (фіксований та dynamic);
- отримання перших N результатів за умовою (`islice`);
- eager vs lazy experiment (час, peak memory, time to first result, early termination).

Завдання підвищеної складності: власний iterator class, recursive generator із `yield from`,
infinite generator + `islice`, `chain`, `accumulate`, `pairwise`, `groupby`, dynamic batching,
pipeline із декількох files, streaming export, підрахунок invalid records, logging pipeline stages,
time-to-first-result, lazy search із early termination, порівняння пам'яті list vs generator.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

## Run

```bash
sport-results-generate 100000
sport-results
sport-results-experiment
```

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Project structure

```text
Lab_03/
├── .gitignore
├── pyproject.toml
├── README.md
├── data/
│   └── sample.csv
├── report/
│   └── Lab_03_Naborska.pdf
├── src/
│   └── sport_results/
│       ├── __init__.py
│       ├── analytics.py
│       ├── batching.py
│       ├── config.py
│       ├── experiments.py
│       ├── export.py
│       ├── filters.py
│       ├── generator.py
│       ├── iterators.py
│       ├── main.py
│       ├── models.py
│       ├── parsers.py
│       ├── pipeline.py
│       ├── readers.py
│       └── transform.py
└── tests/
    └── test_stream.py
```

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
