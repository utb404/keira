"""Подключение к репозиторию."""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

try:
    import gitlab
    from git import Repo
except ImportError:
    gitlab = None
    Repo = None

from test_generator.models import RepositoryContext
from test_generator.utils.exceptions import RepositoryConnectionError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryConnector:
    """Управление подключением к репозиторию."""

    def __init__(self, context: RepositoryContext):
        """
        Инициализация коннектора.

        Args:
            context: Контекст репозитория
        """
        self.context = context
        self.local_path: Optional[Path] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

    def connect(self) -> Path:
        """
        Подключается к репозиторию и возвращает локальный путь.

        Returns:
            Локальный путь к репозиторию

        Raises:
            RepositoryConnectionError: При ошибках подключения
        """
        # Если указан локальный путь
        if self.context.repository_path:
            path = Path(self.context.repository_path)
            if path.exists() and (path / ".git").exists():
                self.local_path = path
                logger.info(f"Используется локальный репозиторий: {path}")
                return path
            else:
                raise RepositoryConnectionError(f"Локальный путь не является Git репозиторием: {path}")

        # Если указан URL
        if self.context.repository_url:
            return self._clone_repository()

        raise RepositoryConnectionError("Не указан ни URL, ни локальный путь к репозиторию")

    def _clone_repository(self) -> Path:
        """
        Клонирует репозиторий.

        Returns:
            Путь к клонированному репозиторию

        Raises:
            RepositoryConnectionError: При ошибках клонирования
        """
        if Repo is None:
            raise RepositoryConnectionError(
                "GitPython не установлен. Установите: pip install GitPython"
            )

        try:
            # Создание временной директории
            self._temp_dir = tempfile.TemporaryDirectory()
            temp_path = Path(self._temp_dir.name)

            # Подготовка URL для клонирования
            repo_url = self.context.repository_url
            
            # Если указаны gitlab_url и project_path, собираем URL
            if not repo_url and self.context.gitlab_url and self.context.project_path:
                gitlab_url_clean = self.context.gitlab_url.rstrip("/")
                project_path_clean = self.context.project_path.rstrip(".git")
                repo_url = f"{gitlab_url_clean}/{project_path_clean}.git"
            
            if not repo_url:
                raise RepositoryConnectionError("URL репозитория не указан (ни repository_url, ни gitlab_url+project_path)")

            # Аутентификация
            if self.context.auth_type == "token" and self.context.auth_token:
                # Добавление токена в URL
                if "gitlab" in repo_url.lower() or self.context.repository_type == "gitlab":
                    # GitLab: для личных токенов доступа используем oauth2:TOKEN
                    # Для токенов glpat- также работает формат oauth2:TOKEN
                    if repo_url.startswith("https://"):
                        parts = repo_url.replace("https://", "").split("/", 1)
                        if len(parts) == 2:
                            repo_url = f"https://oauth2:{self.context.auth_token}@{parts[0]}/{parts[1]}"
                        else:
                            # Если нет пути после домена, просто добавляем токен
                            repo_url = f"https://oauth2:{self.context.auth_token}@{parts[0]}"
                elif "github" in repo_url.lower():
                    # GitHub: https://TOKEN@github.com/...
                    if repo_url.startswith("https://"):
                        parts = repo_url.replace("https://", "").split("/", 1)
                        repo_url = f"https://{self.context.auth_token}@{parts[0]}/{parts[1]}"

            # Клонирование
            logger.info(f"Клонирование репозитория: {self.context.repository_url}")
            if self.context.auth_type == "token" and self.context.auth_token:
                logger.debug(f"Использование токена для аутентификации (URL изменен)")
            repo = Repo.clone_from(
                repo_url,
                temp_path,
                depth=1,  # Неглубокое клонирование для экономии времени
            )

            # Переключение на нужную ветку/коммит
            if self.context.branch:
                repo.git.checkout(self.context.branch)
            elif self.context.commit:
                repo.git.checkout(self.context.commit)

            self.local_path = temp_path
            logger.info(f"Репозиторий клонирован в: {temp_path}")

            return temp_path

        except Exception as e:
            logger.error(f"Ошибка клонирования репозитория: {e}", exc_info=True)
            raise RepositoryConnectionError(f"Не удалось клонировать репозиторий: {e}") from e

    def disconnect(self) -> None:
        """Отключается от репозитория и очищает временные файлы."""
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
                logger.debug("Временная директория очищена")
            except Exception as e:
                logger.warning(f"Ошибка очистки временной директории: {e}")

        self.local_path = None

    def get_local_path(self) -> Optional[Path]:
        """Возвращает локальный путь к репозиторию."""
        return self.local_path

    def __enter__(self):
        """Контекстный менеджер: вход."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        self.disconnect()

