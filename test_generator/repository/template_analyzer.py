"""Анализ шаблонов из репозитория."""

from pathlib import Path
from typing import List, Optional

from test_generator.repository.models import RepositoryIndex, TemplateInfo, FileType
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateAnalyzer:
    """Анализ корпоративных шаблонов."""

    def analyze_templates(self, index: RepositoryIndex, repo_path: Path) -> RepositoryIndex:
        """
        Анализирует шаблоны из индекса.

        Args:
            index: Индекс репозитория
            repo_path: Путь к репозиторию

        Returns:
            Обновленный индекс с шаблонами
        """
        logger.info("Анализ шаблонов...")

        templates = TemplateInfo()

        # Анализ Page Object шаблонов
        page_object_template = self._extract_page_object_template(index, repo_path)
        templates.page_object_template = page_object_template

        # Анализ тестовых шаблонов
        test_template = self._extract_test_template(index, repo_path)
        templates.test_template = test_template

        # Анализ шаблонов фикстур
        fixture_template = self._extract_fixture_template(index, repo_path)
        templates.fixture_template = fixture_template

        # Общие фрагменты кода
        common_snippets = self._extract_common_snippets(index, repo_path)
        templates.common_code_snippets = common_snippets

        index.templates = templates

        logger.info("Шаблоны проанализированы")
        return index

    def _extract_page_object_template(
        self, index: RepositoryIndex, repo_path: Path
    ) -> Optional[str]:
        """
        Извлекает шаблон Page Object класса.

        Args:
            index: Индекс репозитория
            repo_path: Путь к репозиторию

        Returns:
            Шаблон Page Object или None
        """
        page_files = index.get_page_object_files()
        if not page_files:
            return None

        # Берем первый Page Object файл как пример
        example_file = page_files[0]
        file_path = repo_path / example_file.path

        try:
            content = file_path.read_text(encoding="utf-8")
            # Возвращаем первые 500 строк как шаблон
            lines = content.split("\n")
            return "\n".join(lines[:500])
        except Exception as e:
            logger.warning(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def _extract_test_template(self, index: RepositoryIndex, repo_path: Path) -> Optional[str]:
        """
        Извлекает шаблон тестового метода.

        Args:
            index: Индекс репозитория
            repo_path: Путь к репозиторию

        Returns:
            Шаблон теста или None
        """
        test_files = index.get_test_files()
        if not test_files:
            return None

        # Берем первый тестовый файл как пример
        example_file = test_files[0]
        file_path = repo_path / example_file.path

        try:
            content = file_path.read_text(encoding="utf-8")
            # Возвращаем первые 300 строк как шаблон
            lines = content.split("\n")
            return "\n".join(lines[:300])
        except Exception as e:
            logger.warning(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def _extract_fixture_template(
        self, index: RepositoryIndex, repo_path: Path
    ) -> Optional[str]:
        """
        Извлекает шаблон фикстуры.

        Args:
            index: Индекс репозитория
            repo_path: Путь к репозиторию

        Returns:
            Шаблон фикстуры или None
        """
        fixture_files = [f for f in index.files if f.file_type == FileType.FIXTURE]
        if not fixture_files:
            return None

        # Берем первый файл фикстур
        example_file = fixture_files[0]
        file_path = repo_path / example_file.path

        try:
            content = file_path.read_text(encoding="utf-8")
            # Возвращаем первые 200 строк как шаблон
            lines = content.split("\n")
            return "\n".join(lines[:200])
        except Exception as e:
            logger.warning(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def _extract_common_snippets(
        self, index: RepositoryIndex, repo_path: Path
    ) -> List[str]:
        """
        Извлекает общие фрагменты кода.

        Args:
            index: Индекс репозитория
            repo_path: Путь к репозиторию

        Returns:
            Список общих фрагментов кода
        """
        snippets = []

        # Извлекаем примеры из разных типов файлов
        for file_type in [FileType.TEST, FileType.PAGE_OBJECT]:
            files = [f for f in index.files if f.file_type == file_type][:2]  # Берем 2 примера
            for file in files:
                try:
                    file_path = repo_path / file.path
                    content = file_path.read_text(encoding="utf-8")
                    # Берем первые 100 строк как пример
                    lines = content.split("\n")[:100]
                    snippets.append("\n".join(lines))
                except Exception:
                    pass

        return snippets

