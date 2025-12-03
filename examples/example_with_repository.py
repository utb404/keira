#!/usr/bin/env python3
"""
Пример использования библиотеки с индексацией репозитория.

Этот пример демонстрирует:
1. Индексацию репозитория для извлечения паттернов
2. Генерацию теста с учетом паттернов из репозитория
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта библиотеки
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_generator import TestGenerator
from test_generator.models import GenerationConfig, RepositoryContext


def main():
    """Пример использования с индексацией репозитория."""
    print("🚀 Пример использования Test Generator с индексацией репозитория")
    print()

    # Инициализация генератора
    generator = TestGenerator(config_path="config.yaml")

    # Пример: индексация репозитория (раскомментируйте и укажите URL)
    # repository_url = "https://gitlab.example.com/project/repo.git"
    # print(f"📦 Индексация репозитория: {repository_url}")
    # 
    # context = RepositoryContext(
    #     repository_url=repository_url,
    #     auth_type="token",
    #     auth_token=os.getenv("GITLAB_TOKEN"),
    #     index_path=Path("./.test_generator/index.json"),
    # )
    # 
    # index = generator.index_repository(
    #     repository_url=repository_url,
    #     force=False
    # )
    # 
    # print(f"✅ Индексация завершена:")
    # print(f"   - Файлов проиндексировано: {index.total_files}")
    # print(f"   - Тестовых файлов: {index.test_files_count}")
    # print(f"   - Page Objects: {index.page_object_files_count}")
    # print()

    # Генерация теста
    print("⚙️  Генерация теста с учетом паттернов репозитория...")
    result = generator.generate_test(
        test_case="test_case.json",
        generation_config=GenerationConfig(
            quality_level="high",
            use_cdp=False,
        ),
    )

    if result.success:
        print("✅ Генерация завершена успешно!")
        print(f"📁 Файлов: {len(result.generated_files)}")
    else:
        print("❌ Ошибки генерации:")
        for error in result.errors:
            print(f"   - {error}")


if __name__ == "__main__":
    main()

