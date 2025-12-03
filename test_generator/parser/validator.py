"""Валидатор тест-кейсов."""

from test_generator.models import TestCase
from test_generator.utils.exceptions import ValidationError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseValidator:
    """Валидатор тест-кейсов."""

    @staticmethod
    def validate(test_case: TestCase) -> None:
        """
        Валидирует тест-кейс.

        Args:
            test_case: Тест-кейс для валидации

        Raises:
            ValidationError: При ошибках валидации
        """
        errors = []

        # Проверка обязательных полей
        if not test_case.id:
            errors.append("ID тест-кейса обязателен")

        if not test_case.name:
            errors.append("Название тест-кейса обязательно")

        if not test_case.expected_result:
            errors.append("Ожидаемый результат обязателен")

        # Проверка шагов
        if not test_case.steps:
            errors.append("Тест-кейс должен содержать хотя бы один шаг")

        for i, step in enumerate(test_case.steps, 1):
            if not step.id:
                errors.append(f"Шаг {i}: ID шага обязателен")
            if not step.name:
                errors.append(f"Шаг {i}: Название шага обязательно")
            if not step.description:
                errors.append(f"Шаг {i}: Описание шага обязательно")

        if errors:
            error_msg = "Ошибки валидации тест-кейса:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValidationError(error_msg)

        logger.debug(f"Тест-кейс {test_case.id} успешно валидирован")

