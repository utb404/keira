"""Нормализатор тест-кейсов."""

from test_generator.models import TestCase
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseNormalizer:
    """Нормализатор данных тест-кейсов."""

    @staticmethod
    def normalize(test_case: TestCase) -> TestCase:
        """
        Нормализует данные тест-кейса.

        Args:
            test_case: Тест-кейс для нормализации

        Returns:
            Нормализованный тест-кейс
        """
        # Нормализация строковых полей (удаление лишних пробелов)
        if test_case.description:
            test_case.description = test_case.description.strip()

        if test_case.preconditions:
            test_case.preconditions = test_case.preconditions.strip()

        # Нормализация шагов
        for step in test_case.steps:
            step.name = step.name.strip()
            step.description = step.description.strip()
            step.expected_result = step.expected_result.strip()

        logger.debug(f"Тест-кейс {test_case.id} нормализован")

        return test_case

