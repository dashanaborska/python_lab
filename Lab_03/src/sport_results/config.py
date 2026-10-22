from pathlib import Path

CATEGORIES: tuple[str, ...] = (
    "МСМК",
    "МС",
    "КМС",
    "I розряд",
    "II розряд",
    "III розряд",
)
SPORTS: tuple[str, ...] = ("Плавання", "Бокс", "Легка атлетика", "Велоспорт")
FIELDS: tuple[str, ...] = (
    "athlete",
    "sport",
    "result",
    "category",
    "timestamp",
)
MIN_RESULT: float = 0.0
MAX_RESULT: float = 100.0
DATA_DIR: Path = Path("data")
GENERATED_DIR: Path = DATA_DIR / "generated"
OUTPUT_DIR: Path = Path("output")
DEFAULT_RECORDS: int = 100_000
INVALID_RATE: float = 0.02
EXPERIMENT_SIZES: tuple[int, ...] = (10_000, 100_000, 500_000)
EARLY_TERMINATION_SIZE: int = 1_000_000
