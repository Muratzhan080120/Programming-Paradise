import tempfile
import unittest
from pathlib import Path

from src.aggregators import MeanAggregator, MedianAggregator
from src.logic import (
    build_report, filter_complete_responses, is_complete, select_problem_questions,
    validate_rating, validate_response, recursive_count, make_threshold_filter,
)
from src.main import make_default_survey
from src.models import Response, Survey
from src.service import load_responses, format_report


class QualitySurveyTests(unittest.TestCase):
    def setUp(self):
        self.survey = Survey("Тестовая дисциплина", {1: "Понятность", 2: "Практика"})
        self.responses = [
            Response("anon-1", {1: 5, 2: 4}),
            Response("anon-2", {1: 2, 2: 2}),
            Response("anon-3", {1: 4, 2: 5}),
            Response("anon-4", {1: 3, 2: None}),
        ]

    def test_valid_rating_range(self):
        self.assertTrue(validate_rating(1))
        self.assertTrue(validate_rating(5))
        self.assertTrue(validate_rating(None))

    def test_invalid_rating_zero(self):
        self.assertFalse(validate_rating(0))

    def test_invalid_rating_six(self):
        self.assertFalse(validate_rating(6))

    def test_invalid_float_rating(self):
        self.assertFalse(validate_rating(3.5))

    def test_response_with_missing_question_field(self):
        response = Response("x", {1: 4})
        self.assertTrue(validate_response(response, self.survey))

    def test_complete_response(self):
        self.assertTrue(is_complete(self.responses[0], self.survey))

    def test_incomplete_response(self):
        self.assertFalse(is_complete(self.responses[3], self.survey))

    def test_filter_complete_responses(self):
        result = filter_complete_responses(self.responses, self.survey)
        self.assertEqual(len(result), 3)

    def test_mean_aggregator(self):
        self.assertEqual(MeanAggregator().aggregate([1, 3, 5]), 3)

    def test_median_aggregator_even_count(self):
        self.assertEqual(MedianAggregator().aggregate([1, 2, 5, 5]), 3.5)

    def test_empty_mean_raises(self):
        with self.assertRaises(ValueError):
            MeanAggregator().aggregate([])

    def test_empty_median_raises(self):
        with self.assertRaises(ValueError):
            MedianAggregator().aggregate([])

    def test_problem_question_threshold(self):
        report = build_report(self.survey, self.responses, MeanAggregator(), 0.3)
        self.assertTrue(any(item.question_id == 1 for item in report.problem_questions))

    def test_threshold_out_of_range(self):
        with self.assertRaises(ValueError):
            select_problem_questions([], 1.5)

    def test_recursive_count(self):
        self.assertEqual(recursive_count([1, 2, 3]), 3)
        self.assertEqual(recursive_count([]), 0)

    def test_higher_order_filter(self):
        predicate = make_threshold_filter(0.5)
        report = build_report(self.survey, self.responses, MeanAggregator(), 0.5)
        self.assertTrue(all(predicate(item) for item in report.problem_questions))

    def test_report_has_course_name(self):
        report = build_report(self.survey, self.responses, MeanAggregator())
        self.assertEqual(report.course_name, "Тестовая дисциплина")

    def test_report_counts_incomplete(self):
        report = build_report(self.survey, self.responses, MeanAggregator())
        self.assertEqual(report.submitted_responses, 4)
        self.assertEqual(report.complete_responses, 3)
        self.assertEqual(report.incomplete_responses, 1)

    def test_format_report_contains_summary(self):
        report = build_report(self.survey, self.responses, MeanAggregator())
        formatted = format_report(report)
        self.assertIn("СТАТИСТИКА ПО ВОПРОСАМ", formatted)
        self.assertIn("Общая оценка", formatted)

    def test_survey_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Survey(" ", {1: "Вопрос"})

    def test_survey_rejects_empty_questions(self):
        with self.assertRaises(ValueError):
            Survey("Курс", {})

    def test_csv_loader(self):
        content = "respondent_id,q1,q2\nanon-1,5,4\nanon-2,3,\n"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "responses.csv"
            path.write_text(content, encoding="utf-8")
            survey = Survey("Курс", {1: "Q1", 2: "Q2"})
            loaded = load_responses(str(path), survey)
            self.assertEqual(len(loaded), 2)
            self.assertIsNone(loaded[1].ratings[2])

    def test_default_survey_has_five_questions(self):
        self.assertEqual(len(make_default_survey().questions), 5)


if __name__ == "__main__":
    unittest.main()
