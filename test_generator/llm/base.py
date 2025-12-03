"""Базовый класс для LLM провайдеров."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """Абстрактный базовый класс для провайдеров LLM."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        Генерирует ответ на основе промпта.

        Args:
            prompt: Основной промпт
            system_prompt: Системный промпт
            temperature: Температура генерации
            max_tokens: Максимум токенов
            **kwargs: Дополнительные параметры

        Returns:
            Сгенерированный текст

        Raises:
            LLMError: При ошибках работы с LLM
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Генерирует структурированный ответ (JSON).

        Args:
            prompt: Промпт
            response_format: Схема ожидаемого ответа
            **kwargs: Дополнительные параметры

        Returns:
            Структурированный ответ
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность провайдера."""
        pass

