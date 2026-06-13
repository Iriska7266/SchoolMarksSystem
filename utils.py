"""Вспомогательные функции."""

from datetime import datetime, date
from typing import Any


def validate_full_name(name: str) -> bool:
    """Проверяет, что ФИО состоит из 3 частей."""
    parts = name.strip().split()
    return len(parts) == 3


def validate_gender(gender: str) -> bool:
    """Проверяет корректность пола."""
    return gender.lower() in ("m", "f")


def validate_mark(value: int) -> bool:
    """Проверяет корректность оценки (2-5)."""
    return 2 <= value <= 5


ASSESSMENT_FORMS = [
    "homework", "classwork", "word_dictation",
    "independent_work", "dictation", "medium_test",
    "report", "abstract", "final_test",
]

ASSESSMENT_FORMS_RU = {
    "homework": "Домашняя работа",
    "classwork": "Классная работа",
    "word_dictation": "Словарный диктант",
    "independent_work": "Самостоятельная работа",
    "dictation": "Диктант",
    "medium_test": "Промежуточный тест",
    "report": "Доклад",
    "abstract": "Реферат",
    "final_test": "Итоговый тест",
}


def validate_assessment_form(form: str) -> bool:
    """Проверяет форму контроля."""
    return form in ASSESSMENT_FORMS


def calculate_age(birth_date: date) -> int:
    """Вычисляет возраст."""
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def is_adult(birth_date: date) -> bool:
    """Проверяет совершеннолетие (>= 18 лет)."""
    return calculate_age(birth_date) >= 18


def format_date(dt: datetime | date | None) -> str:
    """Форматирует дату в строку."""
    if dt is None:
        return "—"
    if isinstance(dt, datetime):
        return dt.strftime("%d.%m.%Y %H:%M")
    return dt.strftime("%d.%m.%Y")


def format_gender(g: str) -> str:
    """Переводит пол в читаемый вид."""
    return "Мужской" if g.lower() == "m" else "Женский"


def get_role_display(role: str) -> str:
    """Отображает роль на русском."""
    roles = {
        "headteacher": "Завуч",
        "teacher": "Учитель",
        "pupil": "Ученик",
        "parent": "Родитель",
    }
    return roles.get(role, role)
