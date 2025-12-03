# API Design - Библиотека генерации автотестов

## Оглавление

1. [Введение](#введение)
2. [Публичный Python API](#публичный-python-api)
3. [Модели данных](#модели-данных)
4. [Передача контекста и настроек](#передача-контекста-и-настроек)
5. [Интеграция с LLM](#интеграция-с-llm)
6. [Пайплайн генерации и валидации](#пайплайн-генерации-и-валидации)
7. [Нефункциональные требования](#нефункциональные-требования)
8. [Примеры использования](#примеры-использования)

---

## Введение

Данный документ описывает публичный Python API библиотеки для генерации UI-автотестов с использованием LLM. API спроектирован для использования в трех основных сценариях:

1. **Встраивание в существующий сервис** - использование через Python API
2. **CLI интерфейс** - командная строка для прямого использования
3. **Встраивание в веб-интерфейс** - REST API обертка над Python API

---

## Публичный Python API

### Основной класс: `TestGenerator`

Главная точка входа в библиотеку, координирующая все компоненты системы.

```python
from test_generator import TestGenerator
from test_generator.models import TestCase, GenerationConfig, GenerationResult
from test_generator.repository import RepositoryContext
from pathlib import Path
from typing import Optional, Dict, Any, List

class TestGenerator:
    """
    Главный класс для генерации автотестов UI на основе тест-кейсов.
    
    Координирует работу всех компонентов: парсинг тест-кейсов, анализ репозитория,
    генерацию кода через LLM, валидацию и сохранение результатов.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        llm_provider: Optional['LLMProvider'] = None,
        repository_context: Optional[RepositoryContext] = None
    ) -> None:
        """
        Инициализация генератора тестов.
        
        Args:
            config_path: Путь к YAML конфигурационному файлу
            config_dict: Словарь с конфигурацией (альтернатива config_path)
            llm_provider: Кастомный провайдер LLM (опционально)
            repository_context: Контекст репозитория для анализа (опционально)
            
        Raises:
            ConfigError: При ошибках загрузки конфигурации
            ValidationError: При невалидной конфигурации
        """
        pass
    
    def generate_test(
        self,
        test_case: Union[TestCase, str, Path, Dict[str, Any]],
        output_path: Optional[Union[str, Path]] = None,
        generation_config: Optional[GenerationConfig] = None,
        repository_context: Optional[RepositoryContext] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Генерирует автотест на основе тест-кейса.
        
        Args:
            test_case: Тест-кейс в виде объекта TestCase, пути к JSON файлу,
                      словаря или строки с JSON
            output_path: Путь для сохранения сгенерированных файлов.
                        Если None, используется из конфигурации
            generation_config: Настройки генерации (переопределяют конфиг)
            repository_context: Контекст репозитория для анализа паттернов
            additional_context: Дополнительный контекст (API контракты, спецификации)
            
        Returns:
            GenerationResult: Результат генерации с метаданными
            
        Raises:
            TestCaseParseError: При ошибках парсинга тест-кейса
            LLMError: При ошибках работы с LLM
            CodeValidationError: При ошибках валидации сгенерированного кода
            OutputError: При ошибках сохранения файлов
        """
        pass
    
    def generate_tests_batch(
        self,
        test_cases: List[Union[TestCase, str, Path, Dict[str, Any]]],
        output_path: Optional[Union[str, Path]] = None,
        generation_config: Optional[GenerationConfig] = None,
        repository_context: Optional[RepositoryContext] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        parallel: bool = False
    ) -> List[GenerationResult]:
        """
        Генерирует несколько автотестов пакетно.
        
        Args:
            test_cases: Список тест-кейсов
            output_path: Базовый путь для сохранения
            generation_config: Настройки генерации
            repository_context: Контекст репозитория
            additional_context: Дополнительный контекст
            parallel: Использовать параллельную генерацию (если поддерживается)
            
        Returns:
            Список результатов генерации
        """
        pass
    
    def index_repository(
        self,
        repository_url: Optional[str] = None,
        repository_path: Optional[Union[str, Path]] = None,
        force: bool = False,
        incremental: bool = True
    ) -> 'RepositoryIndex':
        """
        Индексирует репозиторий для извлечения паттернов и шаблонов.
        
        Args:
            repository_url: URL репозитория (GitLab или Git)
            repository_path: Локальный путь к репозиторию
            force: Принудительная переиндексация даже если индекс существует
            incremental: Инкрементальное обновление (только измененные файлы)
            
        Returns:
            RepositoryIndex: Индекс репозитория
            
        Raises:
            RepositoryConnectionError: При ошибках подключения
            RepositoryIndexError: При ошибках индексации
        """
        pass
    
    def update_repository_index(
        self,
        force: bool = False
    ) -> 'RepositoryIndex':
        """
        Обновляет существующий индекс репозитория.
        
        Args:
            force: Принудительная полная переиндексация
            
        Returns:
            Обновленный индекс репозитория
        """
        pass
    
    def is_repository_indexed(self) -> bool:
        """
        Проверяет наличие индекса репозитория.
        
        Returns:
            True если индекс существует и валиден
        """
        pass
    
    def get_repository_index(self) -> Optional['RepositoryIndex']:
        """
        Возвращает текущий индекс репозитория.
        
        Returns:
            Индекс репозитория или None если не проиндексирован
        """
        pass
    
    def validate_generated_code(
        self,
        code: str,
        test_case: Optional[TestCase] = None
    ) -> 'ValidationReport':
        """
        Валидирует сгенерированный код теста.
        
        Args:
            code: Сгенерированный код Python
            test_case: Исходный тест-кейс для проверки соответствия
            
        Returns:
            ValidationReport: Отчет о валидации
        """
        pass
    
    def format_code(
        self,
        code: str,
        style: Optional[str] = None
    ) -> str:
        """
        Форматирует код согласно стандартам проекта.
        
        Args:
            code: Исходный код
            style: Стиль форматирования (black, ruff, autopep8)
            
        Returns:
            Отформатированный код
        """
        pass
```

### Модели данных

#### `TestCase` - Модель тест-кейса

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class TestLayer(str, Enum):
    """Уровень тестирования."""
    E2E = "E2E"
    INTEGRATION = "INTEGRATION"
    UNIT = "UNIT"

class Severity(str, Enum):
    """Критичность теста."""
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"
    NORMAL = "NORMAL"
    MINOR = "MINOR"
    TRIVIAL = "TRIVIAL"

class TestStep(BaseModel):
    """Шаг тест-кейса."""
    id: str = Field(..., description="Уникальный идентификатор шага")
    name: str = Field(..., description="Название шага")
    description: str = Field(..., description="Описание действия")
    expected_result: str = Field(..., alias="expectedResult", description="Ожидаемый результат")
    status: Optional[str] = Field(default="", description="Статус выполнения")
    bug_link: Optional[str] = Field(default="", alias="bugLink")
    skip_reason: Optional[str] = Field(default="", alias="skipReason")
    attachments: Optional[str] = Field(default="")
    
    class Config:
        allow_population_by_field_name = True

class TestCase(BaseModel):
    """Модель тест-кейса для генерации автотестов."""
    
    # Основные поля
    id: str = Field(..., description="Уникальный идентификатор тест-кейса")
    name: str = Field(..., description="Название тест-кейса")
    description: Optional[str] = Field(default="", description="Подробное описание")
    preconditions: Optional[str] = Field(default="", description="Предусловия")
    expected_result: str = Field(..., alias="expectedResult", description="Ожидаемый результат")
    
    # Классификация
    epic: Optional[str] = Field(default="", description="Epic для Allure")
    feature: Optional[str] = Field(default="", description="Feature для Allure")
    story: Optional[str] = Field(default="", description="Story для Allure")
    component: Optional[str] = Field(default="", description="Компонент системы")
    test_layer: TestLayer = Field(..., alias="testLayer", description="Уровень тестирования")
    
    # Метаданные
    severity: Severity = Field(default=Severity.NORMAL, description="Критичность")
    priority: str = Field(default="1", description="Приоритет")
    environment: Optional[str] = Field(default="", description="Окружение")
    browser: Optional[str] = Field(default="chromium", description="Браузер для теста")
    tags: Optional[str] = Field(default="", description="Теги через запятую")
    test_type: str = Field(default="automated", alias="testType")
    
    # Владельцы
    owner: Optional[str] = Field(default="", description="Владелец теста")
    author: Optional[str] = Field(default="", description="Автор")
    reviewer: Optional[str] = Field(default="", description="Ревьюер")
    
    # Связи
    test_case_id: Optional[str] = Field(default=None, alias="testCaseId")
    issue_links: Optional[str] = Field(default="", alias="issueLinks")
    test_case_links: Optional[str] = Field(default="", alias="testCaseLinks")
    
    # Шаги теста
    steps: List[TestStep] = Field(default_factory=list, description="Шаги тест-кейса")
    
    # Временные метки
    created_at: Optional[int] = Field(default=None, alias="createdAt")
    updated_at: Optional[int] = Field(default=None, alias="updatedAt")
    
    @validator('steps')
    def validate_steps(cls, v):
        """Валидация наличия шагов."""
        if not v:
            raise ValueError("Тест-кейс должен содержать хотя бы один шаг")
        return v
    
    @property
    def tags_list(self) -> List[str]:
        """Возвращает список тегов."""
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
```

#### `GenerationConfig` - Настройки генерации

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class CodeStyle(str, Enum):
    """Стиль кода."""
    STANDARD = "standard"
    COMPACT = "compact"
    VERBOSE = "verbose"

class QualityLevel(str, Enum):
    """Уровень качества генерации."""
    FAST = "fast"  # Быстрая генерация, меньше проверок
    BALANCED = "balanced"  # Баланс скорости и качества
    HIGH = "high"  # Максимальное качество, больше проверок

class LLMConfig(BaseModel):
    """Настройки LLM провайдера."""
    provider: str = Field(default="ollama", description="Провайдер LLM")
    model: str = Field(default="codellama:13b", description="Модель для использования")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(default=4000, ge=100, le=32000, description="Максимум токенов")
    timeout: int = Field(default=300, ge=10, description="Таймаут запроса в секундах")
    max_retries: int = Field(default=3, ge=0, le=10, description="Максимум повторных попыток")
    retry_delay: float = Field(default=1.0, ge=0.0, description="Задержка между повторами")
    url: Optional[str] = Field(default=None, description="URL Ollama сервера")

class GenerationConfig(BaseModel):
    """Конфигурация генерации тестов."""
    
    # Качество и детализация
    quality_level: QualityLevel = Field(
        default=QualityLevel.BALANCED,
        description="Уровень качества генерации"
    )
    code_style: CodeStyle = Field(
        default=CodeStyle.STANDARD,
        description="Стиль генерируемого кода"
    )
    include_comments: bool = Field(
        default=True,
        description="Включать комментарии в код"
    )
    detail_level: str = Field(
        default="medium",
        description="Уровень детализации (low, medium, high)"
    )
    
    # LLM настройки
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Валидация и форматирование
    validate_code: bool = Field(default=True, description="Валидировать сгенерированный код")
    format_code: bool = Field(default=True, description="Форматировать код")
    format_style: Optional[str] = Field(default="black", description="Стиль форматирования")
    
    # Поведение при генерации
    overwrite_existing: bool = Field(
        default=False,
        description="Перезаписывать существующие файлы"
    )
    generate_page_objects: bool = Field(
        default=True,
        description="Генерировать Page Object классы"
    )
    generate_fixtures: bool = Field(
        default=True,
        description="Генерировать фикстуры pytest"
    )
    use_cdp: bool = Field(
        default=False,
        description="Использовать CDP для определения селекторов"
    )
    
    # Дополнительные настройки
    custom_prompts: Optional[Dict[str, str]] = Field(
        default=None,
        description="Кастомные промпты для переопределения стандартных"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Дополнительные метаданные"
    )
```

#### `GenerationResult` - Результат генерации

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

class GenerationStatus(str, Enum):
    """Статус генерации."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Частичная генерация (с предупреждениями)
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"

class GeneratedFile(BaseModel):
    """Информация о сгенерированном файле."""
    path: Path = Field(..., description="Путь к файлу")
    content: str = Field(..., description="Содержимое файла")
    file_type: str = Field(..., description="Тип файла (test, page_object, fixture)")
    size_bytes: int = Field(..., description="Размер файла в байтах")

class LLMRequest(BaseModel):
    """Информация о запросе к LLM."""
    prompt: str = Field(..., description="Отправленный промпт")
    model: str = Field(..., description="Использованная модель")
    temperature: float = Field(..., description="Температура")
    tokens_used: Optional[int] = Field(default=None, description="Использовано токенов")
    response_time_ms: Optional[float] = Field(default=None, description="Время ответа в мс")
    retry_count: int = Field(default=0, description="Количество повторов")

class GenerationResult(BaseModel):
    """Результат генерации автотеста."""
    
    # Статус
    status: GenerationStatus = Field(..., description="Статус генерации")
    success: bool = Field(..., description="Успешна ли генерация")
    
    # Входные данные
    test_case_id: str = Field(..., description="ID тест-кейса")
    test_case_name: str = Field(..., description="Название тест-кейса")
    
    # Результаты
    generated_files: List[GeneratedFile] = Field(
        default_factory=list,
        description="Сгенерированные файлы"
    )
    output_directory: Optional[Path] = Field(
        default=None,
        description="Директория с результатами"
    )
    
    # Метаданные генерации
    generation_time_ms: float = Field(..., description="Время генерации в мс")
    llm_requests: List[LLMRequest] = Field(
        default_factory=list,
        description="Запросы к LLM"
    )
    
    # Валидация
    validation_report: Optional['ValidationReport'] = Field(
        default=None,
        description="Отчет о валидации"
    )
    
    # Ошибки и предупреждения
    errors: List[str] = Field(default_factory=list, description="Ошибки")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")
    
    # Дополнительная информация
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метаданные"
    )
    
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_tokens_used(self) -> int:
        """Общее количество использованных токенов."""
        return sum(req.tokens_used or 0 for req in self.llm_requests)
    
    @property
    def total_llm_time_ms(self) -> float:
        """Общее время работы с LLM в мс."""
        return sum(req.response_time_ms or 0.0 for req in self.llm_requests)
```

#### `RepositoryContext` - Контекст репозитория

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from pathlib import Path

class RepositoryContext(BaseModel):
    """Контекст репозитория для анализа паттернов."""
    
    # Источник
    repository_url: Optional[str] = Field(default=None, description="URL репозитория")
    repository_path: Optional[Path] = Field(default=None, description="Локальный путь")
    repository_type: str = Field(default="gitlab", description="Тип (gitlab, git)")
    
    # Аутентификация
    auth_type: Optional[str] = Field(default=None, description="Тип аутентификации")
    auth_token: Optional[str] = Field(default=None, description="Токен доступа")
    ssh_key_path: Optional[Path] = Field(default=None, description="Путь к SSH ключу")
    
    # Настройки индексации
    index_path: Optional[Path] = Field(default=None, description="Путь к индексу")
    auto_index: bool = Field(default=False, description="Автоматическая индексация")
    
    # Фильтры
    include_patterns: Optional[List[str]] = Field(
        default=None,
        description="Паттерны файлов для включения"
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="Паттерны файлов для исключения"
    )
    
    # Дополнительные настройки
    branch: Optional[str] = Field(default=None, description="Ветка для анализа")
    commit: Optional[str] = Field(default=None, description="Конкретный коммит")
```

#### `ValidationReport` - Отчет о валидации

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ValidationLevel(str, Enum):
    """Уровень валидации."""
    SYNTAX = "syntax"  # Только синтаксис
    STRUCTURE = "structure"  # Структура и импорты
    SEMANTIC = "semantic"  # Семантика и соответствие тест-кейсу
    FULL = "full"  # Полная валидация

class ValidationIssue(BaseModel):
    """Проблема при валидации."""
    level: str = Field(..., description="Уровень (error, warning, info)")
    message: str = Field(..., description="Сообщение")
    file: Optional[str] = Field(default=None, description="Файл")
    line: Optional[int] = Field(default=None, description="Строка")
    code: Optional[str] = Field(default=None, description="Код проблемы")

class ValidationReport(BaseModel):
    """Отчет о валидации сгенерированного кода."""
    
    valid: bool = Field(..., description="Валиден ли код")
    validation_level: ValidationLevel = Field(..., description="Уровень валидации")
    
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="Найденные проблемы"
    )
    
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="Ошибки"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="Предупреждения"
    )
    info: List[ValidationIssue] = Field(
        default_factory=list,
        description="Информационные сообщения"
    )
    
    # Метрики
    syntax_valid: bool = Field(..., description="Синтаксис валиден")
    imports_valid: bool = Field(..., description="Импорты валидны")
    structure_valid: bool = Field(..., description="Структура валидна")
    test_case_match: Optional[float] = Field(
        default=None,
        description="Соответствие тест-кейсу (0.0-1.0)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метрики"
    )
```

---

## Передача контекста и настроек

### 1. Передача исходного контекста

Библиотека поддерживает несколько способов передачи контекста:

#### Через `additional_context` параметр

```python
additional_context = {
    # API контракты (OpenAPI/Swagger)
    "api_contracts": {
        "users_api": {
            "type": "openapi",
            "content": "...",  # JSON/YAML содержимое
            "url": "https://api.example.com/openapi.json"
        }
    },
    
    # Спецификации
    "specifications": {
        "ui_spec": {
            "type": "html",
            "content": "...",  # HTML спецификация
            "url": "https://docs.example.com/ui-spec"
        }
    },
    
    # Требования
    "requirements": {
        "functional": ["REQ-001", "REQ-002"],
        "non_functional": ["PERF-001"]
    },
    
    # Дополнительный код для анализа
    "code_samples": {
        "existing_tests": ["path/to/test1.py", "path/to/test2.py"],
        "page_objects": ["path/to/page1.py"]
    },
    
    # Селекторы и локаторы
    "selectors": {
        "login_page": {
            "username_input": "input[name='username']",
            "password_input": "input[name='password']"
        }
    },
    
    # Конфигурации
    "configs": {
        "base_url": "https://example.com",
        "timeouts": {"default": 30000}
    }
}

result = generator.generate_test(
    test_case=test_case,
    additional_context=additional_context
)
```

#### Через конфигурационный файл

```yaml
# config.yaml
context:
  api_contracts:
    - type: openapi
      url: https://api.example.com/openapi.json
      cache: true
  
  specifications:
    - type: html
      path: ./specs/ui-spec.html
  
  code_samples:
    include_patterns:
      - "**/tests/**/*.py"
      - "**/pages/**/*.py"
```

### 2. Настройки генерации

Настройки передаются через `GenerationConfig`:

```python
from test_generator.models import GenerationConfig, QualityLevel, CodeStyle, LLMConfig

# Базовые настройки
config = GenerationConfig(
    quality_level=QualityLevel.HIGH,
    code_style=CodeStyle.STANDARD,
    include_comments=True,
    detail_level="high"
)

# Настройки LLM
config.llm = LLMConfig(
    model="codellama:13b",
    temperature=0.2,  # Низкая температура для более детерминированного кода
    max_tokens=8000,
    timeout=600,
    max_retries=5
)

# Валидация и форматирование
config.validate_code = True
config.format_code = True
config.format_style = "black"

# Поведение
config.overwrite_existing = False
config.generate_page_objects = True
config.use_cdp = True  # Использовать CDP для селекторов

# Кастомные промпты
config.custom_prompts = {
    "system": "Ты эксперт по автоматизации тестирования...",
    "page_object": "Создай Page Object класс для..."
}

result = generator.generate_test(
    test_case=test_case,
    generation_config=config
)
```

### 3. Возврат результатов

Библиотека возвращает структурированный результат:

```python
result: GenerationResult = generator.generate_test(test_case)

# Проверка успешности
if result.success:
    print(f"Генерация успешна: {len(result.generated_files)} файлов")
    
    # Доступ к файлам
    for file in result.generated_files:
        print(f"  - {file.path}: {file.file_type}")
        print(f"    Размер: {file.size_bytes} байт")
    
    # Метаданные LLM
    print(f"Использовано токенов: {result.total_tokens_used}")
    print(f"Время LLM: {result.total_llm_time_ms} мс")
    
    # Валидация
    if result.validation_report:
        report = result.validation_report
        if report.valid:
            print("Код валиден")
        else:
            print(f"Найдено ошибок: {len(report.errors)}")
            for error in report.errors:
                print(f"  - {error.message} ({error.file}:{error.line})")
else:
    # Ошибки
    print("Ошибки генерации:")
    for error in result.errors:
        print(f"  - {error}")
    
    # Предупреждения
    if result.warnings:
        print("Предупреждения:")
        for warning in result.warnings:
            print(f"  - {warning}")

# Доступ к сырым ответам LLM
for llm_req in result.llm_requests:
    print(f"Промпт: {llm_req.prompt[:100]}...")
    print(f"Модель: {llm_req.model}")
    print(f"Токены: {llm_req.tokens_used}")
```

---

## Интеграция с LLM

### Абстракция провайдера

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from test_generator.models import LLMRequest

class LLMProvider(ABC):
    """Абстрактный базовый класс для провайдеров LLM."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Основной промпт
            system_prompt: Системный промпт
            temperature: Температура генерации
            max_tokens: Максимум токенов
            **kwargs: Дополнительные параметры
            
        Returns:
            Сгенерированный текст
            
        Raises:
            LLMError: При ошибках работы с LLM
        """
        pass
    
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Генерирует структурированный ответ (JSON).
        
        Args:
            prompt: Промпт
            response_format: Схема ожидаемого ответа
            **kwargs: Дополнительные параметры
            
        Returns:
            Структурированный ответ
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность провайдера."""
        pass

class OllamaProvider(LLMProvider):
    """Провайдер для Ollama (локальный и удаленный)."""
    
    def __init__(
        self,
        url: str = "http://localhost:11434",
        model: str = "codellama:13b",
        timeout: int = 300,
        max_retries: int = 3
    ):
        """
        Инициализация Ollama провайдера.
        
        Args:
            url: URL Ollama сервера
            model: Модель для использования
            timeout: Таймаут запроса
            max_retries: Максимум повторов
        """
        pass
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Реализация генерации через Ollama."""
        pass
```

### Формат промптов

#### Структура промпта

```python
class PromptBuilder:
    """Построитель промптов для LLM."""
    
    def build_system_prompt(
        self,
        templates: Optional[Dict[str, Any]] = None,
        code_style: CodeStyle = CodeStyle.STANDARD
    ) -> str:
        """
        Строит системный промпт.
        
        Пример:
        "Ты эксперт по автоматизации тестирования на Python.
        Используй паттерн Page Object Model.
        Применяй библиотеку qautils для взаимодействия с элементами.
        Следуй корпоративным стандартам кодирования..."
        """
        pass
    
    def build_context_prompt(
        self,
        repository_index: Optional['RepositoryIndex'] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Строит контекстный промпт с информацией о проекте.
        
        Включает:
        - Структуру проекта
        - Примеры существующих тестов
        - Паттерны именования
        - Использование qautils
        """
        pass
    
    def build_task_prompt(
        self,
        test_case: TestCase,
        page_objects_needed: List[str]
    ) -> str:
        """
        Строит задачный промпт для конкретного тест-кейса.
        
        Включает:
        - Описание тест-кейса
        - Шаги теста
        - Требуемые Page Objects
        - Ожидаемые результаты
        """
        pass
    
    def build_full_prompt(
        self,
        test_case: TestCase,
        repository_index: Optional['RepositoryIndex'] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Строит полный промпт для генерации.
        
        Returns:
            Словарь с ключами: system, context, task, examples
        """
        pass
```

#### Пример структурированного ответа

```python
# Промпт для генерации Page Object
prompt = """
Создай Page Object класс для страницы логина на основе следующего тест-кейса.
Верни ответ в формате JSON:
{
    "class_name": "LoginPage",
    "base_url": "https://example.com/login",
    "elements": [
        {
            "name": "username_input",
            "type": "Input",
            "strategy": "by_name",
            "value": "username",
            "allure_name": "Поле ввода имени пользователя"
        }
    ],
    "methods": [
        {
            "name": "login",
            "description": "Выполняет вход в систему",
            "parameters": ["username", "password"],
            "code": "..."
        }
    ]
}
"""

# Генерация структурированного ответа
response_format = {
    "type": "object",
    "properties": {
        "class_name": {"type": "string"},
        "base_url": {"type": "string"},
        "elements": {"type": "array"},
        "methods": {"type": "array"}
    },
    "required": ["class_name", "elements"]
}

result = llm_provider.generate_structured(
    prompt=prompt,
    response_format=response_format
)
```

### Стратегия ретраев

```python
from typing import Callable, Optional
import time
import logging

class RetryStrategy:
    """Стратегия повторных попыток для LLM."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retryable_errors: Optional[List[type]] = None
    ):
        """
        Инициализация стратегии.
        
        Args:
            max_retries: Максимум повторов
            initial_delay: Начальная задержка
            backoff_factor: Множитель для экспоненциальной задержки
            max_delay: Максимальная задержка
            retryable_errors: Типы ошибок, при которых стоит повторять
        """
        pass
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Выполняет функцию с повторными попытками.
        
        Returns:
            Результат выполнения функции
            
        Raises:
            Последняя ошибка после всех попыток
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # Проверка, стоит ли повторять
                if not self._should_retry(e, attempt):
                    raise
                
                # Задержка перед повтором
                if attempt < self.max_retries:
                    delay = min(
                        self.initial_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    time.sleep(delay)
                    logging.warning(
                        f"Повторная попытка {attempt + 1}/{self.max_retries} "
                        f"после ошибки: {e}"
                    )
        
        raise last_error
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Определяет, стоит ли повторять при данной ошибке."""
        # Повторяем при таймаутах, сетевых ошибках, временных ошибках LLM
        retryable = (
            TimeoutError,
            ConnectionError,
            LLMTimeoutError,
            LLMTemporaryError
        )
        return isinstance(error, retryable) and attempt < self.max_retries
```

### Логирование и трассировка

```python
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

class LLMTracer:
    """Трассировка запросов и ответов LLM для дебага и аналитики."""
    
    def __init__(
        self,
        log_file: Optional[str] = None,
        log_level: str = "INFO",
        enable_offline_analysis: bool = True
    ):
        """
        Инициализация трассировщика.
        
        Args:
            log_file: Путь к файлу логов
            log_level: Уровень логирования
            enable_offline_analysis: Сохранять данные для офлайн анализа
        """
        self.logger = logging.getLogger("test_generator.llm")
        self.log_file = log_file
        self.enable_offline_analysis = enable_offline_analysis
        self.trace_data: List[Dict[str, Any]] = []
    
    def trace_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "unknown",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Логирует запрос к LLM и возвращает ID трассировки.
        
        Returns:
            Уникальный ID запроса
        """
        trace_id = f"llm_req_{datetime.now().timestamp()}"
        
        trace_entry = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt_length": len(prompt),
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "metadata": metadata or {}
        }
        
        # Логирование
        self.logger.info(
            f"[{trace_id}] LLM Request: model={model}, "
            f"prompt_len={len(prompt)}, temp={temperature}"
        )
        
        if self.log_file:
            # Сохранение полного промпта (для офлайн анализа)
            trace_entry["prompt"] = prompt
            if system_prompt:
                trace_entry["system_prompt"] = system_prompt
        
        self.trace_data.append(trace_entry)
        return trace_id
    
    def trace_response(
        self,
        trace_id: str,
        response: str,
        tokens_used: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Логирует ответ от LLM.
        
        Args:
            trace_id: ID запроса
            response: Ответ от LLM
            tokens_used: Использовано токенов
            response_time_ms: Время ответа
            error: Ошибка (если была)
        """
        trace_entry = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "response_length": len(response),
            "tokens_used": tokens_used,
            "response_time_ms": response_time_ms,
            "success": error is None
        }
        
        if error:
            trace_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error)
            }
        
        # Логирование
        if error:
            self.logger.error(
                f"[{trace_id}] LLM Response Error: {error}",
                exc_info=error
            )
        else:
            self.logger.info(
                f"[{trace_id}] LLM Response: len={len(response)}, "
                f"tokens={tokens_used}, time={response_time_ms}ms"
            )
        
        if self.log_file:
            trace_entry["response"] = response
        
        # Обновление записи запроса
        for entry in self.trace_data:
            if entry.get("trace_id") == trace_id and entry.get("type") == "request":
                entry["response"] = trace_entry
                break
        
        self.trace_data.append(trace_entry)
    
    def save_trace(self, file_path: str) -> None:
        """Сохраняет трассировку в файл для офлайн анализа."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.trace_data, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику по запросам."""
        requests = [e for e in self.trace_data if e.get("type") == "request"]
        responses = [e for e in self.trace_data if e.get("type") == "response"]
        
        successful = [r for r in responses if r.get("success", False)]
        
        return {
            "total_requests": len(requests),
            "successful_requests": len(successful),
            "failed_requests": len(responses) - len(successful),
            "total_tokens": sum(r.get("tokens_used", 0) for r in successful),
            "avg_response_time_ms": (
                sum(r.get("response_time_ms", 0) for r in successful) / len(successful)
                if successful else 0
            ),
            "total_prompt_length": sum(r.get("prompt_length", 0) for r in requests)
        }
```

### Обработка ошибок и нестабильности

```python
from typing import Optional, Callable
from enum import Enum

class LLMErrorType(str, Enum):
    """Типы ошибок LLM."""
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    RATE_LIMIT = "rate_limit"
    INVALID_RESPONSE = "invalid_response"
    PARTIAL_RESPONSE = "partial_response"
    MODEL_UNAVAILABLE = "model_unavailable"
    UNKNOWN = "unknown"

class LLMError(Exception):
    """Базовое исключение для ошибок LLM."""
    def __init__(
        self,
        message: str,
        error_type: LLMErrorType = LLMErrorType.UNKNOWN,
        retryable: bool = False,
        original_error: Optional[Exception] = None
    ):
        self.error_type = error_type
        self.retryable = retryable
        self.original_error = original_error
        super().__init__(message)

class LLMErrorHandler:
    """Обработчик ошибок и нестабильности LLM."""
    
    def __init__(
        self,
        fallback_strategy: Optional[Callable] = None,
        degradation_mode: bool = True
    ):
        """
        Инициализация обработчика.
        
        Args:
            fallback_strategy: Стратегия отката при ошибках
            degradation_mode: Включить деградационный режим
        """
        self.fallback_strategy = fallback_strategy
        self.degradation_mode = degradation_mode
    
    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Обрабатывает ошибку LLM.
        
        Args:
            error: Ошибка
            context: Контекст запроса
            
        Returns:
            Результат обработки (fallback ответ или None)
        """
        error_type = self._classify_error(error)
        
        # Логирование
        logging.error(
            f"LLM Error: {error_type.value} - {error}",
            exc_info=error,
            extra=context
        )
        
        # Обработка по типу
        if error_type == LLMErrorType.TIMEOUT:
            return self._handle_timeout(context)
        elif error_type == LLMErrorType.PARTIAL_RESPONSE:
            return self._handle_partial_response(context)
        elif error_type == LLMErrorType.CONNECTION:
            return self._handle_connection_error(context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_timeout(self, context: Dict[str, Any]) -> Optional[str]:
        """Обработка таймаута."""
        if self.degradation_mode:
            # Упрощенный промпт для быстрой генерации
            simplified_prompt = self._simplify_prompt(context.get("prompt", ""))
            return self._retry_with_simplified_prompt(simplified_prompt, context)
        return None
    
    def _handle_partial_response(
        self,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Обработка частичного ответа."""
        partial_response = context.get("partial_response", "")
        
        if partial_response and self._is_usable_partial(partial_response):
            logging.warning("Использован частичный ответ LLM")
            return partial_response
        
        # Попытка достроить ответ
        return self._complete_partial_response(partial_response, context)
    
    def _handle_connection_error(self, context: Dict[str, Any]) -> Optional[str]:
        """Обработка ошибки подключения."""
        if self.fallback_strategy:
            return self.fallback_strategy(context)
        return None
    
    def _handle_generic_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Обработка общей ошибки."""
        if self.degradation_mode and self.fallback_strategy:
            return self.fallback_strategy(context)
        return None
    
    def _classify_error(self, error: Exception) -> LLMErrorType:
        """Классифицирует тип ошибки."""
        if isinstance(error, TimeoutError):
            return LLMErrorType.TIMEOUT
        elif isinstance(error, ConnectionError):
            return LLMErrorType.CONNECTION
        elif "rate limit" in str(error).lower():
            return LLMErrorType.RATE_LIMIT
        elif isinstance(error, LLMError):
            return error.error_type
        else:
            return LLMErrorType.UNKNOWN
    
    def _is_usable_partial(self, response: str) -> bool:
        """Проверяет, можно ли использовать частичный ответ."""
        # Проверка на наличие ключевых структур
        has_class = "class " in response
        has_method = "def " in response
        has_imports = "import " in response
        
        return has_class or (has_method and has_imports)
```

---

## Пайплайн генерации и валидации

### Полный пайплайн

```python
class GenerationPipeline:
    """Пайплайн генерации автотестов."""
    
    def execute(
        self,
        test_case: TestCase,
        config: GenerationConfig,
        repository_index: Optional['RepositoryIndex'] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Выполняет полный пайплайн генерации.
        
        Этапы:
        1. Парсинг и валидация тест-кейса
        2. Анализ шагов и определение Page Objects
        3. Построение промптов
        4. Генерация через LLM
        5. Пост-обработка ответа
        6. Генерация кода
        7. Валидация
        8. Форматирование
        9. Сохранение
        """
        start_time = time.time()
        result = GenerationResult(
            status=GenerationStatus.FAILED,
            success=False,
            test_case_id=test_case.id,
            test_case_name=test_case.name
        )
        
        try:
            # Этап 1: Валидация тест-кейса
            self._validate_test_case(test_case)
            
            # Этап 2: Анализ шагов
            page_objects_needed = self._analyze_steps(test_case)
            
            # Этап 3: Построение промптов
            prompts = self._build_prompts(
                test_case,
                repository_index,
                additional_context,
                config
            )
            
            # Этап 4: Генерация через LLM
            llm_responses = self._generate_with_llm(
                prompts,
                config.llm,
                result
            )
            
            # Этап 5: Пост-обработка
            processed_code = self._post_process_responses(
                llm_responses,
                test_case
            )
            
            # Этап 6: Генерация файлов
            generated_files = self._generate_files(
                processed_code,
                test_case,
                config
            )
            
            # Этап 7: Валидация
            if config.validate_code:
                validation_report = self._validate_code(
                    generated_files,
                    test_case
                )
                result.validation_report = validation_report
                
                if not validation_report.valid:
                    result.status = GenerationStatus.VALIDATION_ERROR
                    result.errors.extend([
                        issue.message for issue in validation_report.errors
                    ])
            
            # Этап 8: Форматирование
            if config.format_code:
                generated_files = self._format_files(
                    generated_files,
                    config.format_style
                )
            
            # Этап 9: Сохранение
            output_dir = self._save_files(
                generated_files,
                config.output_path
            )
            
            # Успешное завершение
            result.status = GenerationStatus.SUCCESS
            result.success = True
            result.generated_files = generated_files
            result.output_directory = output_dir
            
        except Exception as e:
            result.errors.append(str(e))
            logging.error("Ошибка в пайплайне генерации", exc_info=e)
        
        finally:
            result.generation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _analyze_steps(self, test_case: TestCase) -> List[str]:
        """
        Анализирует шаги тест-кейса и определяет необходимые Page Objects.
        
        Returns:
            Список названий необходимых Page Objects
        """
        page_objects = []
        
        for step in test_case.steps:
            # Извлечение URL из шага
            url = self._extract_url_from_step(step.description)
            if url:
                page_name = self._derive_page_name(url)
                if page_name not in page_objects:
                    page_objects.append(page_name)
            
            # Анализ действий
            actions = self._extract_actions(step.description)
            for action in actions:
                page_name = self._derive_page_from_action(action)
                if page_name and page_name not in page_objects:
                    page_objects.append(page_name)
        
        return page_objects
    
    def _generate_with_llm(
        self,
        prompts: Dict[str, str],
        llm_config: LLMConfig,
        result: GenerationResult
    ) -> Dict[str, Any]:
        """
        Генерирует код через LLM.
        
        Returns:
            Словарь с ответами LLM для разных компонентов
        """
        llm_provider = self._get_llm_provider(llm_config)
        responses = {}
        
        # Генерация Page Objects
        if prompts.get("page_objects"):
            try:
                response = llm_provider.generate(
                    prompt=prompts["page_objects"],
                    system_prompt=prompts.get("system"),
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens
                )
                responses["page_objects"] = response
                
                # Логирование запроса
                llm_request = LLMRequest(
                    prompt=prompts["page_objects"][:500],  # Первые 500 символов
                    model=llm_config.model,
                    temperature=llm_config.temperature
                )
                result.llm_requests.append(llm_request)
                
            except Exception as e:
                result.errors.append(f"Ошибка генерации Page Objects: {e}")
                raise
        
        # Генерация тестового метода
        if prompts.get("test_method"):
            try:
                response = llm_provider.generate(
                    prompt=prompts["test_method"],
                    system_prompt=prompts.get("system"),
                    temperature=llm_config.temperature,
                    max_tokens=llm_config.max_tokens
                )
                responses["test_method"] = response
                
            except Exception as e:
                result.errors.append(f"Ошибка генерации теста: {e}")
                raise
        
        return responses
    
    def _post_process_responses(
        self,
        llm_responses: Dict[str, Any],
        test_case: TestCase
    ) -> Dict[str, str]:
        """
        Пост-обработка ответов LLM.
        
        Включает:
        - Извлечение кода из markdown блоков
        - Валидацию структуры
        - Нормализацию импортов
        - Добавление недостающих частей
        """
        processed = {}
        
        for key, response in llm_responses.items():
            # Извлечение кода из markdown
            code = self._extract_code_from_markdown(response)
            
            # Валидация синтаксиса
            if not self._validate_syntax(code):
                raise CodeValidationError(f"Невалидный синтаксис в {key}")
            
            # Нормализация
            code = self._normalize_imports(code)
            code = self._add_missing_parts(code, test_case)
            
            processed[key] = code
        
        return processed
    
    def _validate_code(
        self,
        files: List[GeneratedFile],
        test_case: TestCase
    ) -> ValidationReport:
        """
        Валидирует сгенерированный код.
        
        Проверки:
        1. Синтаксис Python
        2. Импорты
        3. Структура (классы, методы)
        4. Соответствие тест-кейсу
        5. Использование qautils
        6. Allure декораторы
        """
        issues = []
        
        for file in files:
            # Синтаксис
            syntax_valid, syntax_issues = self._validate_syntax_detailed(file.content)
            if not syntax_valid:
                issues.extend(syntax_issues)
            
            # Импорты
            import_issues = self._validate_imports(file.content)
            issues.extend(import_issues)
            
            # Структура
            structure_issues = self._validate_structure(file.content, file.file_type)
            issues.extend(structure_issues)
            
            # Соответствие тест-кейсу
            if file.file_type == "test":
                test_case_issues = self._validate_test_case_match(
                    file.content,
                    test_case
                )
                issues.extend(test_case_issues)
        
        # Классификация проблем
        errors = [i for i in issues if i.level == "error"]
        warnings = [i for i in issues if i.level == "warning"]
        info = [i for i in issues if i.level == "info"]
        
        return ValidationReport(
            valid=len(errors) == 0,
            validation_level=ValidationLevel.FULL,
            issues=issues,
            errors=errors,
            warnings=warnings,
            info=info,
            syntax_valid=len([i for i in errors if "syntax" in i.message.lower()]) == 0,
            imports_valid=len([i for i in errors if "import" in i.message.lower()]) == 0,
            structure_valid=len([i for i in errors if "structure" in i.message.lower()]) == 0,
            test_case_match=self._calculate_test_case_match(files, test_case)
        )
```

---

## Нефункциональные требования

### Производительность

#### Предположения и ограничения

- **Объем данных**:
  - Тест-кейс: до 100 КБ (JSON)
  - Индекс репозитория: до 50 МБ
  - Контекст: до 10 МБ
  
- **Время ответа**:
  - Генерация одного теста: 30-120 секунд (зависит от LLM)
  - Индексация репозитория: 1-5 минут (зависит от размера)
  - Валидация кода: < 5 секунд
  
- **Ресурсы**:
  - Память: минимум 2 ГБ, рекомендуется 4+ ГБ
  - CPU: зависит от LLM (локальный Ollama требует больше ресурсов)
  - Диск: минимум 1 ГБ для индексов и кэша

#### Оптимизации

```python
class PerformanceOptimizer:
    """Оптимизатор производительности."""
    
    def __init__(self):
        self.cache = {}
        self.parallel_executor = None
    
    def cache_repository_index(
        self,
        repository_url: str,
        index: 'RepositoryIndex'
    ) -> None:
        """Кэширует индекс репозитория."""
        cache_key = f"repo_index_{hash(repository_url)}"
        self.cache[cache_key] = index
    
    def get_cached_index(
        self,
        repository_url: str
    ) -> Optional['RepositoryIndex']:
        """Получает кэшированный индекс."""
        cache_key = f"repo_index_{hash(repository_url)}"
        return self.cache.get(cache_key)
    
    def optimize_prompt_size(
        self,
        prompt: str,
        max_length: int = 8000
    ) -> str:
        """Оптимизирует размер промпта."""
        if len(prompt) <= max_length:
            return prompt
        
        # Сокращение примеров кода
        # Приоритизация важной информации
        # Удаление избыточных комментариев
        return self._truncate_intelligently(prompt, max_length)
```

### Масштабируемость

- **Параллельная генерация**: Поддержка пакетной обработки нескольких тест-кейсов
- **Асинхронность**: Опциональная асинхронная работа с LLM
- **Распределенная обработка**: Возможность использования удаленного Ollama сервера

### Безопасность

```python
class SecurityManager:
    """Менеджер безопасности."""
    
    def sanitize_input(self, data: Any) -> Any:
        """Санитизация входных данных."""
        # Защита от инъекций
        # Валидация путей
        # Проверка содержимого файлов
        pass
    
    def secure_token_storage(self, token: str) -> str:
        """Безопасное хранение токенов."""
        # Использование переменных окружения
        # Шифрование при необходимости
        # Никогда не логировать токены
        pass
    
    def validate_file_path(self, path: Path) -> bool:
        """Валидация путей файлов."""
        # Защита от path traversal
        # Проверка разрешенных директорий
        pass
```

### Логирование и Observability

```python
import logging
import json
from typing import Dict, Any
from datetime import datetime

class ObservabilityManager:
    """Менеджер observability."""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = self._setup_logger(config)
        self.metrics_collector = MetricsCollector()
    
    def log_generation_start(
        self,
        test_case_id: str,
        config: GenerationConfig
    ) -> None:
        """Логирует начало генерации."""
        self.logger.info(
            f"Генерация начата: test_case={test_case_id}, "
            f"model={config.llm.model}, quality={config.quality_level}"
        )
        self.metrics_collector.increment("generation.started")
    
    def log_generation_complete(
        self,
        result: GenerationResult
    ) -> None:
        """Логирует завершение генерации."""
        self.logger.info(
            f"Генерация завершена: test_case={result.test_case_id}, "
            f"status={result.status}, files={len(result.generated_files)}, "
            f"time={result.generation_time_ms}ms"
        )
        
        # Метрики
        self.metrics_collector.record(
            "generation.duration_ms",
            result.generation_time_ms
        )
        self.metrics_collector.record(
            "generation.tokens_used",
            result.total_tokens_used
        )
        
        if result.success:
            self.metrics_collector.increment("generation.success")
        else:
            self.metrics_collector.increment("generation.failed")
    
    def log_llm_request(
        self,
        request: LLMRequest,
        response_time_ms: float,
        tokens_used: int
    ) -> None:
        """Логирует запрос к LLM."""
        self.logger.debug(
            f"LLM Request: model={request.model}, "
            f"time={response_time_ms}ms, tokens={tokens_used}"
        )
        
        self.metrics_collector.record("llm.response_time_ms", response_time_ms)
        self.metrics_collector.record("llm.tokens_used", tokens_used)

class MetricsCollector:
    """Сборщик метрик."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Увеличивает счетчик."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = 0
        self.metrics[metric_name] += value
    
    def record(self, metric_name: str, value: float) -> None:
        """Записывает значение метрики."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку метрик."""
        summary = {}
        for name, values in self.metrics.items():
            if isinstance(values, list):
                summary[name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
            else:
                summary[name] = values
        return summary
```

---

## Примеры использования

### Пример 1: Базовое использование через API

```python
from test_generator import TestGenerator
from test_generator.models import TestCase, GenerationConfig

# Инициализация
generator = TestGenerator(config_path="config.yaml")

# Загрузка тест-кейса
test_case = TestCase.parse_file("test_case.json")

# Генерация
result = generator.generate_test(
    test_case=test_case,
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
# Дополнительный контекст
additional_context = {
    "api_contracts": {
        "users_api": {
            "type": "openapi",
            "url": "https://api.example.com/openapi.json"
        }
    },
    "selectors": {
        "login_page": {
            "username": "input[name='username']",
            "password": "input[name='password']"
        }
    }
}

# Генерация с контекстом
result = generator.generate_test(
    test_case=test_case,
    additional_context=additional_context,
    generation_config=GenerationConfig(
        quality_level=QualityLevel.HIGH,
        use_cdp=True
    )
)
```

### Пример 3: Пакетная генерация

```python
# Список тест-кейсов
test_cases = [
    "test_case_1.json",
    "test_case_2.json",
    "test_case_3.json"
]

# Пакетная генерация
results = generator.generate_tests_batch(
    test_cases=test_cases,
    output_path="./generated_tests",
    parallel=True  # Параллельная обработка
)

# Статистика
successful = sum(1 for r in results if r.success)
print(f"Успешно: {successful}/{len(results)}")
```

### Пример 4: С индексацией репозитория

```python
# Индексация репозитория
index = generator.index_repository(
    repository_url="https://gitlab.example.com/project/repo.git",
    force=False
)

# Генерация с учетом паттернов репозитория
result = generator.generate_test(
    test_case=test_case,
    repository_context=RepositoryContext(
        repository_url="https://gitlab.example.com/project/repo.git"
    )
)
```

### Пример 5: Кастомный LLM провайдер

```python
from test_generator.llm import LLMProvider

class CustomLLMProvider(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> str:
        # Кастомная реализация
        return "generated code"
    
    def generate_structured(self, prompt: str, response_format: Dict, **kwargs) -> Dict:
        # Кастомная реализация
        return {}
    
    def is_available(self) -> bool:
        return True

# Использование кастомного провайдера
generator = TestGenerator(
    config_path="config.yaml",
    llm_provider=CustomLLMProvider()
)
```

---

## Заключение

Данный API дизайн обеспечивает:

1. **Гибкость** - поддержка различных сценариев использования
2. **Расширяемость** - возможность кастомизации через интерфейсы
3. **Надежность** - обработка ошибок и нестабильности LLM
4. **Observability** - детальное логирование и трассировка
5. **Производительность** - оптимизации и кэширование

Библиотека готова к использованию в production окружении с учетом всех требований из ARCHITECTURE.md.

