import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO


@contextmanager
def atomic_write(path: Path) -> Iterator[IO[str]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(descriptor)
    temp_path = Path(temporary)
    try:
        with temp_path.open("w", encoding="utf-8", newline="") as file:
            yield file
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
