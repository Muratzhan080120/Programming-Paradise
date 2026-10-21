"""Точка входа в консольное приложение."""
from pathlib import Path

from .aggregators import MeanAggregator, MedianAggregator
from .models import Survey
from .service import export_question_stats, format_report, load_responses, create_report


def make_default_survey() -> Survey:
    return Survey(
        course_name="Парадигмы программирования",
        questions={
            1: "Насколько понятны объяснения преподавателя?",
            2: "Насколько логично организован материал?",
            3: "Насколько полезны практические задания?",
            4: "Насколько доступна обратная связь?",
            5: "Насколько равномерно распределена учебная нагрузка?",
        },
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "responses.csv"
    survey = make_default_survey()
    responses = load_responses(str(data_path), survey)

    while True:
        print("\nСИСТЕМА ОЦЕНКИ КАЧЕСТВА ДИСЦИПЛИНЫ")
        print("1. Отчёт по среднему арифметическому")
        print("2. Отчёт по медиане")
        print("3. Сравнить оба агрегатора")
        print("4. Экспортировать статистику в CSV")
        print("0. Выход")
        choice = input("Выберите действие: ").strip()

        if choice == "0":
            print("Работа завершена.")
            break
        if choice == "1":
            print(format_report(create_report(survey, responses, MeanAggregator())))
        elif choice == "2":
            print(format_report(create_report(survey, responses, MedianAggregator())))
        elif choice == "3":
            mean_report = create_report(survey, responses, MeanAggregator())
            median_report = create_report(survey, responses, MedianAggregator())
            print("СРАВНЕНИЕ АГРЕГАТОРОВ")
            print(f"Среднее: {mean_report.overall_mean:.2f}/5")
            print(f"Медиана: {median_report.overall_mean:.2f}/5")
            print("Среднее учитывает величину всех оценок; медиана устойчивее к крайним значениям.")
        elif choice == "4":
            report = create_report(survey, responses, MeanAggregator())
            output = root / "data" / "question_stats.csv"
            export_question_stats(report, str(output))
            print(f"Файл сохранён: {output}")
        else:
            print("Неизвестная команда. Выберите пункт меню от 0 до 4.")


if __name__ == "__main__":
    main()
