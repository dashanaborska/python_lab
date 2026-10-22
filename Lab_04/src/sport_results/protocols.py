from typing import Protocol, runtime_checkable

from sport_results.models import RankingTable
from sport_results.value_objects import AthleteId


@runtime_checkable
class Identified(Protocol):
    @property
    def id(self) -> AthleteId | int: ...


@runtime_checkable
class Reporter(Protocol):
    def report(self, table: RankingTable) -> str: ...


class Exporter(Protocol):
    def export(self, table: RankingTable) -> list[dict[str, str]]: ...
