from abc import ABC, abstractmethod
from collections.abc import Callable, Hashable, Iterator
from typing import Generic, TypeVar

from sport_results.exceptions import DuplicateError, NotFoundError
from sport_results.models import Athlete, Competition
from sport_results.protocols import Identified

K = TypeVar("K", bound=Hashable)
T = TypeVar("T", bound=Identified)


class Repository(ABC, Generic[K, T]):
    @abstractmethod
    def add(self, item: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: K) -> T:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> list[T]:
        raise NotImplementedError


class InMemoryRepository(Repository[K, T]):
    def __init__(self, key: Callable[[T], K]) -> None:
        self._key = key
        self._items: dict[K, T] = {}

    def add(self, item: T) -> None:
        key = self._key(item)
        if key in self._items:
            raise DuplicateError(f"Об'єкт з ключем {key} вже існує")
        self._items[key] = item

    def get(self, key: K) -> T:
        try:
            return self._items[key]
        except KeyError:
            raise NotFoundError(f"Об'єкт {key} не знайдено") from None

    def all(self) -> list[T]:
        return list(self._items.values())

    def find(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self._items.values() if predicate(item)]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, key: object) -> bool:
        return key in self._items


def athlete_repository() -> InMemoryRepository[int, Athlete]:
    return InMemoryRepository(lambda athlete: athlete.id.value)


def competition_repository() -> InMemoryRepository[int, Competition]:
    return InMemoryRepository(lambda competition: competition.id)
