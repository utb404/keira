#!/usr/bin/env python3
"""
Пример пакетной генерации тестов.

Этот пример демонстрирует генерацию нескольких тестов одновременно.
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта библиотеки
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_generator import TestGenerator
from test_generator.models import GenerationConfig


def main():
    """Пример пакетной генерации."""
    print("🚀 Пример пакетной генерации тестов")
    print()

    # Инициализация генератора
    generator = TestGenerator(config_path="config.yaml")

    # Список тест-кейсов для генерации
    test_cases = [
        "test_case.json",
        # Добавьте другие тест-кейсы:
        # "test_case_2.json",
        # "test_case_3.json",
    ]

    print(f"📋 Генерация {len(test_cases)} тест-кейсов...")
    print()

    # Пакетная генерация
    results = generator.generate_tests_batch(
        test_cases=test_cases,
        generation_config=GenerationConfig(
            quality_level="balanced",
            use_cdp=False,
        ),
        parallel=False,  # Параллельная генерация (если поддерживается)
    )

    # Статистика
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    print()
    print("📊 Результаты пакетной генерации:")
    print(f"   ✅ Успешно: {successful}/{len(results)}")
    print(f"   ❌ Ошибки: {failed}/{len(results)}")
    print()

    # Детальная информация
    for i, result in enumerate(results, 1):
        status = "✅" if result.success else "❌"
        print(f"{status} Тест-кейс {i}: {result.test_case_id}")
        if result.success:
            print(f"      Файлов: {len(result.generated_files)}, "
                  f"Время: {result.generation_time_ms:.2f}мс")
        else:
            print(f"      Ошибки: {len(result.errors)}")


if __name__ == "__main__":
    main()

