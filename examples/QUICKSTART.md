# Быстрый старт - Пример использования Test Generator

## Шаг 1: Подготовка окружения

```bash
# Установка зависимостей
pip install -r ../requirements.txt

# Установка Playwright (для CDP, опционально)
playwright install chromium

# Запуск Ollama (если локально)
ollama serve
```

## Шаг 2: Настройка конфигурации

Отредактируйте `config.yaml`:
- Укажите URL Ollama сервера (если не локальный)
- Выберите модель LLM
- Настройте пути для сохранения

## Шаг 3: Запуск генерации

### Базовый запуск

```bash
python generate_test.py
```

### С использованием CDP

```bash
python generate_test.py --use-cdp --test-case test_case_with_url.json
```

### С настройками качества

```bash
python generate_test.py --quality high
```

## Шаг 4: Проверка результатов

После успешной генерации:

```bash
# Просмотр сгенерированных файлов
ls -la generated_tests/

# Запуск тестов (если pytest установлен)
cd generated_tests
pytest tests/ -v
```

## Ожидаемый результат

После генерации будут созданы:

```
generated_tests/
├── pages/
│   ├── __init__.py
│   └── installation_page.py      # Page Object для страницы Installation
└── tests/
    ├── __init__.py
    └── test_playwright_intro_001.py  # Тестовый файл
```

## Устранение проблем

### Ollama недоступен

Убедитесь, что Ollama запущен:
```bash
ollama serve
```

Проверьте доступность:
```bash
curl http://localhost:11434/api/tags
```

### Модель не найдена

Скачайте модель:
```bash
ollama pull codellama:13b
```

### Ошибки генерации

Проверьте логи в `test_generator.log` или вывод консоли для деталей ошибок.

