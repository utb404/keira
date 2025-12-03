# Модуль CDP интеграции

Модуль для работы с Chrome DevTools Protocol (CDP) для автоматического определения селекторов и анализа элементов страницы.

## Компоненты

### CDPClient
Клиент для подключения к браузеру через CDP.

```python
from test_generator.cdp import CDPClient

with CDPClient(browser_type="chromium", headless=True) as client:
    client.navigate("https://example.com")
    
    # Получение DOM снимка
    dom_snapshot = client.get_dom_snapshot()
    
    # Поиск элемента
    element_info = client.query_selector("button#submit")
```

### SelectorExtractor
Извлечение оптимальных селекторов для элементов.

```python
from test_generator.cdp import CDPClient, SelectorExtractor

with CDPClient() as client:
    client.navigate("https://example.com")
    
    extractor = SelectorExtractor(client)
    
    # Извлечение селекторов по описанию
    selectors = extractor.extract_selectors("кнопка отправки формы")
    
    # Валидация селектора
    validation = extractor.validate_selector("button#submit")
```

### ElementAnalyzer
Анализ элементов страницы.

```python
from test_generator.cdp import CDPClient, ElementAnalyzer

with CDPClient() as client:
    client.navigate("https://example.com")
    
    analyzer = ElementAnalyzer(client)
    
    # Анализ элемента
    element_info = analyzer.analyze_element("button#submit")
    
    # Анализ структуры страницы
    page_structure = analyzer.analyze_page_structure()
    
    # Поиск интерактивных элементов
    interactive = analyzer.find_interactive_elements()
```

## Использование в генерации тестов

CDP автоматически используется при генерации, если в конфигурации включено `use_cdp: true`:

```python
from test_generator import TestGenerator
from test_generator.models import GenerationConfig

generator = TestGenerator(config_path="config.yaml")

result = generator.generate_test(
    test_case="test_case.json",
    generation_config=GenerationConfig(use_cdp=True)
)
```

## Конфигурация

В `config.yaml`:

```yaml
cdp:
  enabled: true
  browser: "chromium"  # chromium, firefox, webkit
  headless: true
```

## Принцип работы

1. **Извлечение URL**: CDP извлекает URL из тест-кейса (из описания или шагов)
2. **Навигация**: Переход на указанную страницу
3. **Анализ шагов**: Для каждого шага тест-кейса извлекаются селекторы элементов
4. **Генерация селекторов**: Создаются различные варианты селекторов с приоритетами:
   - ID селекторы (высокий приоритет)
   - Name селекторы
   - ARIA атрибуты
   - Class селекторы
   - Текстовые селекторы
   - XPath (низкий приоритет)
5. **Валидация**: Проверка работоспособности селекторов
6. **Интеграция**: Найденные селекторы передаются в промпт для LLM

## Поддерживаемые стратегии селекторов

- `by_id` - по ID элемента
- `by_name` - по атрибуту name
- `by_class` - по классу
- `by_text` - по тексту элемента
- `by_role` - по ARIA роли
- `by_aria_label` - по aria-label
- `by_css` - CSS селектор
- `by_xpath` - XPath селектор

## Требования

- Playwright установлен и браузеры скачаны:
  ```bash
  pip install playwright
  playwright install chromium
  ```

