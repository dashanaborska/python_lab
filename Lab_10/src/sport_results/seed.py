from datetime import date

from sqlalchemy.orm import Session

from sport_results.schemas import AthleteCreate, ResultCreate
from sport_results.services import SportService

ATHLETES: list[tuple[str, str, str, list[float]]] = [
    ("Олена Ковальчук", "Плавання", "КМС", [87.5, 91.0]),
    ("Ірина Мельник", "Плавання", "I розряд", [78.4]),
    ("Марія Бойко", "Плавання", "МС", [90.2]),
    ("Максим Бондар", "Легка атлетика", "МС", [92.3]),
    ("Софія Ткачук", "Легка атлетика", "МСМК", [95.1]),
    ("Андрій Шевченко", "Бокс", "КМС", [81.0]),
    ("Тарас Новак", "Бокс", "МС", [88.6]),
]


def seed(session: Session) -> None:
    service = SportService(session)
    if service.list_sports():
        return
    for name, sport, category, scores in ATHLETES:
        athlete = service.create_athlete(
            AthleteCreate(name=name, sport=sport, category=category)
        )
        service.create_results(
            [
                ResultCreate(
                    athlete_id=athlete.id,
                    score=score,
                    competition_name="Кубок Львова",
                    competition_date=date(2026, 3, 14),
                )
                for score in scores
            ]
        )
