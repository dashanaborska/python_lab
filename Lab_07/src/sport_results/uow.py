from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from sport_results.repositories import (
    AthleteRepository,
    ResultRepository,
    SportRepository,
)


class UnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def __enter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        self.sports = SportRepository(self.session)
        self.athletes = AthleteRepository(self.session)
        self.results = ResultRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
