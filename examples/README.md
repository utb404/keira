# Примеры использования Test Generator

Данная директория содержит примеры использования библиотеки для генерации автотестов.

## Структура

```
examples/
├── README.md              # Этот файл
├── config.yaml            # Конфигурация библиотеки
├── test_case.json         # Входной тест-кейс
├── generate_test.py       # Скрипт генерации теста
└── generated_tests/       # Сгенерированные тесты (создается автоматически)
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r ../requirements.txt
playwright install chromium
```

### 2. Настройка конфигурации

Отредактируйте `config.yaml` при необходимости:
- URL Ollama сервера
- Модель LLM
- Пути для сохранения результатов

### 3. Запуск генерации

Базовый запуск:
```bash
python generate_test.py
```

С использованием CDP (требует URL в тест-кейсе):
```bash
python generate_test.py --use-cdp --test-case test_case_with_url.json
```

С настройкой качества:
```bash
python generate_test.py --quality high
```

С указанием выходной директории:
```bash
python generate_test.py --output ./my_tests
```

## Примеры использования

### Базовый пример

```python
from test_generator import TestGenerator

generator = TestGenerator(config_path="config.yaml")
result = generator.generate_test("test_case.json")

if result.success:
    print(f"Успешно сгенерировано {len(result.generated_files)} файлов")
else:
    print(f"Ошибки: {result.errors}")
```

### С использованием CDP

```python
from test_generator import TestGenerator
from test_generator.models import GenerationConfig

generator = TestGenerator(config_path="config.yaml")
result = generator.generate_test(
    test_case="test_case.json",
    generation_config=GenerationConfig(use_cdp=True)
)
```

### С индексацией репозитория

```python
from test_generator import TestGenerator

generator = TestGenerator(config_path="config.yaml")

# Индексация репозитория
index = generator.index_repository(
    repository_url="https://gitlab.example.com/project/repo.git"
)

# Генерация с учетом паттернов репозитория
result = generator.generate_test("test_case.json")
```

## Результаты

После генерации в директории `generated_tests/` будут созданы:

- `pages/` - Page Object классы
- `tests/` - Тестовые файлы
- `conftest.py` - Фикстуры pytest

## Структура проекта

```
examples/
├── README.md                    # Документация примеров
├── config.yaml                  # Конфигурация библиотеки
├── test_case.json              # Входной тест-кейс (PLAYWRIGHT_INTRO_001)
├── generate_test.py             # Основной скрипт генерации
├── example_with_cdp.py         # Пример с CDP
├── example_with_repository.py  # Пример с индексацией репозитория
├── example_batch.py            # Пример пакетной генерации
└── generated_tests/            # Сгенерированные тесты (создается автоматически)
    ├── pages/
    │   └── *.py               # Page Object классы
    └── tests/
        └── *.py               # Тестовые файлы
```

## Примечания

- Убедитесь, что Ollama запущен и доступен по адресу из конфигурации
- Для использования CDP необходимо установить Playwright: `playwright install chromium`
- Сгенерированные файлы можно запускать с помощью pytest

