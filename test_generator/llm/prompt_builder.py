"""Построитель промптов для LLM."""

from typing import Optional, Dict, Any, List

from test_generator.models import TestCase, CodeStyle
from test_generator.repository.models import RepositoryIndex
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Построитель промптов для LLM."""

    def build_system_prompt(
        self,
        templates: Optional[Dict[str, Any]] = None,
        code_style: CodeStyle = CodeStyle.STANDARD,
    ) -> str:
        """
        Строит системный промпт.

        Args:
            templates: Шаблоны из репозитория
            code_style: Стиль кода

        Returns:
            Системный промпт
        """
        prompt = """Ты эксперт по автоматизации тестирования на Python.

Твоя задача - генерировать качественные автотесты UI с использованием:
- Playwright для взаимодействия с браузером
- Паттерна Page Object Model
- Библиотеки qautils (gpn_qa_utils) для работы с элементами
- Allure Report для отчетности

Требования к коду:
1. Используй классы из gpn_qa_utils.ui.page_factory (Button, Input, Link, Text и др.)
2. Page Object классы должны наследоваться от gpn_qa_utils.ui.pages.base.BasePage
3. Используй Allure декораторы (@allure.epic, @allure.feature, @allure.story, @allure.title)
4. Используй allure.step для шагов теста
5. Следуй корпоративным стандартам кодирования
6. Добавляй понятные комментарии
7. Используй осмысленные имена переменных и методов
"""

        if code_style == CodeStyle.VERBOSE:
            prompt += "\n8. Добавляй подробные комментарии и docstrings\n"
        elif code_style == CodeStyle.COMPACT:
            prompt += "\n8. Пиши компактный код без избыточных комментариев\n"

        return prompt

    def build_context_prompt(
        self,
        repository_index: Optional[RepositoryIndex] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Строит контекстный промпт с информацией о проекте.

        Args:
            repository_index: Индекс репозитория
            additional_context: Дополнительный контекст

        Returns:
            Контекстный промпт
        """
        prompt_parts = []

        # Информация из репозитория
        if repository_index:
            prompt_parts.append("Информация о структуре проекта:")

            # Структура проекта
            structure = repository_index.structure
            prompt_parts.append(f"- Тестовые директории: {len(structure.test_directories)}")
            prompt_parts.append(f"- Page Object директории: {len(structure.page_object_directories)}")

            # Паттерны именования
            naming = repository_index.naming_patterns
            prompt_parts.append(f"\nПаттерны именования:")
            prompt_parts.append(f"- Файлы: {naming.file_naming}")
            prompt_parts.append(f"- Классы: {naming.class_naming}")
            prompt_parts.append(f"- Функции: {naming.function_naming}")
            prompt_parts.append(f"- Префикс тестов: {naming.test_prefix}")
            prompt_parts.append(f"- Суффикс Page Objects: {naming.page_suffix}")

            # Паттерны кода
            code_patterns = repository_index.code_patterns
            prompt_parts.append(f"\nПаттерны кода:")
            prompt_parts.append(f"- Используется qautils: {code_patterns.uses_qautils}")
            prompt_parts.append(f"- Используется Allure: {code_patterns.uses_allure}")
            if code_patterns.base_page_class:
                prompt_parts.append(f"- Базовый класс Page: {code_patterns.base_page_class}")
            if code_patterns.browser_launcher:
                prompt_parts.append(f"- Browser Launcher: {code_patterns.browser_launcher}")

            # Примеры кода - полные шаблоны
            if repository_index.templates.page_object_template:
                prompt_parts.append("\n=== ШАБЛОН PAGE OBJECT КЛАССА (СТРОГО СЛЕДУЙ ЭТОМУ ФОРМАТУ) ===")
                prompt_parts.append("```python")
                prompt_parts.append(repository_index.templates.page_object_template)
                prompt_parts.append("```")
            
            if repository_index.templates.test_template:
                prompt_parts.append("\n=== ШАБЛОН ТЕСТОВОГО КЛАССА (СТРОГО СЛЕДУЙ ЭТОМУ ФОРМАТУ) ===")
                prompt_parts.append("```python")
                prompt_parts.append(repository_index.templates.test_template)
                prompt_parts.append("```")
            
            # Общие фрагменты кода
            if repository_index.templates.common_code_snippets:
                prompt_parts.append("\n=== ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ КОДА ===")
                for i, snippet in enumerate(repository_index.templates.common_code_snippets[:2], 1):
                    prompt_parts.append(f"\nПример {i}:")
                    prompt_parts.append("```python")
                    # Берем первые 80 строк каждого примера
                    lines = snippet.split("\n")[:80]
                    prompt_parts.extend(lines)
                    prompt_parts.append("```")

        # Дополнительный контекст
        if additional_context:
            if "api_contracts" in additional_context:
                prompt_parts.append("\nAPI контракты:")
                for name, contract in additional_context["api_contracts"].items():
                    prompt_parts.append(f"- {name}: {contract.get('type', 'unknown')}")

            if "selectors" in additional_context:
                prompt_parts.append("\nСелекторы элементов:")
                for page, selectors in additional_context["selectors"].items():
                    prompt_parts.append(f"- {page}: {len(selectors)} селекторов")

            if "code_samples" in additional_context:
                prompt_parts.append("\nПримеры кода доступны для анализа")

        if not prompt_parts:
            return ""

        return "\n".join(prompt_parts)

    def build_task_prompt(
        self,
        test_case: TestCase,
        page_objects_needed: List[str],
    ) -> str:
        """
        Строит задачный промпт для конкретного тест-кейса.

        Args:
            test_case: Тест-кейс
            page_objects_needed: Список необходимых Page Objects

        Returns:
            Задачный промпт
        """
        prompt = f"""Сгенерируй автотест на основе следующего тест-кейса:

ID: {test_case.id}
Название: {test_case.name}
Описание: {test_case.description or 'Нет описания'}
Уровень тестирования: {test_case.test_layer}
Браузер: {test_case.browser}

Epic: {test_case.epic or 'Не указан'}
Feature: {test_case.feature or 'Не указан'}
Story: {test_case.story or 'Не указан'}

Шаги теста:
"""

        for i, step in enumerate(test_case.steps, 1):
            prompt += f"""
Шаг {i} ({step.id}): {step.name}
Описание: {step.description}
Ожидаемый результат: {step.expected_result}
"""

        if page_objects_needed:
            prompt += f"\nНеобходимые Page Objects: {', '.join(page_objects_needed)}"

        prompt += f"""

КРИТИЧЕСКИ ВАЖНО: Строго следуй шаблонам из репозитория проекта!

1. PAGE OBJECT КЛАСС:
   - ИМПОРТЫ (в таком порядке):
     * import os
     * import allure
     * from dotenv import load_dotenv
     * from gpn_qa_utils.ui.page_factory.* (Button, Input, Link, Text и т.д.)
     * from gpn_qa_utils.ui.pages.base import BasePage
     * from playwright.sync_api import Page
   - В начале класса: load_dotenv()
   - super().__init__(page, url=os.getenv("AUTOTEST_BASE_URL")) или super().__init__(page)
   - Элементы определяй как self.element_name = Component(page, selector="...", allure_name="...")
   - Методы используй allure.step для действий

2. ТЕСТОВЫЙ КЛАСС:
   - Тесты должны быть в КЛАССЕ, а не как отдельные функции!
   - Имя класса: Test* (например, Test{test_case.id.replace('_', '')})
   - ИМПОРТЫ (в таком порядке):
     * import os
     * import allure
     * import pytest
     * from src.ui.pages.* import PageObjectClass (НЕ из pages.*!)
   - Класс должен иметь декораторы: @allure.epic("..."), @allure.feature("...")
   - Каждый тест должен иметь @allure.title("...")
   - Тесты принимают browser: Page или фикстуры страниц (main_page, login_page и т.д.)
   - НЕ используй прямые вызовы Playwright (expect, page.locator) - только методы Page Object!
   - Используй методы Page Object для всех действий и проверок

Формат ответа:
```python
# === PAGE OBJECT ===
[код Page Object класса строго по шаблону]

# === TEST CLASS ===
[код тестового класса строго по шаблону]
```

ТРЕБОВАНИЯ:
1. Строго следуй шаблонам из репозитория - они показаны выше
2. Page Object и тестовый класс должны быть в ОДНОМ ответе, но четко разделены
3. Используй ТОЛЬКО компоненты из gpn_qa_utils.ui.page_factory
4. НЕ используй прямые вызовы Playwright в тестах - только методы Page Object
5. Тесты должны быть в классе, а не как отдельные функции
6. Используй правильные импорты из src.ui.pages.*
7. Каждый тест должен иметь @allure.title
8. Класс тестов должен иметь @allure.epic и @allure.feature
"""

        return prompt

    def build_full_prompt(
        self,
        test_case: TestCase,
        repository_index: Optional[Any] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        code_style: CodeStyle = CodeStyle.STANDARD,
    ) -> Dict[str, str]:
        """
        Строит полный промпт для генерации.

        Args:
            test_case: Тест-кейс
            repository_index: Индекс репозитория
            additional_context: Дополнительный контекст
            custom_prompts: Кастомные промпты
            code_style: Стиль кода

        Returns:
            Словарь с ключами: system, context, task
        """
        # Использование кастомных промптов если есть
        if custom_prompts:
            system_prompt = custom_prompts.get("system") or self.build_system_prompt(
                code_style=code_style
            )
        else:
            system_prompt = self.build_system_prompt(code_style=code_style)

        context_prompt = self.build_context_prompt(repository_index, additional_context)

        # Определение необходимых Page Objects
        page_objects_needed = self._extract_page_objects(test_case)
        task_prompt = self.build_task_prompt(test_case, page_objects_needed)

        return {
            "system": system_prompt,
            "context": context_prompt,
            "task": task_prompt,
        }

    def _extract_page_objects(self, test_case: TestCase) -> List[str]:
        """
        Извлекает необходимые Page Objects из тест-кейса.

        Args:
            test_case: Тест-кейс

        Returns:
            Список названий Page Objects
        """
        page_objects = []
        # Простая эвристика: извлечение из описаний шагов
        for step in test_case.steps:
            # Можно добавить более сложную логику анализа
            if "страниц" in step.description.lower() or "page" in step.description.lower():
                # Попытка извлечь название страницы
                # Это упрощенная версия, в реальности нужен более сложный анализ
                pass

        return page_objects

