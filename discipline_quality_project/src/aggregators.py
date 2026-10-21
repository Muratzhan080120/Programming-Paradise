"""Стратегии агрегирования оценок: среднее и медиана."""
from abc import ABC, abstractmethod
from statistics import median
from typing import Iterable, List


class Aggregator(ABC):
    """Общий интерфейс взаимозаменяемых агрегаторов."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Название стратегии."""

    @abstractmethod
    def aggregate(self, values: Iterable[int]) -> float:
        """Возвращает одно число по набору оценок."""


class MeanAggregator(Aggregator):
    @property
    def name(self) -> str:
        return "Среднее арифметическое"

    def aggregate(self, values: Iterable[int]) -> float:
        numbers = list(values)
        if not numbers:
            raise ValueError("Нельзя вычислить среднее для пустого набора")
        return sum(numbers) / len(numbers)


class MedianAggregator(Aggregator):
    @property
    def name(self) -> str:
        return "Медиана"

    def aggregate(self, values: Iterable[int]) -> float:
        numbers = list(values)
        if not numbers:
            raise ValueError("Нельзя вычислить медиану для пустого набора")
        return float(median(numbers))
