"""Индексация репозитория."""

import hashlib
import ast
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime

from test_generator.repository.models import (
    RepositoryIndex,
    IndexedFile,
    ProjectStructure,
    FileType,
)
from test_generator.repository.connector import RepositoryConnector
from test_generator.models import RepositoryContext
from test_generator.utils.exceptions import RepositoryIndexError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryIndexer:
    """Индексация файлов и структуры репозитория."""

    def __init__(self, connector: RepositoryConnector):
        """
        Инициализация индексатора.

        Args:
            connector: Коннектор к репозиторию
        """
        self.connector = connector

    def index(
        self,
        context: RepositoryContext,
        force: bool = False,
        incremental: bool = True,
    ) -> RepositoryIndex:
        """
        Индексирует репозиторий.

        Args:
            context: Контекст репозитория
            force: Принудительная переиндексация
            incremental: Инкрементальное обновление

        Returns:
            Индекс репозитория

        Raises:
            RepositoryIndexError: При ошибках индексации
        """
        try:
            # Подключение к репозиторию
            repo_path = self.connector.get_local_path()
            if not repo_path:
                repo_path = self.connector.connect()

            logger.info(f"Начало индексации репозитория: {repo_path}")

            # Анализ структуры
            structure = self._analyze_structure(repo_path, context)

            # Индексация файлов
            files = self._index_files(repo_path, context, incremental)

            # Создание индекса
            index = RepositoryIndex(
                repository_url=context.repository_url,
                repository_path=Path(repo_path) if repo_path else None,
                structure=structure,
                files=files,
                total_files=len(files),
                test_files_count=len([f for f in files if f.file_type == FileType.TEST]),
                page_object_files_count=len(
                    [f for f in files if f.file_type == FileType.PAGE_OBJECT]
                ),
            )

            logger.info(
                f"Индексация завершена: {len(files)} файлов, "
                f"{index.test_files_count} тестов, {index.page_object_files_count} Page Objects"
            )

            return index

        except Exception as e:
            logger.error(f"Ошибка индексации репозитория: {e}", exc_info=True)
            raise RepositoryIndexError(f"Ошибка индексации: {e}") from e

    def _analyze_structure(
        self, repo_path: Path, context: RepositoryContext
    ) -> ProjectStructure:
        """
        Анализирует структуру проекта.

        Args:
            repo_path: Путь к репозиторию
            context: Контекст репозитория

        Returns:
            Структура проекта
        """
        repo_path = Path(repo_path)
        structure = ProjectStructure(root_path=repo_path)

        # Поиск директорий с тестами
        test_dirs = self._find_directories(repo_path, ["tests", "test", "autotests"])
        structure.test_directories = test_dirs

        # Поиск директорий с Page Objects
        page_dirs = self._find_directories(repo_path, ["pages", "page_objects", "page"])
        structure.page_object_directories = page_dirs

        # Поиск файлов фикстур
        fixture_files = list(repo_path.rglob("conftest.py"))
        structure.fixture_files = fixture_files

        # Поиск конфигурационных файлов
        config_files = []
        for pattern in ["pytest.ini", "setup.cfg", "pyproject.toml", "requirements.txt"]:
            config_files.extend(list(repo_path.rglob(pattern)))
        structure.config_files = config_files

        return structure

    def _find_directories(self, root: Path, names: List[str]) -> List[Path]:
        """
        Находит директории по именам.

        Args:
            root: Корневой путь
            names: Список имен для поиска

        Returns:
            Список найденных директорий
        """
        directories = []
        for name in names:
            found = list(root.rglob(name))
            directories.extend([d for d in found if d.is_dir()])
        return directories

    def _index_files(
        self,
        repo_path: Path,
        context: RepositoryContext,
        incremental: bool,
    ) -> List[IndexedFile]:
        """
        Индексирует файлы репозитория.

        Args:
            repo_path: Путь к репозиторию
            context: Контекст репозитория
            incremental: Инкрементальное обновление

        Returns:
            Список индексированных файлов
        """
        files = []
        repo_path = Path(repo_path)

        # Паттерны для поиска
        include_patterns = context.include_patterns or ["**/*.py"]
        exclude_patterns = context.exclude_patterns or [
            "**/__pycache__/**",
            "**/.git/**",
            "**/node_modules/**",
            "**/venv/**",
            "**/.venv/**",
        ]

        # Поиск файлов
        all_files = []
        for pattern in include_patterns:
            all_files.extend(repo_path.rglob(pattern))

        # Фильтрация
        for file_path in all_files:
            if not file_path.is_file():
                continue

            # Проверка исключений
            if any(
                self._match_pattern(str(file_path.relative_to(repo_path)), pattern)
                for pattern in exclude_patterns
            ):
                continue

            # Индексация файла
            try:
                indexed_file = self._index_file(file_path, repo_path)
                if indexed_file:
                    files.append(indexed_file)
            except Exception as e:
                logger.warning(f"Ошибка индексации файла {file_path}: {e}")

        return files

    def _index_file(self, file_path: Path, repo_path: Path) -> Optional[IndexedFile]:
        """
        Индексирует один файл.

        Args:
            file_path: Путь к файлу
            repo_path: Корневой путь репозитория

        Returns:
            Индексированный файл или None
        """
        try:
            # Чтение содержимого
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Определение типа файла
            file_type = self._determine_file_type(file_path, content)

            # Хеш содержимого
            content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

            # Парсинг AST для извлечения информации
            imports, classes, functions = self._parse_ast(content)

            # Относительный путь
            relative_path = file_path.relative_to(repo_path)

            # Время модификации
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            return IndexedFile(
                path=relative_path,
                file_type=file_type,
                content_hash=content_hash,
                size_bytes=len(content.encode("utf-8")),
                last_modified=last_modified,
                imports=imports,
                classes=classes,
                functions=functions,
            )

        except Exception as e:
            logger.debug(f"Ошибка индексации файла {file_path}: {e}")
            return None

    def _determine_file_type(self, file_path: Path, content: str) -> FileType:
        """
        Определяет тип файла.

        Args:
            file_path: Путь к файлу
            content: Содержимое файла

        Returns:
            Тип файла
        """
        name = file_path.name.lower()
        path_str = str(file_path).lower()

        # Тестовые файлы
        if "test_" in name or name.startswith("test") or "_test.py" in name:
            return FileType.TEST

        # Page Objects
        if "page" in path_str or "page_object" in path_str:
            if "class" in content and "BasePage" in content:
                return FileType.PAGE_OBJECT

        # Фикстуры
        if name == "conftest.py" or "fixture" in name:
            return FileType.FIXTURE

        # Конфигурационные файлы
        if name in ["pytest.ini", "setup.cfg", "pyproject.toml", "requirements.txt"]:
            return FileType.CONFIG

        return FileType.OTHER

    def _parse_ast(self, content: str) -> tuple[List[str], List[str], List[str]]:
        """
        Парсит AST для извлечения информации о коде.

        Args:
            content: Содержимое файла

        Returns:
            Кортеж (импорты, классы, функции)
        """
        imports = []
        classes = []
        functions = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except SyntaxError:
            # Игнорируем синтаксические ошибки
            pass

        return imports, classes, functions

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        Проверяет соответствие пути паттерну.

        Args:
            path: Путь для проверки
            pattern: Паттерн (поддерживает **)

        Returns:
            True если соответствует
        """
        # Простая реализация с поддержкой **
        import fnmatch

        # Нормализация путей
        path = path.replace("\\", "/")
        pattern = pattern.replace("\\", "/")

        return fnmatch.fnmatch(path, pattern)

