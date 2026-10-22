# Sport Results

Лабораторна робота №1 з дисципліни «Професійний Python».
Варіант 9 — «Облік спортивних результатів».

## Опис

Консольний застосунок для обліку результатів спортсменів.
Для кожного спортсмена зберігаються ім'я, вид спорту, результат (у балах) та категорія.

Можливості:

- додавання результату;
- пошук за видом спорту;
- визначення найкращого результату;
- обчислення середнього результату;
- формування рейтингу спортсменів.

Завдання підвищеної складності:

- menu-driven interface з введенням даних із клавіатури;
- validation input із власними винятками (`ValidationError`, `AthleteNotFoundError`);
- окремий модуль configuration constants (`config.py`);
- використання `dataclass`;
- сортування (рейтинг);
- README з прикладом запуску програми.

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
python -m pip install -e .
```

## Run

```bash
python -m sport_results.main
```

або

```bash
sport-results
```

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Приклад запуску

```text
===== Облік спортивних результатів =====
1. Показати всі результати
2. Додати результат
3. Пошук за видом спорту
4. Найкращий результат
5. Середній результат
6. Рейтинг спортсменів
0. Вихід
Оберіть команду: 6

Місце  Ім'я                Вид спорту         Результат
-------------------------------------------------------
1      Софія Ткачук        Легка атлетика         95.10
2      Максим Бондар       Легка атлетика         92.30
3      Олена Ковальчук     Плавання               87.50
4      Андрій Шевченко     Бокс                   81.00
5      Ірина Мельник       Плавання               78.40
```

## Project structure

```text
python_lab1/
├── .gitignore
├── pyproject.toml
├── README.md
├── report/
│   ├── Lab_01_Naborska.docx
│   └── Lab_01_Naborska.pdf
├── src/
│   └── sport_results/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── main.py
│       ├── models.py
│       ├── services.py
│       └── validators.py
└── tests/
    └── test_services.py
```

- `models.py` — модель даних `Athlete`;
- `services.py` — бізнес-логіка;
- `validators.py` — перевірка введених даних;
- `exceptions.py` — власні винятки;
- `config.py` — конфігураційні константи;
- `main.py` — точка входу та консольне меню.

## Report

Звіт до лабораторної роботи знаходиться в каталозі `report/`.

## Author

Наборська Дарія Русланівна
