from pathlib import Path

import pytest

from sport_results.files import atomic_write


@pytest.mark.parametrize("run", range(3))
def test_each_run_gets_clean_directory(tmp_path: Path, run: int) -> None:
    assert list(tmp_path.iterdir()) == []
    with atomic_write(tmp_path / "out.json") as file:
        file.write(str(run))
    print(f"run {run}: {tmp_path.name}")
    assert (tmp_path / "out.json").read_text(encoding="utf-8") == str(run)
