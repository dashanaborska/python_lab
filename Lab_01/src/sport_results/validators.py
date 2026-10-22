from sport_results.config import CATEGORIES, MAX_RESULT, MIN_RESULT
from sport_results.exceptions import ValidationError


def validate_text(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"Поле '{field}' не може бути порожнім.")
    if any(char.isdigit() for char in cleaned):
        raise ValidationError(f"Поле '{field}' не повинно містити цифр.")
    return cleaned


def validate_result(value: str) -> float:
    try:
        result = float(value.strip().replace(",", "."))
    except ValueError as error:
        raise ValidationError(f"Результат '{value}' не є числом.") from error
    if not MIN_RESULT <= result <= MAX_RESULT:
        raise ValidationError(
            f"Результат має бути в діапазоні [{MIN_RESULT}; {MAX_RESULT}]."
        )
    return result


def validate_category(value: str) -> str:
    cleaned = value.strip()
    for category in CATEGORIES:
        if category.lower() == cleaned.lower():
            return category
    raise ValidationError(
        f"Невідома категорія '{cleaned}'. Допустимі: {', '.join(CATEGORIES)}."
    )
