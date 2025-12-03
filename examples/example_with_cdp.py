#!/usr/bin/env python3
"""
Пример использования библиотеки с CDP для определения селекторов.

Этот пример демонстрирует:
1. Использование CDP для автоматического определения селекторов
2. Генерацию теста с точными селекторами элементов
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта библиотеки
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_generator import TestGenerator
from test_generator.models import GenerationConfig


def main():
    """Пример использования с CDP."""
    print("🚀 Пример использования Test Generator с CDP")
    print()

    # Инициализация генератора
    generator = TestGenerator(config_path="config.yaml")

    # Генерация теста с использованием CDP
    print("⚙️  Генерация теста с использованием CDP для определения селекторов...")
    print("   (CDP автоматически извлечет селекторы из описания шагов)")
    print()

    result = generator.generate_test(
        test_case="test_case.json",
        generation_config=GenerationConfig(
            use_cdp=True,  # Включить CDP
            quality_level="high",
        ),
    )

    if result.success:
        print("✅ Генерация завершена успешно!")
        print()
        print(f"📁 Файлов сгенерировано: {len(result.generated_files)}")
        print(f"⏱️  Время генерации: {result.generation_time_ms:.2f} мс")
        print()

        # Показываем информацию о CDP селекторах, если они были использованы
        if result.metadata.get("cdp_selectors"):
            print("🎯 Селекторы, определенные через CDP:")
            for step_id, selector_info in result.metadata["cdp_selectors"].items():
                print(f"   {step_id}: {selector_info.get('selector')} ({selector_info.get('strategy')})")
    else:
        print("❌ Ошибки генерации:")
        for error in result.errors:
            print(f"   - {error}")


if __name__ == "__main__":
    main()

