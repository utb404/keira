# Модуль индексации репозитория

Модуль для индексации репозиториев с автотестами для извлечения паттернов и шаблонов.

## Компоненты

### RepositoryConnector
Управление подключением к репозиторию (GitLab/Git).

```python
from test_generator.repository import RepositoryConnector
from test_generator.models import RepositoryContext

context = RepositoryContext(
    repository_url="https://gitlab.example.com/project/repo.git",
    auth_type="token",
    auth_token="your_token"
)

connector = RepositoryConnector(context)
connector.connect()
# Работа с репозиторием
connector.disconnect()
```

### RepositoryIndexer
Индексация файлов и структуры репозитория.

```python
from test_generator.repository import RepositoryIndexer

indexer = RepositoryIndexer(connector)
index = indexer.index(context, force=False, incremental=True)
```

### PatternExtractor
Извлечение паттернов именования и кода.

```python
from test_generator.repository import PatternExtractor

extractor = PatternExtractor()
index = extractor.extract_patterns(index)
```

### TemplateAnalyzer
Анализ шаблонов кода.

```python
from test_generator.repository import TemplateAnalyzer

analyzer = TemplateAnalyzer()
index = analyzer.analyze_templates(index, repo_path)
```

### IndexStorage
Сохранение и загрузка индекса.

```python
from test_generator.repository import IndexStorage

# Сохранение
IndexStorage.save(index, Path("./index.json"))

# Загрузка
index = IndexStorage.load(Path("./index.json"))
```

## Использование через TestGenerator

```python
from test_generator import TestGenerator

generator = TestGenerator(config_path="config.yaml")

# Индексация репозитория
index = generator.index_repository(
    repository_url="https://gitlab.example.com/project/repo.git",
    force=False
)

# Проверка наличия индекса
if generator.is_repository_indexed():
    index = generator.get_repository_index()
    print(f"Индексировано файлов: {index.total_files}")
    print(f"Тестовых файлов: {index.test_files_count}")
    print(f"Page Objects: {index.page_object_files_count}")

# Обновление индекса
generator.update_repository_index(force=True)
```

## Формат индекса

Индекс сохраняется в JSON формате и содержит:

- **Структура проекта**: директории с тестами, Page Objects, фикстурами
- **Индексированные файлы**: метаданные о каждом файле (импорты, классы, функции)
- **Паттерны именования**: стили именования файлов, классов, функций
- **Паттерны кода**: использование qautils, Allure, базовые классы
- **Шаблоны**: примеры Page Objects, тестов, фикстур

## Конфигурация

В `config.yaml`:

```yaml
repository:
  url: "https://gitlab.example.com/project/repo.git"
  auth:
    type: "token"
    token: "${GITLAB_TOKEN}"
  index_path: "./.test_generator/index.json"
  auto_index: false
```

