from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sport_results.database import Base

CATEGORIES: tuple[str, ...] = (
    "МСМК",
    "МС",
    "КМС",
    "I розряд",
    "II розряд",
    "III розряд",
)


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    athletes: Mapped[list["Athlete"]] = relationship(
        back_populates="sport", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Sport(id={self.id}, name={self.name!r})"


class Athlete(Base):
    __tablename__ = "athletes"
    __table_args__ = (
        UniqueConstraint("name", "sport_id", name="uq_athlete_sport"),
        CheckConstraint("length(trim(name)) > 0", name="ck_athlete_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(20))
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id", ondelete="CASCADE"))

    sport: Mapped[Sport] = relationship(back_populates="athletes")
    results: Mapped[list["Result"]] = relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Athlete(id={self.id}, name={self.name!r})"


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_result_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athletes.id", ondelete="CASCADE")
    )
    score: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    competition_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    competition_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    athlete: Mapped[Athlete] = relationship(back_populates="results")

    def __repr__(self) -> str:
        return f"Result(id={self.id}, score={self.score})"
