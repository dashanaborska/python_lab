from collections.abc import Callable
from dataclasses import dataclass

from sport_results.exceptions import ValidationError
from sport_results.value_objects import Score


class FixedClock:
    def now(self) -> str:
        return "2026-05-01 10:00"


class TightlyCoupledService:
    def __init__(self) -> None:
        self.clock = FixedClock()

    def stamp(self, text: str) -> str:
        return f"[{self.clock.now()}] {text}"


class Clock:
    def __init__(self, source: Callable[[], str]) -> None:
        self._source = source

    def now(self) -> str:
        return self._source()


class InjectedService:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def stamp(self, text: str) -> str:
        return f"[{self.clock.now()}] {text}"


class BaseProcessor:
    def process(self, line: str) -> str:
        name, value = self.parse(line)
        self.validate(value)
        return self.format(name, value)

    def parse(self, line: str) -> tuple[str, float]:
        name, value = line.split(",")
        return name.strip(), float(value)

    def validate(self, value: float) -> None:
        Score(value)

    def format(self, name: str, value: float) -> str:
        return f"{name}: {value:.1f}"


class CsvProcessor(BaseProcessor):
    def parse(self, line: str) -> tuple[str, float]:
        name, value = line.split(";")
        return name.strip(), float(value)


class SemicolonParser:
    def parse(self, line: str) -> tuple[str, float]:
        name, value = line.split(";")
        return name.strip(), float(value)


class ScoreValidator:
    def validate(self, value: float) -> None:
        Score(value)


class UpperFormatter:
    def format(self, name: str, value: float) -> str:
        return f"{name.upper()}: {value:.1f}"


@dataclass
class Processor:
    parser: SemicolonParser
    validator: ScoreValidator
    formatter: UpperFormatter

    def process(self, line: str) -> str:
        name, value = self.parser.parse(line)
        self.validator.validate(value)
        return self.formatter.format(name, value)


def main() -> None:
    print("Варіант A (сервіс сам створює залежність):")
    print(" ", TightlyCoupledService().stamp("результат збережено"))
    print("Варіант B (dependency injection, у тесті підміняємо годинник):")
    fake = InjectedService(Clock(lambda: "TEST-TIME"))
    print(" ", fake.stamp("результат збережено"))
    print()
    print("Inheritance: CsvProcessor(BaseProcessor)")
    print(" ", CsvProcessor().process("Софія Ткачук; 95.1"))
    print("Composition: Processor(parser, validator, formatter)")
    composed = Processor(SemicolonParser(), ScoreValidator(), UpperFormatter())
    print(" ", composed.process("Софія Ткачук; 95.1"))
    try:
        composed.process("Тарас Новак; 120")
    except ValidationError as error:
        print("  валідатор спрацював:", error)


if __name__ == "__main__":
    main()
