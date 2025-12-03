#!/usr/bin/env python3
"""
Пример скрипта для генерации автотеста из тест-кейса.

Использование:
    python generate_test.py [--use-cdp] [--config CONFIG_PATH] [--test-case TEST_CASE_PATH]
"""

import argparse
import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта библиотеки
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_generator import TestGenerator
from test_generator.models import GenerationConfig, QualityLevel, CodeStyle


def main():
    """Основная функция генерации теста."""
    parser = argparse.ArgumentParser(
        description="Генерация автотеста из тест-кейса с использованием LLM"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Путь к конфигурационному файлу (по умолчанию: config.yaml)",
    )
    parser.add_argument(
        "--test-case",
        type=str,
        default="test_case.json",
        help="Путь к файлу тест-кейса (по умолчанию: test_case.json)",
    )
    parser.add_argument(
        "--use-cdp",
        action="store_true",
        help="Использовать CDP для определения селекторов",
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["fast", "balanced", "high"],
        default="balanced",
        help="Уровень качества генерации (по умолчанию: balanced)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Путь для сохранения результатов (по умолчанию: из конфигурации)",
    )

    args = parser.parse_args()

    # Проверка существования файлов
    config_path = Path(args.config)
    test_case_path = Path(args.test_case)

    if not config_path.exists():
        print(f"❌ Ошибка: Файл конфигурации не найден: {config_path}")
        return 1

    if not test_case_path.exists():
        print(f"❌ Ошибка: Файл тест-кейса не найден: {test_case_path}")
        return 1

    print("🚀 Запуск генерации автотеста...")
    print(f"   Конфигурация: {config_path}")
    print(f"   Тест-кейс: {test_case_path}")
    print(f"   CDP: {'включен' if args.use_cdp else 'выключен'}")
    print(f"   Качество: {args.quality}")
    print()

    try:
        # Инициализация генератора
        print("📦 Инициализация генератора...")
        generator = TestGenerator(config_path=str(config_path))

        # Проверка и индексация репозитория, если нужно
        repo_context = generator.repository_context
        if repo_context and repo_context.auto_index:
            print("📚 Проверка индекса репозитория...")
            if not generator.is_repository_indexed():
                print("🔍 Индекс не найден. Начинаю индексацию репозитория...")
                try:
                    index = generator.index_repository(force=False)
                    print(f"✅ Индексация завершена:")
                    print(f"   - Файлов проиндексировано: {index.total_files}")
                    print(f"   - Тестовых файлов: {index.test_files_count}")
                    print(f"   - Page Objects: {index.page_object_files_count}")
                    print()
                except Exception as e:
                    print(f"⚠️  Предупреждение: Не удалось проиндексировать репозиторий: {e}")
                    print("   Продолжаю генерацию без индекса репозитория...")
                    print()
            else:
                print("✅ Индекс репозитория найден и загружен")
                print()

        # Настройка конфигурации генерации
        generation_config = GenerationConfig(
            quality_level=QualityLevel(args.quality),
            code_style=CodeStyle.STANDARD,
            use_cdp=args.use_cdp,
            validate_code=True,
            format_code=True,
        )

        # Генерация теста
        print("⚙️  Генерация теста...")
        result = generator.generate_test(
            test_case=str(test_case_path),
            output_path=args.output,
            generation_config=generation_config,
        )

        # Вывод результатов
        print()
        if result.success:
            print("✅ Генерация завершена успешно!")
            print()
            print(f"📁 Файлов сгенерировано: {len(result.generated_files)}")
            print(f"⏱️  Время генерации: {result.generation_time_ms:.2f} мс")
            print(f"🎯 Использовано токенов: {result.total_tokens_used}")
            print(f"🔄 Запросов к LLM: {len(result.llm_requests)}")
            print()

            print("📄 Сгенерированные файлы:")
            for file in result.generated_files:
                print(f"   - {file.path} ({file.file_type}, {file.size_bytes} байт)")

            if result.output_directory:
                print()
                print(f"💾 Результаты сохранены в: {result.output_directory}")

            # Валидация
            if result.validation_report:
                print()
                print("🔍 Результаты валидации:")
                report = result.validation_report
                if report.valid:
                    print("   ✅ Код валиден")
                else:
                    print(f"   ⚠️  Найдено ошибок: {len(report.errors)}")
                    print(f"   ⚠️  Найдено предупреждений: {len(report.warnings)}")
                    for error in report.errors[:5]:  # Показываем первые 5 ошибок
                        print(f"      - {error.message}")

            # Предупреждения
            if result.warnings:
                print()
                print("⚠️  Предупреждения:")
                for warning in result.warnings:
                    print(f"   - {warning}")

            return 0

        else:
            print("❌ Генерация завершилась с ошибками!")
            print()
            print("Ошибки:")
            for error in result.errors:
                print(f"   - {error}")

            if result.warnings:
                print()
                print("Предупреждения:")
                for warning in result.warnings:
                    print(f"   - {warning}")

            return 1

    except KeyboardInterrupt:
        print()
        print("⚠️  Генерация прервана пользователем")
        return 130

    except Exception as e:
        print()
        print(f"❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

