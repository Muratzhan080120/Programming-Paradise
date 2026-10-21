"""Предметные модели системы оценки качества дисциплины."""
from dataclasses import dataclass, field
from statistics import median
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Survey:
    """Анкета с набором оцениваемых вопросов."""
    course_name: str
    questions: Dict[int, str]

    def __post_init__(self):
        if not self.course_name.strip():
            raise ValueError("Название дисциплины не может быть пустым")
        if not self.questions:
            raise ValueError("Анкета должна содержать хотя бы один вопрос")
        if any(not text.strip() for text in self.questions.values()):
            raise ValueError("Текст вопроса не может быть пустым")


@dataclass(frozen=True)
class Response:
    """Анонимный ответ: respondent_id нужен только для проверки полноты."""
    respondent_id: str
    ratings: Dict[int, Optional[int]]

    def __post_init__(self):
        if not self.respondent_id.strip():
            raise ValueError("Идентификатор ответа не может быть пустым")


@dataclass(frozen=True)
class QuestionStats:
    question_id: int
    question_text: str
    count: int
    mean: Optional[float]
    median: Optional[float]
    low_rating_share: float


@dataclass(frozen=True)
class SurveyReport:
    course_name: str
    submitted_responses: int
    complete_responses: int
    incomplete_responses: int
    overall_mean: Optional[float]
    question_stats: List[QuestionStats]
    problem_questions: List[QuestionStats]
    aggregator_name: str
