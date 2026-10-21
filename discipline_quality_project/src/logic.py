"""Чистые функции проверки, фильтрации и аналитики анкет."""
from functools import reduce
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .aggregators import Aggregator
from .models import QuestionStats, Response, Survey, SurveyReport


def validate_rating(value: Optional[int]) -> bool:
    """Проверяет, является ли оценка допустимым целым числом от 1 до 5."""
    return value is None or (type(value) is int and 1 <= value <= 5)


def validate_response(response: Response, survey: Survey) -> List[str]:
    """Возвращает список ошибок ответа; пустой список означает корректный ответ."""
    errors = []
    unknown = set(response.ratings) - set(survey.questions)
    missing = set(survey.questions) - set(response.ratings)
    if unknown:
        errors.append(f"Неизвестные вопросы: {sorted(unknown)}")
    if missing:
        errors.append(f"Нет полей для вопросов: {sorted(missing)}")
    for question_id, rating in response.ratings.items():
        if not validate_rating(rating):
            errors.append(f"Оценка вопроса {question_id} должна быть целым числом от 1 до 5")
    return errors


def is_complete(response: Response, survey: Survey) -> bool:
    """Анкета полная, если есть все вопросы, нет неизвестных и нет пропусков."""
    if validate_response(response, survey):
        return False
    return all(response.ratings[qid] is not None for qid in survey.questions)


def filter_complete_responses(
    responses: Sequence[Response], survey: Survey
) -> List[Response]:
    """Чистая функция: возвращает новые списки, не изменяя входные данные."""
    return [response for response in responses if is_complete(response, survey)]


def collect_question_values(
    responses: Sequence[Response], question_id: int
) -> List[int]:
    """Собирает допустимые числовые оценки заданного вопроса."""
    values = []
    for response in responses:
        value = response.ratings.get(question_id)
        if type(value) is int and 1 <= value <= 5:
            values.append(value)
    return values


def calculate_question_stats(
    survey: Survey, responses: Sequence[Response], aggregator: Aggregator
) -> List[QuestionStats]:
    """Создаёт статистику по каждому вопросу."""
    stats = []
    for question_id, question_text in survey.questions.items():
        values = collect_question_values(responses, question_id)
        if values:
            score = aggregator.aggregate(values)
            med = float(sorted(values)[len(values) // 2]) if len(values) % 2 else (
                sorted(values)[len(values) // 2 - 1] + sorted(values)[len(values) // 2]
            ) / 2
            low_share = sum(value <= 2 for value in values) / len(values)
        else:
            score, med, low_share = None, None, 0.0
        stats.append(QuestionStats(
            question_id=question_id,
            question_text=question_text,
            count=len(values),
            mean=score,
            median=med,
            low_rating_share=low_share,
        ))
    return stats


def calculate_overall_mean(responses: Sequence[Response], survey: Survey) -> Optional[float]:
    """Считает среднее по всем валидным оценкам, не меняя исходные анкеты."""
    values = []
    for response in responses:
        for question_id in survey.questions:
            value = response.ratings.get(question_id)
            if type(value) is int and 1 <= value <= 5:
                values.append(value)
    if not values:
        return None
    return sum(values) / len(values)


def select_problem_questions(
    stats: Sequence[QuestionStats], threshold: float = 0.35
) -> List[QuestionStats]:
    """Проблемным считается вопрос, где доля оценок 1–2 не ниже порога."""
    if not 0 <= threshold <= 1:
        raise ValueError("Порог должен находиться в диапазоне от 0 до 1")
    return [item for item in stats if item.count and item.low_rating_share >= threshold]


def recursive_count(items: Sequence[object]) -> int:
    """Небольшая демонстрация рекурсии для подсчёта элементов."""
    if not items:
        return 0
    return 1 + recursive_count(items[1:])


def make_threshold_filter(threshold: float):
    """Функция высшего порядка: возвращает фильтр по минимальному рейтингу."""
    if not 0 <= threshold <= 1:
        raise ValueError("Порог должен находиться в диапазоне от 0 до 1")
    return lambda stat: stat.count > 0 and stat.low_rating_share >= threshold


def build_report(
    survey: Survey,
    responses: Sequence[Response],
    aggregator: Aggregator,
    problem_threshold: float = 0.35,
) -> SurveyReport:
    """Основной функциональный конвейер формирования отчёта."""
    valid_responses = [r for r in responses if not validate_response(r, survey)]
    complete = filter_complete_responses(valid_responses, survey)
    stats = calculate_question_stats(survey, complete, aggregator)
    problem_filter = make_threshold_filter(problem_threshold)
    problems = list(filter(problem_filter, stats))
    return SurveyReport(
        course_name=survey.course_name,
        submitted_responses=len(responses),
        complete_responses=len(complete),
        incomplete_responses=len(responses) - len(complete),
        overall_mean=calculate_overall_mean(complete, survey),
        question_stats=stats,
        problem_questions=problems,
        aggregator_name=aggregator.name,
    )


def reduce_total(values: Iterable[int]) -> int:
    """Пример reduce: сумма числовых оценок."""
    return reduce(lambda total, value: total + value, values, 0)
