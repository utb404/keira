"""Извлечение селекторов через CDP."""

import re
from typing import List, Optional, Dict, Any, Tuple

from test_generator.cdp.cdp_client import CDPClient
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class SelectorExtractor:
    """Извлечение оптимальных селекторов для элементов."""

    def __init__(self, cdp_client: CDPClient):
        """
        Инициализация экстрактора селекторов.

        Args:
            cdp_client: CDP клиент
        """
        self.cdp_client = cdp_client

    def extract_selectors(
        self,
        element_description: str,
        page_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Извлекает селекторы для элемента по описанию.

        Args:
            element_description: Описание элемента (текст, роль, атрибуты)
            page_url: URL страницы (если нужно перейти)

        Returns:
            Список найденных селекторов с приоритетами
        """
        if page_url and self.cdp_client.page:
            self.cdp_client.navigate(page_url)

        selectors = []

        # Поиск по тексту
        text_selectors = self._find_by_text(element_description)
        selectors.extend(text_selectors)

        # Поиск по роли (ARIA)
        role_selectors = self._find_by_role(element_description)
        selectors.extend(role_selectors)

        # Поиск по атрибутам
        attribute_selectors = self._find_by_attributes(element_description)
        selectors.extend(attribute_selectors)

        # Сортировка по приоритету (стабильность)
        selectors.sort(key=lambda x: x.get("priority", 0), reverse=True)

        logger.info(f"Найдено {len(selectors)} селекторов для элемента: {element_description}")

        return selectors

    def _find_by_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Находит элементы по тексту.

        Args:
            text: Текст для поиска

        Returns:
            Список селекторов
        """
        selectors = []

        if not self.cdp_client.page:
            return selectors

        try:
            # Поиск по точному тексту
            exact_text = text.strip()
            xpath = f"//*[text()='{exact_text}']"
            element = self.cdp_client.page.query_selector(f"xpath={xpath}")

            if element:
                # Генерация селекторов
                selectors.extend(self._generate_selectors_for_element(element, priority=90))

            # Поиск по частичному тексту
            xpath_partial = f"//*[contains(text(), '{exact_text}')]"
            elements = self.cdp_client.page.query_selector_all(f"xpath={xpath_partial}")

            for element in elements[:3]:  # Ограничиваем количество
                selectors.extend(self._generate_selectors_for_element(element, priority=70))

        except Exception as e:
            logger.debug(f"Ошибка поиска по тексту: {e}")

        return selectors

    def _find_by_role(self, description: str) -> List[Dict[str, Any]]:
        """
        Находит элементы по ARIA роли.

        Args:
            description: Описание элемента

        Returns:
            Список селекторов
        """
        selectors = []

        if not self.cdp_client.page:
            return selectors

        # Определение роли из описания
        role_keywords = {
            "button": ["кнопка", "button", "btn"],
            "link": ["ссылка", "link", "a"],
            "input": ["поле", "input", "ввод"],
            "heading": ["заголовок", "heading", "h1", "h2", "h3"],
        }

        for role, keywords in role_keywords.items():
            if any(keyword.lower() in description.lower() for keyword in keywords):
                try:
                    elements = self.cdp_client.page.query_selector_all(f'[role="{role}"]')
                    for element in elements[:3]:
                        selectors.extend(self._generate_selectors_for_element(element, priority=85))
                except Exception as e:
                    logger.debug(f"Ошибка поиска по роли {role}: {e}")

        return selectors

    def _find_by_attributes(self, description: str) -> List[Dict[str, Any]]:
        """
        Находит элементы по атрибутам.

        Args:
            description: Описание элемента

        Returns:
            Список селекторов
        """
        selectors = []

        if not self.cdp_client.page:
            return selectors

        # Поиск по data-атрибутам
        try:
            # Извлечение возможных data-атрибутов из описания
            data_attrs = re.findall(r"data-[\w-]+", description.lower())
            for attr in data_attrs:
                elements = self.cdp_client.page.query_selector_all(f"[{attr}]")
                for element in elements[:2]:
                    selectors.extend(self._generate_selectors_for_element(element, priority=80))
        except Exception as e:
            logger.debug(f"Ошибка поиска по атрибутам: {e}")

        return selectors

    def _generate_selectors_for_element(
        self, element, priority: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Генерирует различные селекторы для элемента.

        Args:
            element: Элемент Playwright
            priority: Базовый приоритет

        Returns:
            Список селекторов
        """
        selectors = []

        try:
            # Получение информации об элементе
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            element_id = element.evaluate("el => el.id")
            class_names = element.evaluate("el => el.className")
            name_attr = element.evaluate("el => el.name")
            type_attr = element.evaluate("el => el.type")
            text_content = element.evaluate("el => el.textContent?.trim() || ''")
            aria_label = element.evaluate("el => el.getAttribute('aria-label') || ''")
            role = element.evaluate("el => el.getAttribute('role') || ''")

            # 1. ID селектор (высокий приоритет)
            if element_id:
                selectors.append(
                    {
                        "selector": f"#{element_id}",
                        "type": "id",
                        "strategy": "by_id",
                        "priority": priority + 20,
                        "value": element_id,
                        "description": f"Селектор по ID: {element_id}",
                    }
                )

            # 2. Name селектор
            if name_attr:
                selectors.append(
                    {
                        "selector": f"[name='{name_attr}']",
                        "type": "name",
                        "strategy": "by_name",
                        "priority": priority + 15,
                        "value": name_attr,
                        "description": f"Селектор по name: {name_attr}",
                    }
                )

            # 3. Class селектор (если класс уникален)
            if class_names:
                classes = class_names.split()
                if len(classes) == 1:
                    selectors.append(
                        {
                            "selector": f".{classes[0]}",
                            "type": "class",
                            "strategy": "by_class",
                            "priority": priority + 10,
                            "value": classes[0],
                            "description": f"Селектор по классу: {classes[0]}",
                        }
                    )

            # 4. ARIA label
            if aria_label:
                selectors.append(
                    {
                        "selector": f"[aria-label='{aria_label}']",
                        "type": "aria-label",
                        "strategy": "by_aria_label",
                        "priority": priority + 12,
                        "value": aria_label,
                        "description": f"Селектор по aria-label: {aria_label}",
                    }
                )

            # 5. Role селектор
            if role:
                selectors.append(
                    {
                        "selector": f"[role='{role}']",
                        "type": "role",
                        "strategy": "by_role",
                        "priority": priority + 8,
                        "value": role,
                        "description": f"Селектор по роли: {role}",
                    }
                )

            # 6. Текстовый селектор
            if text_content and len(text_content) < 50:
                selectors.append(
                    {
                        "selector": f"text={text_content}",
                        "type": "text",
                        "strategy": "by_text",
                        "priority": priority + 5,
                        "value": text_content,
                        "description": f"Селектор по тексту: {text_content}",
                    }
                )

            # 7. Комбинированный селектор (tag + class)
            if tag_name and class_names:
                classes = class_names.split()
                if classes:
                    combined = f"{tag_name}.{'.'.join(classes[:2])}"
                    selectors.append(
                        {
                            "selector": combined,
                            "type": "combined",
                            "strategy": "by_css",
                            "priority": priority + 3,
                            "value": combined,
                            "description": f"Комбинированный селектор: {combined}",
                        }
                    )

            # 8. XPath (низкий приоритет, но универсальный)
            xpath = self._generate_xpath(element)
            if xpath:
                selectors.append(
                    {
                        "selector": xpath,
                        "type": "xpath",
                        "strategy": "by_xpath",
                        "priority": priority - 5,
                        "value": xpath,
                        "description": f"XPath селектор: {xpath}",
                    }
                )

        except Exception as e:
            logger.warning(f"Ошибка генерации селекторов для элемента: {e}")

        return selectors

    def _generate_xpath(self, element) -> Optional[str]:
        """
        Генерирует XPath для элемента.

        Args:
            element: Элемент Playwright

        Returns:
            XPath строка или None
        """
        try:
            xpath = element.evaluate(
                """
                (el) => {
                    if (el.id !== '') {
                        return `//*[@id="${el.id}"]`;
                    }
                    if (el === document.body) {
                        return '/html/body';
                    }
                    let ix = 0;
                    const siblings = el.parentNode ? el.parentNode.childNodes : [];
                    for (let i = 0; i < siblings.length; i++) {
                        const sibling = siblings[i];
                        if (sibling === el) {
                            const tagName = el.tagName.toLowerCase();
                            return `/${tagName}[${ix + 1}]`;
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === el.tagName) {
                            ix++;
                        }
                    }
                    return null;
                }
                """
            )
            return xpath
        except Exception:
            return None

    def validate_selector(self, selector: str) -> Dict[str, Any]:
        """
        Валидирует селектор.

        Args:
            selector: Селектор для валидации

        Returns:
            Результат валидации
        """
        if not self.cdp_client.page:
            return {"valid": False, "error": "CDP клиент не запущен"}

        try:
            # Проверка существования элемента
            element = self.cdp_client.page.query_selector(selector)
            if not element:
                return {"valid": False, "error": "Элемент не найден"}

            # Проверка видимости
            is_visible = element.is_visible()
            is_enabled = element.is_enabled()

            return {
                "valid": True,
                "found": True,
                "visible": is_visible,
                "enabled": is_enabled,
                "selector": selector,
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

