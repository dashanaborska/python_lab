import argparse
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from sport_results.config import load_config
from sport_results.exceptions import (
    ApplicationError,
    ConfigurationError,
    DataError,
)
from sport_results.logging_config import setup_logging
from sport_results.services import ImportService

logger = logging.getLogger("sport_results.main")

EXIT_OK = 0
EXIT_DATA = 1
EXIT_CONFIG = 2


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Імпорт спортивних результатів"
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--mode", choices=("strict", "tolerant"))
    return parser.parse_args(argv)


def print_stats(service: ImportService, success: bool = True) -> None:
    stats = service.stats
    config = service.config
    print(f"Режим:        {config.processing.mode}")
    print(f"Оброблено:    {stats.total}")
    print(f"Valid:        {stats.valid}")
    print(f"Invalid:      {stats.invalid}")
    print(f"Exported:     {stats.exported}")
    for field, count in sorted(stats.by_field.items()):
        print(f"  invalid {field:10}{count}")
    if success:
        print(f"JSON export:  {config.output.path}")
        print(f"Error report: {config.output.errors_path}")
        print(f"Summary:      {config.output.summary_path}")
    else:
        print("Output не змінено (atomic write скасовано)")
    print(f"Log:          {config.logging.path}")


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    env = dict(os.environ)
    if args.mode:
        env["SPORT_RESULTS_MODE"] = args.mode
    try:
        config = load_config(args.config, env)
    except ConfigurationError as error:
        cause = f" ({error.__cause__})" if error.__cause__ else ""
        print(f"CONFIG ERROR: {error}{cause}", file=sys.stderr)
        return EXIT_CONFIG
    setup_logging(config.logging)
    service = ImportService(config)
    try:
        service.run()
    except DataError as error:
        logger.critical("Імпорт не виконано: %s", error)
        print_stats(service, success=False)
        return EXIT_DATA
    except ApplicationError as error:
        logger.exception("Помилка застосунку: %s", error)
        return EXIT_DATA
    print_stats(service)
    return EXIT_OK


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
