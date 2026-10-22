import logging
from logging.handlers import RotatingFileHandler

from sport_results.config import LoggingConfig

FORMAT = "%(asctime)s %(levelname)-8s %(module)s: %(message)s"


def setup_logging(config: LoggingConfig, console: bool = True) -> None:
    config.path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("sport_results")
    root.handlers.clear()
    root.setLevel(config.level)
    root.propagate = False
    file_handler = RotatingFileHandler(
        config.path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(FORMAT))
    root.addHandler(file_handler)
    if console:
        stream = logging.StreamHandler()
        stream.setLevel(logging.WARNING)
        stream.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(stream)
