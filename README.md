# Test Generator - Библиотека генерации автотестов UI с использованием LLM

Библиотека для автоматической генерации автотестов UI на основе тест-кейсов с применением технологий Large Language Models (LLM).

## Описание

Библиотека решает проблему трудоемкого процесса создания автотестов UI, автоматизируя генерацию кода тестов на основе структурированных тест-кейсов в формате JSON. Применение LLM позволяет создавать контекстуально правильные тесты, учитывающие структуру существующего проекта и корпоративные стандарты разработки.

## Основные возможности

- ✅ Генерация автотестов на основе JSON тест-кейсов
- ✅ Интеграция с Ollama для генерации кода через LLM
- ✅ Поддержка паттерна Page Object Model
- ✅ Интеграция с библиотекой qautils
- ✅ Генерация Allure декораторов
- ✅ Валидация и форматирование сгенерированного кода
- ✅ Гибкая конфигурация через YAML файлы

## Установка

```bash
pip install -r requirements.txt
playwright install chromium  # Для CDP интеграции (опционально)
```

## Быстрый старт

### Запуск примера

Перейдите в директорию `examples/` и запустите:

```bash
cd examples
python generate_test.py
```

Или с использованием CDP:

```bash
python generate_test.py --use-cdp
```

## Примеры использования

Полные примеры находятся в директории `examples/`:

- `generate_test.py` - основной скрипт генерации с CLI интерфейсом
- `example_with_cdp.py` - использование CDP для определения селекторов
- `example_with_repository.py` - индексация репозитория и использование паттернов
- `example_batch.py` - пакетная генерация нескольких тестов

### Пример 1: Базовое использование

```python
from test_generator import TestGenerator

# Инициализация генератора
generator = TestGenerator(config_path="config.yaml")

# Генерация теста из тест-кейса
result = generator.generate_test(
    test_case="test_case.json",
    output_path="./generated_tests"
)

# Проверка результата
if result.success:
    print(f"Успешно сгенерировано {len(result.generated_files)} файлов")
    for file in result.generated_files:
        print(f"  - {file.path}")
else:
    print("Ошибки генерации:")
    for error in result.errors:
        print(f"  - {error}")
```

### Пример 2: С дополнительным контекстом

```python
from test_generator import TestGenerator
from test_generator.models import GenerationConfig, QualityLevel

# Дополнительный контекст
additional_context = {
    "selectors": {
        "login_page": {
            "username": "input[name='username']",
            "password": "input[name='password']"
        }
    }
}

# Генерация с контекстом
result = generator.generate_test(
    test_case="test_case.json",
    additional_context=additional_context,
    generation_config=GenerationConfig(
        quality_level=QualityLevel.HIGH,
        use_cdp=True
    )
)
```

## Структура библиотеки

```
test_generator/
├── __init__.py
├── models.py                 # Модели данных
├── core/                     # Основная логика
│   ├── generator.py          # Главный генератор
│   └── config.py            # Конфигурация
├── parser/                   # Парсинг тест-кейсов
│   ├── json_parser.py
│   ├── validator.py
│   └── normalizer.py
├── llm/                      # Работа с LLM
│   ├── base.py
│   ├── ollama_provider.py
│   └── prompt_builder.py
├── code_generator/           # Генерация кода
│   ├── code_processor.py
│   └── formatter.py
├── output/                   # Управление выводом
│   ├── file_manager.py
│   └── directory_builder.py
└── utils/                    # Утилиты
    ├── exceptions.py
    └── logger.py
```

## Конфигурация

Пример файла `config.yaml`:

```yaml
# Настройки LLM
llm:
  provider: "ollama"
  ollama:
    url: "http://localhost:11434"
    model: "codellama:13b"
    temperature: 0.3
    max_tokens: 4000
    timeout: 300

# Настройки генерации
generation:
  output_path: "./generated_tests"
  overwrite_existing: false
  format_code: true
  validate_code: true
  quality_level: "balanced"
  code_style: "standard"

# Логирование
logging:
  level: "INFO"
  file: "./test_generator.log"
```

## Формат тест-кейса

Тест-кейс должен быть в формате JSON:

```json
{
  "id": "TEST_001",
  "name": "Тест логина",
  "description": "Проверка входа в систему",
  "expectedResult": "Пользователь успешно авторизован",
  "testLayer": "E2E",
  "epic": "Авторизация",
  "feature": "Логин",
  "story": "Вход в систему",
  "browser": "chromium",
  "steps": [
    {
      "id": "1",
      "name": "Открыть страницу логина",
      "description": "Перейти на страницу /login",
      "expectedResult": "Страница логина открыта"
    }
  ]
}
```

## Требования

- Python 3.9+
- Ollama (локально или удаленно)
- Модель LLM (например, codellama:13b)
- Playwright (для CDP интеграции, опционально)

## Быстрый старт с примерами

1. Перейдите в директорию examples:
   ```bash
   cd examples
   ```

2. Убедитесь, что Ollama запущен:
   ```bash
   ollama serve
   ```

3. Запустите генерацию:
   ```bash
   python generate_test.py
   ```

4. Для использования CDP:
   ```bash
   python generate_test.py --use-cdp
   ```

5. Результаты будут в директории `generated_tests/`

## Документация

Полная документация по архитектуре и API находится в файлах:
- `ARCHITECTURE.md` - архитектура системы
- `API_DESIGN.md` - описание API

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности см. в файле [LICENSE](LICENSE).

