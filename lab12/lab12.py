import argparse
import asyncio
import time
from dataclasses import dataclass
from typing import Any


# Имитация базы данных университета.
STUDENT_DATABASE: dict[int, dict[str, Any]] = {
    1001: {"name": "Алия Садыкова", "group": "ИС-23-1", "gpa": 3.7},
    1002: {"name": "Дамир Нурланов", "group": "ИС-23-2", "gpa": 3.2},
    1003: {"name": "Мадина Ермекова", "group": "ИС-23-1", "gpa": 3.9},
    1004: {"name": "Руслан Алиев", "group": "ИС-23-3", "gpa": 2.8},
}

# Для демонстрации тайм-аута: запрос к этому ID выполняется слишком долго.
STUDENT_DELAYS: dict[int, float] = {1003: 1.0}

SENTINEL = object()


class StudentNotFoundError(Exception):
    """Карточка студента отсутствует в базе данных."""


@dataclass
class PipelineReport:
    cards: list[dict[str, Any]]
    errors: list[str]
    cache_hits: int
    unavailable_count: int
    elapsed: float


class StudentCardService:
    """Имитирует асинхронный сервис получения карточек студентов."""

    def __init__(
        self,
        database: dict[int, dict[str, Any]] | None = None,
        delays: dict[int, float] | None = None,
        timeout_seconds: float = 0.4,
    ) -> None:
        self.database = database if database is not None else STUDENT_DATABASE
        self.delays = delays if delays is not None else STUDENT_DELAYS
        self.timeout_seconds = timeout_seconds
        self.cache: dict[int, dict[str, Any]] = {}
        self.cache_lock = asyncio.Lock()
        self.key_locks: dict[int, asyncio.Lock] = {}
        self.cache_hits = 0
        self.requests_to_service = 0

    async def _request_from_service(self, student_id: int) -> dict[str, Any]:
        """Имитация сетевого запроса к серверу университета."""
        self.requests_to_service += 1
        await asyncio.sleep(self.delays.get(student_id, 0.15))

        if student_id not in self.database:
            raise StudentNotFoundError(
                f"Студент с ID {student_id} не найден"
            )

        return {"student_id": student_id, **self.database[student_id]}

    async def get_card(self, student_id: int) -> dict[str, Any]:
        """Получает карточку с кешированием и ограничением времени запроса."""
        async with self.cache_lock:
            cached_card = self.cache.get(student_id)
            if cached_card is not None:
                self.cache_hits += 1
                return cached_card.copy()

            key_lock = self.key_locks.setdefault(student_id, asyncio.Lock())

        # Блокировка по ID не позволяет двум worker одновременно
        # отправлять одинаковый запрос, если карточки ещё нет в кеше.
        async with key_lock:
            async with self.cache_lock:
                cached_card = self.cache.get(student_id)
                if cached_card is not None:
                    self.cache_hits += 1
                    return cached_card.copy()

            try:
                async with asyncio.timeout(self.timeout_seconds):
                    card = await self._request_from_service(student_id)
            except TimeoutError:
                raise TimeoutError(
                    f"Истекло время ожидания карточки ID {student_id}"
                ) from None

            async with self.cache_lock:
                self.cache[student_id] = card.copy()

            return card
