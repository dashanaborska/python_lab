from collections.abc import Callable, Iterable, Iterator
from itertools import islice
from typing import TypeVar

T = TypeVar("T")


def batched(items: Iterable[T], size: int) -> Iterator[list[T]]:
    if size < 1:
        raise ValueError("Розмір batch має бути додатним.")
    iterator = iter(items)
    while batch := list(islice(iterator, size)):
        yield batch


def dynamic_batches(
    items: Iterable[T],
    limit: float,
    weight: Callable[[T], float],
) -> Iterator[list[T]]:
    batch: list[T] = []
    total = 0.0
    for item in items:
        item_weight = weight(item)
        if batch and total + item_weight > limit:
            yield batch
            batch, total = [], 0.0
        batch.append(item)
        total += item_weight
    if batch:
        yield batch
