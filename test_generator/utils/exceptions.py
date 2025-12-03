"""Исключения библиотеки."""


class TestGeneratorError(Exception):
    """Базовое исключение библиотеки."""

    pass


class ConfigError(TestGeneratorError):
    """Ошибка загрузки или валидации конфигурации."""

    pass


class ValidationError(TestGeneratorError):
    """Ошибка валидации данных."""

    pass


class TestCaseParseError(TestGeneratorError):
    """Ошибка парсинга тест-кейса."""

    pass


class LLMError(TestGeneratorError):
    """Базовое исключение для ошибок LLM."""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        retryable: bool = False,
        original_error: Exception = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable
        self.original_error = original_error


class LLMTimeoutError(LLMError):
    """Ошибка таймаута LLM."""

    def __init__(self, message: str = "LLM request timeout", original_error: Exception = None):
        super().__init__(message, error_type="timeout", retryable=True, original_error=original_error)


class LLMTemporaryError(LLMError):
    """Временная ошибка LLM."""

    def __init__(self, message: str = "Temporary LLM error", original_error: Exception = None):
        super().__init__(message, error_type="temporary", retryable=True, original_error=original_error)


class CodeValidationError(TestGeneratorError):
    """Ошибка валидации сгенерированного кода."""

    pass


class OutputError(TestGeneratorError):
    """Ошибка сохранения файлов."""

    pass


class RepositoryConnectionError(TestGeneratorError):
    """Ошибка подключения к репозиторию."""

    pass


class RepositoryIndexError(TestGeneratorError):
    """Ошибка индексации репозитория."""

    pass

