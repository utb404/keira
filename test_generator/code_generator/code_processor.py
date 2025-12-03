"""Обработчик сгенерированного кода."""

import re
from typing import Dict, Any

from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class CodeProcessor:
    """Обработчик кода, сгенерированного LLM."""

    @staticmethod
    def extract_code_from_markdown(response: str) -> str:
        """
        Извлекает код из markdown блоков.

        Args:
            response: Ответ от LLM

        Returns:
            Извлеченный код (может содержать несколько блоков)
        """
        # Удаление markdown блоков кода
        code_pattern = r"```(?:python)?\s*\n(.*?)```"
        matches = re.findall(code_pattern, response, re.DOTALL)

        if matches:
            # Объединяем все блоки кода
            code_blocks = [match.strip() for match in matches]
            code = "\n\n".join(code_blocks)
            logger.debug(f"Извлечено {len(matches)} блоков кода, общая длина: {len(code)} символов")
            return code

        # Проверка наличия маркеров разделения
        if "=== PAGE OBJECT ===" in response or "=== TEST" in response:
            # Извлекаем код между маркерами
            page_object_match = re.search(r"=== PAGE OBJECT ===\s*\n(.*?)(?=\n===|$)", response, re.DOTALL)
            test_match = re.search(r"=== TEST.*?===\s*\n(.*?)(?=\n===|$)", response, re.DOTALL)
            
            parts = []
            if page_object_match:
                parts.append(page_object_match.group(1).strip())
            if test_match:
                parts.append(test_match.group(1).strip())
            
            if parts:
                code = "\n\n".join(parts)
                logger.debug(f"Извлечен код по маркерам, длина: {len(code)} символов")
                return code

        # Если нет markdown блоков, возвращаем как есть
        return response.strip()

    @staticmethod
    def normalize_imports(code: str) -> str:
        """
        Нормализует импорты в коде: удаляет дубликаты и сортирует.

        Args:
            code: Исходный код

        Returns:
            Код с нормализованными импортами
        """
        lines = code.split("\n")
        import_lines = []
        other_lines = []
        seen_imports = set()
        in_imports = True

        for line in lines:
            stripped = line.strip()
            if in_imports and (stripped.startswith("import ") or stripped.startswith("from ")):
                # Удаляем дубликаты
                import_key = stripped.split(" as ")[0].split(" import ")[0] if " as " in stripped or " import " in stripped else stripped
                if import_key not in seen_imports:
                    import_lines.append(line)
                    seen_imports.add(import_key)
            else:
                if in_imports and stripped and not stripped.startswith("#"):
                    in_imports = False
                other_lines.append(line)

        # Сортировка импортов по группам:
        # 1. Стандартная библиотека (os, sys и т.д.)
        # 2. Сторонние библиотеки (allure, pytest, dotenv)
        # 3. Локальные импорты (from src..., from pages...)
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for imp in import_lines:
            stripped = imp.strip()
            if stripped.startswith("import os") or stripped.startswith("import sys"):
                stdlib_imports.append(imp)
            elif stripped.startswith("import allure") or stripped.startswith("import pytest") or stripped.startswith("from dotenv"):
                third_party_imports.append(imp)
            elif stripped.startswith("from gpn_qa_utils") or stripped.startswith("from playwright"):
                third_party_imports.append(imp)
            elif stripped.startswith("from src") or stripped.startswith("from pages"):
                local_imports.append(imp)
            else:
                third_party_imports.append(imp)
        
        # Объединение в правильном порядке
        all_imports = stdlib_imports + third_party_imports + local_imports
        
        # Объединение
        normalized = "\n".join(all_imports)
        if all_imports and other_lines:
            normalized += "\n\n"
        normalized += "\n".join(other_lines)

        return normalized

    @staticmethod
    def validate_syntax(code: str) -> bool:
        """
        Проверяет синтаксис Python кода.

        Args:
            code: Код для проверки

        Returns:
            True если синтаксис валиден
        """
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError as e:
            logger.error(f"Синтаксическая ошибка: {e}")
            return False

