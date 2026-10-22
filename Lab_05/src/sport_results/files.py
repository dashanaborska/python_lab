import gzip
import logging
import os
import shutil
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Literal, TypeVar

from sport_results.exceptions import ExportError

logger = logging.getLogger(__name__)
T = TypeVar("T")


@contextmanager
def atomic_write(path: Path, backup: bool = False) -> Iterator[IO[str]]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ExportError(f"Не вдалося створити {path.parent}") from error
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temporary)
    os.close(descriptor)
    try:
        if path.suffix == ".gz":
            stream: IO[str] = gzip.open(temp_path, "wt", encoding="utf-8")
        else:
            stream = temp_path.open("w", encoding="utf-8", newline="")
        with stream:
            yield stream
        if backup and path.exists():
            shutil.copy2(path, path.with_name(path.name + ".bak"))
        os.replace(temp_path, path)
        logger.info("Атомарно записано %s", path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        logger.warning("Запис %s скасовано, тимчасовий файл видалено", path)
        raise


class FileTransaction:
    def __init__(self) -> None:
        self._staged: list[tuple[Path, Path]] = []

    def stage(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        staged = path.with_name(f".{path.name}.staged")
        self._staged.append((staged, path))
        return staged

    def __enter__(self) -> "FileTransaction":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        if exc_type is None:
            for staged, target in self._staged:
                os.replace(staged, target)
            logger.info("Transaction: зафіксовано %d файл(и)",
                        len(self._staged))
        else:
            for staged, _ in self._staged:
                staged.unlink(missing_ok=True)
            logger.error("Transaction: відкат через %s", exc_type.__name__)
        return False


def retry(
    action: Callable[[], T],
    attempts: int = 3,
    delay: float = 0.05,
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except PermissionError:
            if attempt == attempts:
                raise
            logger.warning("Файл зайнятий, спроба %d з %d", attempt, attempts)
            time.sleep(delay)
    raise RuntimeError("unreachable")
