"""Клиент для работы с Chrome DevTools Protocol."""

import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
except ImportError:
    Browser = None
    BrowserContext = None
    Page = None
    sync_playwright = None

from test_generator.utils.exceptions import LLMError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class CDPClient:
    """Клиент для работы с Chrome DevTools Protocol через Playwright."""

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        timeout: int = 30000,
    ):
        """
        Инициализация CDP клиента.

        Args:
            browser_type: Тип браузера (chromium, firefox, webkit)
            headless: Запуск в headless режиме
            timeout: Таймаут операций в миллисекундах
        """
        if sync_playwright is None:
            raise ImportError(
                "Playwright не установлен. Установите: pip install playwright && playwright install"
            )

        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cdp_session = None

    def start(self) -> None:
        """Запускает браузер и создает CDP сессию."""
        try:
            self.playwright = sync_playwright().start()
            browser_launcher = getattr(self.playwright, self.browser_type)

            self.browser = browser_launcher.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

            # Получение CDP сессии
            self.cdp_session = self.page.context.new_cdp_session(self.page)

            logger.info(f"CDP клиент запущен: {self.browser_type}, headless={self.headless}")

        except Exception as e:
            logger.error(f"Ошибка запуска CDP клиента: {e}", exc_info=True)
            raise LLMError(f"Не удалось запустить CDP клиент: {e}") from e

    def stop(self) -> None:
        """Останавливает браузер и закрывает CDP сессию."""
        try:
            if self.cdp_session:
                self.cdp_session.detach()
                self.cdp_session = None

            if self.page:
                self.page.close()
                self.page = None

            if self.context:
                self.context.close()
                self.context = None

            if self.browser:
                self.browser.close()
                self.browser = None

            if self.playwright:
                self.playwright.stop()
                self.playwright = None

            logger.info("CDP клиент остановлен")

        except Exception as e:
            logger.warning(f"Ошибка остановки CDP клиента: {e}")

    def navigate(self, url: str) -> None:
        """
        Переходит на указанный URL.

        Args:
            url: URL для перехода
        """
        if not self.page:
            raise RuntimeError("CDP клиент не запущен. Вызовите start()")

        try:
            self.page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            logger.debug(f"Переход на URL: {url}")
        except Exception as e:
            logger.error(f"Ошибка перехода на URL {url}: {e}")
            raise

    def get_dom_snapshot(self) -> Dict[str, Any]:
        """
        Получает снимок DOM через CDP.

        Returns:
            Словарь с информацией о DOM
        """
        if not self.cdp_session:
            raise RuntimeError("CDP сессия не создана")

        try:
            # Использование CDP команды для получения DOM
            result = self.cdp_session.send(
                "DOMSnapshot.captureSnapshot",
                {"computedStyles": [], "includePaintOrder": True, "includeDOMRects": True},
            )
            return result

        except Exception as e:
            logger.error(f"Ошибка получения DOM снимка: {e}")
            raise

    def get_document(self) -> Dict[str, Any]:
        """
        Получает документ через CDP.

        Returns:
            Информация о документе
        """
        if not self.cdp_session:
            raise RuntimeError("CDP сессия не создана")

        try:
            # Получение корневого узла документа
            result = self.cdp_session.send("DOM.getDocument", {"depth": -1})
            return result

        except Exception as e:
            logger.error(f"Ошибка получения документа: {e}")
            raise

    def query_selector(self, selector: str) -> Optional[Dict[str, Any]]:
        """
        Находит элемент по селектору через CDP.

        Args:
            selector: CSS селектор

        Returns:
            Информация об элементе или None
        """
        if not self.page:
            raise RuntimeError("CDP клиент не запущен")

        try:
            # Использование Playwright для поиска элемента
            element = self.page.query_selector(selector)
            if not element:
                return None

            # Получение информации об элементе через CDP
            node_id = element.evaluate("el => el.__playwright_node_id__")
            if not node_id:
                # Альтернативный способ через JavaScript
                node_id = element.evaluate(
                    """
                    el => {
                        const walker = document.createTreeWalker(
                            document,
                            NodeFilter.SHOW_ELEMENT
                        );
                        let node, index = 0;
                        while (node = walker.nextNode()) {
                            if (node === el) return index;
                            index++;
                        }
                        return -1;
                    }
                    """
                )

            # Получение атрибутов элемента
            attributes = element.evaluate(
                """
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
                """
            )

            return {
                "node_id": node_id,
                "selector": selector,
                "attributes": attributes,
                "tag_name": element.evaluate("el => el.tagName.toLowerCase()"),
                "text_content": element.evaluate("el => el.textContent?.trim() || ''"),
                "inner_html": element.evaluate("el => el.innerHTML"),
            }

        except Exception as e:
            logger.warning(f"Ошибка поиска элемента {selector}: {e}")
            return None

    def get_element_info(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию об элементе по node_id через CDP.

        Args:
            node_id: ID узла в DOM

        Returns:
            Информация об элементе
        """
        if not self.cdp_session:
            raise RuntimeError("CDP сессия не создана")

        try:
            # Получение атрибутов узла
            result = self.cdp_session.send("DOM.getAttributes", {"nodeId": node_id})
            attributes = result.get("attributes", [])

            # Преобразование в словарь
            attrs_dict = {}
            for i in range(0, len(attributes), 2):
                if i + 1 < len(attributes):
                    attrs_dict[attributes[i]] = attributes[i + 1]

            # Получение информации о узле
            node_info = self.cdp_session.send("DOM.describeNode", {"nodeId": node_id})

            return {
                "node_id": node_id,
                "attributes": attrs_dict,
                "node_info": node_info,
            }

        except Exception as e:
            logger.error(f"Ошибка получения информации об элементе {node_id}: {e}")
            return None

    def execute_cdp_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Выполняет произвольную CDP команду.

        Args:
            method: Название CDP метода
            params: Параметры команды

        Returns:
            Результат выполнения команды
        """
        if not self.cdp_session:
            raise RuntimeError("CDP сессия не создана")

        try:
            result = self.cdp_session.send(method, params or {})
            return result

        except Exception as e:
            logger.error(f"Ошибка выполнения CDP команды {method}: {e}")
            raise

    def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Ожидает появления элемента на странице.

        Args:
            selector: CSS селектор
            timeout: Таймаут в миллисекундах

        Returns:
            True если элемент появился
        """
        if not self.page:
            raise RuntimeError("CDP клиент не запущен")

        try:
            timeout = timeout or self.timeout
            self.page.wait_for_selector(selector, timeout=timeout)
            return True

        except Exception as e:
            logger.debug(f"Элемент {selector} не появился: {e}")
            return False

    def take_screenshot(self, path: Optional[Path] = None) -> Optional[bytes]:
        """
        Делает скриншот страницы.

        Args:
            path: Путь для сохранения скриншота

        Returns:
            Байты скриншота или None
        """
        if not self.page:
            raise RuntimeError("CDP клиент не запущен")

        try:
            screenshot = self.page.screenshot(path=path, full_page=True)
            return screenshot

        except Exception as e:
            logger.error(f"Ошибка создания скриншота: {e}")
            return None

    def __enter__(self):
        """Контекстный менеджер: вход."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        self.stop()

