"""Парсер JSON тест-кейсов."""

import json
from pathlib import Path
from typing import Union, Dict, Any

from test_generator.models import TestCase
from test_generator.utils.exceptions import TestCaseParseError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseParser:
    """Парсер тест-кейсов из различных источников."""

    @staticmethod
    def parse(test_case: Union[TestCase, str, Path, Dict[str, Any]]) -> TestCase:
        """
        Парсит тест-кейс из различных форматов.

        Args:
            test_case: Тест-кейс в виде:
                - Объекта TestCase
                - Пути к JSON файлу (str или Path)
                - Словаря с данными
                - JSON строки

        Returns:
            Объект TestCase

        Raises:
            TestCaseParseError: При ошибках парсинга
        """
        try:
            # Если уже TestCase объект
            if isinstance(test_case, TestCase):
                return test_case

            # Если путь к файлу
            if isinstance(test_case, (str, Path)):
                path = Path(test_case)
                if path.exists() and path.is_file():
                    return TestCase.parse_file(path)
                # Если это JSON строка
                try:
                    return TestCase.parse_json(str(test_case))
                except (json.JSONDecodeError, ValueError):
                    raise TestCaseParseError(f"Не удалось распарсить тест-кейс: {test_case}")

            # Если словарь
            if isinstance(test_case, dict):
                return TestCase.parse_obj(test_case)

            raise TestCaseParseError(f"Неподдерживаемый тип тест-кейса: {type(test_case)}")

        except Exception as e:
            logger.error(f"Ошибка парсинга тест-кейса: {e}", exc_info=True)
            if isinstance(e, TestCaseParseError):
                raise
            raise TestCaseParseError(f"Ошибка парсинга тест-кейса: {e}") from e

