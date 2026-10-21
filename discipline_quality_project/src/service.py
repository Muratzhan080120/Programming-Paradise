"""Сервисный слой: загрузка данных и вывод отчёта."""
import csv
from pathlib import Path
from typing import List

from .aggregators import Aggregator, MeanAggregator
from .logic import build_report, validate_response
from .models import Response, Survey, SurveyReport


def load_responses(path: str, survey: Survey) -> List[Response]:
    """Загружает CSV. Пустая ячейка становится None."""
    responses = []
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        expected = {"respondent_id", *(f"q{qid}" for qid in survey.questions)}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise ValueError("CSV не содержит обязательные столбцы")
        for row in reader:
            ratings = {}
            for qid in survey.questions:
                raw = (row.get(f"q{qid}") or "").strip()
                ratings[qid] = None if raw == "" else int(raw)
            response = Response(row["respondent_id"], ratings)
            errors = validate_response(response, survey)
            if errors:
                raise ValueError(f"Некорректная строка {reader.line_num}: {'; '.join(errors)}")
            responses.append(response)
    return responses


def create_report(
    survey: Survey, responses: List[Response], aggregator: Aggregator = None,
    problem_threshold: float = 0.35
) -> SurveyReport:
    """Фасад над логикой аналитики; стратегию можно заменить."""
    selected_aggregator = aggregator or MeanAggregator()
    return build_report(survey, responses, selected_aggregator, problem_threshold)


def format_report(report: SurveyReport) -> str:
    """Преобразует отчёт в читаемый консольный текст."""
    overall = "нет данных" if report.overall_mean is None else f"{report.overall_mean:.2f}/5"
    lines = [
        "=" * 62,
        f"ОЦЕНКА КАЧЕСТВА ДИСЦИПЛИНЫ: {report.course_name}",
        "=" * 62,
        f"Получено анкет: {report.submitted_responses}",
        f"Полных анкет: {report.complete_responses}",
        f"Неполных анкет: {report.incomplete_responses}",
        f"Общая оценка: {overall}",
        f"Агрегатор: {report.aggregator_name}",
        "",
        "СТАТИСТИКА ПО ВОПРОСАМ",
    ]
    for item in report.question_stats:
        score = "нет данных" if item.mean is None else f"{item.mean:.2f}"
        median = "нет данных" if item.median is None else f"{item.median:.2f}"
        lines.append(
            f"{item.question_id}. {item.question_text} | n={item.count} "
            f"| оценка={score} | медиана={median} "
            f"| низкие оценки={item.low_rating_share:.0%}"
        )
    lines.append("")
    lines.append("ВОПРОСЫ, ТРЕБУЮЩИЕ ВНИМАНИЯ")
    if not report.problem_questions:
        lines.append("По заданному порогу проблемные вопросы не выявлены.")
    else:
        for item in report.problem_questions:
            lines.append(f"- {item.question_text} ({item.low_rating_share:.0%} оценок 1–2)")
    return "\n".join(lines)


def export_question_stats(report: SurveyReport, path: str) -> None:
    """Экспортирует сводную статистику в CSV."""
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["question_id", "question", "count", "score", "median", "low_rating_share"])
        for item in report.question_stats:
            writer.writerow([
                item.question_id, item.question_text, item.count, item.mean,
                item.median, item.low_rating_share
            ])
