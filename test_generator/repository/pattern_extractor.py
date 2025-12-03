"""Извлечение паттернов из репозитория."""

import re
from typing import List, Set

from test_generator.repository.models import RepositoryIndex, NamingPattern, CodePatterns
from test_generator.repository.indexer import RepositoryIndexer
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class PatternExtractor:
    """Извлечение паттернов и шаблонов из индекса."""

    def extract_patterns(self, index: RepositoryIndex) -> RepositoryIndex:
        """
        Извлекает паттерны из индекса.

        Args:
            index: Индекс репозитория

        Returns:
            Обновленный индекс с паттернами
        """
        logger.info("Извлечение паттернов из индекса...")

        # Извлечение паттернов именования
        naming_patterns = self._extract_naming_patterns(index)
        index.naming_patterns = naming_patterns

        # Извлечение паттернов кода
        code_patterns = self._extract_code_patterns(index)
        index.code_patterns = code_patterns

        logger.info("Паттерны извлечены")
        return index

    def _extract_naming_patterns(self, index: RepositoryIndex) -> NamingPattern:
        """
        Извлекает паттерны именования.

        Args:
            index: Индекс репозитория

        Returns:
            Паттерны именования
        """
        patterns = NamingPattern()

        # Анализ имен файлов
        file_names = [f.path.name for f in index.files if f.path.suffix == ".py"]
        if file_names:
            patterns.file_naming = self._detect_naming_style(file_names[0])

        # Анализ имен классов
        all_classes = []
        for file in index.files:
            all_classes.extend(file.classes)

        if all_classes:
            patterns.class_naming = self._detect_class_naming_style(all_classes[0])

        # Анализ имен функций
        all_functions = []
        for file in index.files:
            all_functions.extend(file.functions)

        if all_functions:
            patterns.function_naming = self._detect_function_naming_style(all_functions[0])

        # Определение префикса тестов
        test_functions = []
        for file in index.get_test_files():
            test_functions.extend([f for f in file.functions if "test" in f.lower()])

        if test_functions:
            # Ищем общий префикс
            prefixes = ["test_", "test", "test_"]
            for prefix in prefixes:
                if any(f.startswith(prefix) for f in test_functions):
                    patterns.test_prefix = prefix
                    break

        # Определение суффикса Page Objects
        page_classes = []
        for file in index.get_page_object_files():
            page_classes.extend([c for c in file.classes if "page" in c.lower()])

        if page_classes:
            # Ищем общий суффикс
            suffixes = ["Page", "PageObject", "PO"]
            for suffix in suffixes:
                if any(c.endswith(suffix) for c in page_classes):
                    patterns.page_suffix = suffix
                    break

        return patterns

    def _extract_code_patterns(self, index: RepositoryIndex) -> CodePatterns:
        """
        Извлекает паттерны кода.

        Args:
            index: Индекс репозитория

        Returns:
            Паттерны кода
        """
        patterns = CodePatterns()

        # Проверка использования qautils
        qautils_imports = [
            "gpn_qa_utils",
            "qautils",
            "gpn_qa_utils.ui",
            "gpn_qa_utils.ui.pages",
            "gpn_qa_utils.ui.page_factory",
        ]

        for file in index.files:
            for imp in file.imports:
                if any(qa_import in imp for qa_import in qautils_imports):
                    patterns.uses_qautils = True
                    break

            # Поиск базового класса Page
            if "BasePage" in " ".join(file.imports):
                patterns.base_page_class = "BasePage"

            # Поиск BrowserLauncher
            if "BrowserLauncher" in " ".join(file.imports):
                patterns.browser_launcher = "BrowserLauncher"

        # Проверка использования Allure
        allure_imports = ["allure", "allure_commons"]
        for file in index.files:
            if any(imp.startswith("allure") for imp in file.imports):
                patterns.uses_allure = True
                break

        # Часто используемые импорты
        import_counts = {}
        for file in index.files:
            for imp in file.imports:
                import_counts[imp] = import_counts.get(imp, 0) + 1

        # Топ-10 импортов
        common_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        patterns.common_imports = [imp for imp, _ in common_imports]

        # Поиск декораторов
        decorators = set()
        for file in index.files:
            # Простой поиск декораторов в содержимом
            # В реальности нужно парсить AST более детально
            if "@" in str(file.path):
                # Это упрощение, в реальности нужно анализировать код
                pass

        patterns.common_decorators = list(decorators)

        return patterns

    def _detect_naming_style(self, name: str) -> str:
        """Определяет стиль именования файла."""
        if "_" in name:
            return "snake_case"
        elif "-" in name:
            return "kebab-case"
        elif name.islower():
            return "lowercase"
        else:
            return "mixed"

    def _detect_class_naming_style(self, name: str) -> str:
        """Определяет стиль именования класса."""
        if name[0].isupper() and "_" not in name:
            return "PascalCase"
        elif name[0].isupper() and "_" in name:
            return "Pascal_Case"
        else:
            return "mixed"

    def _detect_function_naming_style(self, name: str) -> str:
        """Определяет стиль именования функции."""
        if "_" in name:
            return "snake_case"
        elif name[0].isupper():
            return "PascalCase"
        else:
            return "camelCase"

