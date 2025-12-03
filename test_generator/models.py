"""Модели данных библиотеки."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pathlib import Path
import json


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

    @validator("steps")
    def validate_steps(cls, v):
        """Валидация наличия шагов."""
        if not v:
            raise ValueError("Тест-кейс должен содержать хотя бы один шаг")
        return v

    @property
    def tags_list(self) -> List[str]:
        """Возвращает список тегов."""
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]

    @classmethod
    def parse_file(cls, file_path: Union[str, Path]) -> "TestCase":
        """
        Парсит тест-кейс из JSON файла.

        Args:
            file_path: Путь к JSON файлу

        Returns:
            Объект TestCase
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.parse_obj(data)

    @classmethod
    def parse_json(cls, json_str: str) -> "TestCase":
        """
        Парсит тест-кейс из JSON строки.

        Args:
            json_str: JSON строка

        Returns:
            Объект TestCase
        """
        data = json.loads(json_str)
        return cls.parse_obj(data)

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True


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
        description="Уровень качества генерации",
    )
    code_style: CodeStyle = Field(default=CodeStyle.STANDARD, description="Стиль генерируемого кода")
    include_comments: bool = Field(default=True, description="Включать комментарии в код")
    detail_level: str = Field(default="medium", description="Уровень детализации (low, medium, high)")

    # LLM настройки
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Валидация и форматирование
    validate_code: bool = Field(default=True, description="Валидировать сгенерированный код")
    format_code: bool = Field(default=True, description="Форматировать код")
    format_style: Optional[str] = Field(default="black", description="Стиль форматирования")

    # Поведение при генерации
    overwrite_existing: bool = Field(default=False, description="Перезаписывать существующие файлы")
    generate_page_objects: bool = Field(default=True, description="Генерировать Page Object классы")
    generate_fixtures: bool = Field(default=True, description="Генерировать фикстуры pytest")
    use_cdp: bool = Field(default=False, description="Использовать CDP для определения селекторов")

    # Дополнительные настройки
    custom_prompts: Optional[Dict[str, str]] = Field(
        default=None,
        description="Кастомные промпты для переопределения стандартных",
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Дополнительные метаданные")


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
        description="Сгенерированные файлы",
    )
    output_directory: Optional[Path] = Field(default=None, description="Директория с результатами")

    # Метаданные генерации
    generation_time_ms: float = Field(..., description="Время генерации в мс")
    llm_requests: List[LLMRequest] = Field(
        default_factory=list,
        description="Запросы к LLM",
    )

    # Валидация
    validation_report: Optional[Any] = Field(
        default=None,
        description="Отчет о валидации",
    )

    # Ошибки и предупреждения
    errors: List[str] = Field(default_factory=list, description="Ошибки")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")

    # Дополнительная информация
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")

    timestamp: datetime = Field(default_factory=datetime.now)

    @property
    def total_tokens_used(self) -> int:
        """Общее количество использованных токенов."""
        return sum(req.tokens_used or 0 for req in self.llm_requests)

    @property
    def total_llm_time_ms(self) -> float:
        """Общее время работы с LLM в мс."""
        return sum(req.response_time_ms or 0.0 for req in self.llm_requests)


class RepositoryContext(BaseModel):
    """Контекст репозитория для анализа паттернов."""

    # Источник
    repository_url: Optional[str] = Field(default=None, description="URL репозитория (полный или собранный)")
    repository_path: Optional[Path] = Field(default=None, description="Локальный путь")
    repository_type: str = Field(default="gitlab", description="Тип (gitlab, git)")
    
    # GitLab специфичные поля
    gitlab_url: Optional[str] = Field(default=None, description="Базовый URL GitLab сервера")
    project_path: Optional[str] = Field(default=None, description="Путь к проекту в GitLab (например: devzone/s200001640/erarpro/er-autotests)")

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
        description="Паттерны файлов для включения",
    )
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="Паттерны файлов для исключения",
    )

    # Дополнительные настройки
    branch: Optional[str] = Field(default=None, description="Ветка для анализа")
    commit: Optional[str] = Field(default=None, description="Конкретный коммит")


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

    issues: List[ValidationIssue] = Field(default_factory=list, description="Найденные проблемы")

    errors: List[ValidationIssue] = Field(default_factory=list, description="Ошибки")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="Предупреждения")
    info: List[ValidationIssue] = Field(default_factory=list, description="Информационные сообщения")

    # Метрики
    syntax_valid: bool = Field(..., description="Синтаксис валиден")
    imports_valid: bool = Field(..., description="Импорты валидны")
    structure_valid: bool = Field(..., description="Структура валидна")
    test_case_match: Optional[float] = Field(
        default=None,
        description="Соответствие тест-кейсу (0.0-1.0)",
    )

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метрики")

