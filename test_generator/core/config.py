"""Конфигурация библиотеки."""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from test_generator.models import GenerationConfig, LLMConfig, RepositoryContext
from test_generator.utils.exceptions import ConfigError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """Менеджер конфигурации библиотеки."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        Инициализация конфигурации.

        Args:
            config_path: Путь к YAML файлу конфигурации
            config_dict: Словарь с конфигурацией (альтернатива config_path)

        Raises:
            ConfigError: При ошибках загрузки конфигурации
        """
        self.config_dict: Dict[str, Any] = {}

        if config_path:
            self._load_from_file(config_path)
        elif config_dict:
            self.config_dict = config_dict
        else:
            # Конфигурация по умолчанию
            self.config_dict = self._default_config()

        # Валидация конфигурации
        self._validate()

    def _load_from_file(self, config_path: str) -> None:
        """Загружает конфигурацию из YAML файла."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Файл конфигурации не найден: {config_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.config_dict = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Ошибка загрузки конфигурации: {e}") from e

    def _default_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию по умолчанию."""
        return {
            "llm": {
                "provider": "ollama",
                "ollama": {
                    "url": "http://localhost:11434",
                    "model": "codellama:13b",
                    "temperature": 0.3,
                    "max_tokens": 4000,
                    "timeout": 300,
                },
            },
            "generation": {
                "output_path": "./generated_tests",
                "overwrite_existing": False,
                "format_code": True,
                "validate_code": True,
            },
            "logging": {
                "level": "INFO",
            },
        }

    def _validate(self) -> None:
        """Валидирует конфигурацию."""
        # Базовая валидация структуры
        if not isinstance(self.config_dict, dict):
            raise ConfigError("Конфигурация должна быть словарем")

    def get_generation_config(self) -> GenerationConfig:
        """Возвращает конфигурацию генерации."""
        gen_config = self.config_dict.get("generation", {})

        # LLM конфигурация
        llm_config_dict = self.config_dict.get("llm", {})
        ollama_config = llm_config_dict.get("ollama", {})

        llm_config = LLMConfig(
            provider=llm_config_dict.get("provider", "ollama"),
            model=ollama_config.get("model", "codellama:13b"),
            temperature=ollama_config.get("temperature", 0.3),
            max_tokens=ollama_config.get("max_tokens", 4000),
            timeout=ollama_config.get("timeout", 300),
            max_retries=ollama_config.get("max_retries", 3),
            retry_delay=ollama_config.get("retry_delay", 1.0),
            url=ollama_config.get("url", "http://localhost:11434"),
        )

        return GenerationConfig(
            quality_level=gen_config.get("quality_level", "balanced"),
            code_style=gen_config.get("code_style", "standard"),
            include_comments=gen_config.get("include_comments", True),
            detail_level=gen_config.get("detail_level", "medium"),
            llm=llm_config,
            validate_code=gen_config.get("validate_code", True),
            format_code=gen_config.get("format_code", True),
            format_style=gen_config.get("format_style", "black"),
            overwrite_existing=gen_config.get("overwrite_existing", False),
            generate_page_objects=gen_config.get("generate_page_objects", True),
            generate_fixtures=gen_config.get("generate_fixtures", True),
            use_cdp=gen_config.get("use_cdp", False),
        )

    def get_repository_context(self) -> Optional[RepositoryContext]:
        """Возвращает контекст репозитория из конфигурации."""
        repo_config = self.config_dict.get("repository")
        if not repo_config:
            return None

        # Обработка переменных окружения для токенов
        auth_config = repo_config.get("auth", {})
        token = auth_config.get("token")
        if token and token.startswith("${") and token.endswith("}"):
            env_var = token[2:-1]
            token = os.getenv(env_var)

        # Построение repository_url из gitlab_url и project_path, если они указаны
        repository_url = repo_config.get("url")
        gitlab_url = repo_config.get("gitlab_url")
        project_path = repo_config.get("project_path")
        
        # Если указаны gitlab_url и project_path, собираем полный URL
        if gitlab_url and project_path and not repository_url:
            # Убираем .git из project_path если есть
            project_path_clean = project_path.rstrip(".git")
            # Убираем слэш в конце gitlab_url если есть
            gitlab_url_clean = gitlab_url.rstrip("/")
            repository_url = f"{gitlab_url_clean}/{project_path_clean}.git"
        
        return RepositoryContext(
            repository_url=repository_url,
            repository_type=repo_config.get("type", "gitlab"),
            gitlab_url=gitlab_url,
            project_path=project_path,
            auth_type=auth_config.get("type"),
            auth_token=token,
            ssh_key_path=Path(auth_config["ssh_key"]) if auth_config.get("ssh_key") else None,
            index_path=Path(repo_config["index_path"]) if repo_config.get("index_path") else None,
            auto_index=repo_config.get("auto_index", False),
            include_patterns=repo_config.get("include_patterns"),
            exclude_patterns=repo_config.get("exclude_patterns"),
            branch=repo_config.get("branch"),
            commit=repo_config.get("commit"),
        )

    def get_output_path(self) -> Path:
        """Возвращает путь для сохранения результатов."""
        output_path = self.config_dict.get("generation", {}).get("output_path", "./generated_tests")
        return Path(output_path)

    def get_logging_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию логирования."""
        return self.config_dict.get("logging", {})

