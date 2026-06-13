"""Подключение к базе данных PostgreSQL через SQLAlchemy + pg8000.

pg8000 используется вместо psycopg2-binary, так как libpq из psycopg2
не может декодировать кириллические сообщения об ошибках PostgreSQL
на старых версиях/конфигурациях сервера.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

Base = declarative_base()


class DatabaseManager:
    """Менеджер подключения к БД (синглтон)."""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection_string(self) -> str:
        """Формирует строку подключения из переменных окружения или значений по умолчанию."""
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "school_marks")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        # pg8000 — чистый Python драйвер, корректно работает с любой кодировкой
        return f"postgresql+pg8000://{user}:{password}@{host}:{port}/{dbname}"

    def connect(self, connection_string: str | None = None):
        """Инициализирует подключение к БД."""
        conn_str = connection_string or self.get_connection_string()
        self._engine = create_engine(conn_str, pool_pre_ping=True)
        self._session_factory = scoped_session(
            sessionmaker(bind=self._engine, autoflush=False)
        )

    @property
    def engine(self):
        if self._engine is None:
            self.connect()
        return self._engine

    @property
    def session_factory(self):
        if self._session_factory is None:
            self.connect()
        return self._session_factory

    def create_session(self):
        """Создаёт новую сессию."""
        return self.session_factory()

    def close(self):
        """Закрывает соединение."""
        if self._session_factory is not None:
            self._session_factory.remove()
        if self._engine is not None:
            self._engine.dispose()


db_manager = DatabaseManager()


def get_db():
    """Глобальная точка доступа к сессии БД."""
    return db_manager.create_session()
