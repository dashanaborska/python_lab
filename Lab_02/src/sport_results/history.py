from collections import deque

from sport_results.config import HISTORY_SIZE

operations: deque[str] = deque(maxlen=HISTORY_SIZE)


def last_operations() -> list[str]:
    return list(operations)


def clear_history() -> None:
    operations.clear()
