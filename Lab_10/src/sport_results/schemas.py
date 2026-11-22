from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sport_results.models import CATEGORIES


class SportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AthleteCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120, examples=["Олена Ковальчук"])
    sport: str = Field(min_length=2, max_length=100, examples=["Плавання"])
    category: str = Field(examples=["КМС"])

    @field_validator("name", "sport")
    @classmethod
    def normalize(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if any(char.isdigit() for char in cleaned):
            raise ValueError("не повинно містити цифр")
        return cleaned

    @field_validator("category")
    @classmethod
    def known_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"допустимі категорії: {', '.join(CATEGORIES)}")
        return value


class AthleteRead(BaseModel):
    id: int
    name: str
    category: str
    sport: str


class ResultCreate(BaseModel):
    athlete_id: int = Field(gt=0, examples=[1])
    score: float = Field(ge=0, le=100, examples=[87.5])
    competition_name: str | None = Field(
        default=None, max_length=120, examples=["Кубок Львова"]
    )
    competition_date: date | None = None


class ResultUpdate(BaseModel):
    score: float | None = Field(default=None, ge=0, le=100)
    competition_name: str | None = Field(default=None, max_length=120)


class ResultRead(BaseModel):
    id: int
    athlete_id: int
    athlete: str
    sport: str
    score: float
    competition_name: str | None


class RankingEntry(BaseModel):
    place: int
    athlete: str
    best: float
    results: int


class SportRanking(BaseModel):
    sport_id: int
    sport: str
    ranking: list[RankingEntry]


class SportStatistics(BaseModel):
    sport_id: int
    sport: str
    results: int
    best: float | None
    average: float | None
    std: float | None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str


class AggregatedRankings(BaseModel):
    rankings: list[SportRanking]
    failed: dict[int, str]
    elapsed: float


class ErrorResponse(BaseModel):
    error: str
    detail: str
