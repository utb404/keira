"""Провайдер Ollama для LLM."""

import json
import time
from typing import Dict, Any, Optional

try:
    import ollama
except ImportError:
    ollama = None

from test_generator.llm.base import LLMProvider
from test_generator.models import LLMConfig
from test_generator.utils.exceptions import LLMError, LLMTimeoutError, LLMTemporaryError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Провайдер для Ollama (локальный и удаленный)."""

    def __init__(
        self,
        url: str = "http://localhost:11434",
        model: str = "codellama:13b",
        timeout: int = 300,
        max_retries: int = 3,
    ):
        """
        Инициализация Ollama провайдера.

        Args:
            url: URL Ollama сервера
            model: Модель для использования
            timeout: Таймаут запроса
            max_retries: Максимум повторов
        """
        if ollama is None:
            raise ImportError(
                "Библиотека ollama не установлена. Установите её: pip install ollama"
            )

        self.url = url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = None

        self._init_client()

    def _init_client(self) -> None:
        """Инициализирует клиент Ollama."""
        try:
            # Ollama клиент автоматически использует переменную окружения OLLAMA_HOST
            # или значение по умолчанию http://localhost:11434
            if self.url != "http://localhost:11434":
                import os
                os.environ["OLLAMA_HOST"] = self.url

            self.client = ollama.Client(host=self.url)
            logger.info(f"Ollama провайдер инициализирован: {self.url}, модель: {self.model}")
        except Exception as e:
            logger.error(f"Ошибка инициализации Ollama клиента: {e}")
            raise LLMError(f"Не удалось инициализировать Ollama клиент: {e}") from e

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        Генерирует ответ через Ollama.

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
        if not self.is_available():
            raise LLMError("Ollama провайдер недоступен")

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()

                # Подготовка параметров
                options = {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
                options.update(kwargs)

                # Генерация
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options=options,
                )

                response_time = (time.time() - start_time) * 1000

                if "message" in response and "content" in response["message"]:
                    content = response["message"]["content"]
                    logger.debug(
                        f"Ollama ответ получен за {response_time:.2f}мс, "
                        f"длина: {len(content)} символов"
                    )
                    return content
                else:
                    raise LLMError(f"Неожиданный формат ответа от Ollama: {response}")

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"Ошибка генерации (попытка {attempt + 1}/{self.max_retries}): {e}. "
                        f"Повтор через {delay}с"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Ошибка генерации после {self.max_retries} попыток: {e}")

        # Классификация ошибки
        if isinstance(last_error, TimeoutError):
            raise LLMTimeoutError(f"Таймаут запроса к Ollama: {last_error}", original_error=last_error)
        elif isinstance(last_error, ConnectionError):
            raise LLMTemporaryError(
                f"Ошибка подключения к Ollama: {last_error}",
                original_error=last_error,
            )
        else:
            raise LLMError(f"Ошибка генерации через Ollama: {last_error}", original_error=last_error)

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
        # Добавляем инструкцию по формату JSON в промпт
        json_prompt = f"""{prompt}

Верни ответ в формате JSON согласно следующей схеме:
{json.dumps(response_format, indent=2, ensure_ascii=False)}
"""

        response = self.generate(prompt=json_prompt, **kwargs)

        # Парсинг JSON из ответа
        try:
            # Извлечение JSON из markdown блоков если есть
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа: {e}\nОтвет: {response[:500]}")
            raise LLMError(f"Не удалось распарсить JSON ответ: {e}") from e

    def is_available(self) -> bool:
        """Проверяет доступность Ollama."""
        try:
            if self.client is None:
                return False

            # Проверка доступности через список моделей
            models = self.client.list()
            return models is not None
        except Exception as e:
            logger.debug(f"Ollama недоступен: {e}")
            return False

