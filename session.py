"""Локальное сохранение учётных данных для автоподстановки."""

import json
import os

_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), ".login_credentials.json")


def save_credentials(login: str, password: str) -> None:
    """Сохраняет логин и пароль в локальный JSON-файл."""
    try:
        with open(_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump({"login": login, "password": password}, f)
    except OSError:
        pass


def load_credentials() -> tuple[str, str] | None:
    """Загружает сохранённые логин и пароль. Возвращает None, если файла нет."""
    try:
        with open(_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("login", ""), data.get("password", "")
    except (OSError, json.JSONDecodeError):
        return None


def clear_credentials() -> None:
    """Удаляет сохранённые учётные данные."""
    try:
        if os.path.exists(_CREDENTIALS_FILE):
            os.remove(_CREDENTIALS_FILE)
    except OSError:
        pass


def credentials_exist() -> bool:
    """Проверяет, есть ли сохранённые учётные данные."""
    return os.path.exists(_CREDENTIALS_FILE)
