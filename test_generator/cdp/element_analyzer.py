"""Анализ элементов через CDP."""

from typing import Dict, Any, Optional, List

from test_generator.cdp.cdp_client import CDPClient
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class ElementAnalyzer:
    """Анализ элементов страницы через CDP."""

    def __init__(self, cdp_client: CDPClient):
        """
        Инициализация анализатора элементов.

        Args:
            cdp_client: CDP клиент
        """
        self.cdp_client = cdp_client

    def analyze_element(self, selector: str) -> Optional[Dict[str, Any]]:
        """
        Анализирует элемент по селектору.

        Args:
            selector: CSS селектор элемента

        Returns:
            Информация об элементе или None
        """
        if not self.cdp_client.page:
            return None

        try:
            element = self.cdp_client.page.query_selector(selector)
            if not element:
                return None

            # Получение информации об элементе
            info = element.evaluate(
                """
                (el) => {
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    return {
                        tagName: el.tagName.toLowerCase(),
                        id: el.id || null,
                        className: el.className || null,
                        name: el.name || null,
                        type: el.type || null,
                        textContent: el.textContent?.trim() || '',
                        innerHTML: el.innerHTML || '',
                        value: el.value || null,
                        href: el.href || null,
                        src: el.src || null,
                        alt: el.alt || null,
                        title: el.title || null,
                        ariaLabel: el.getAttribute('aria-label') || null,
                        ariaRole: el.getAttribute('role') || null,
                        ariaLabelledBy: el.getAttribute('aria-labelledby') || null,
                        dataAttributes: Object.fromEntries(
                            Array.from(el.attributes)
                                .filter(attr => attr.name.startsWith('data-'))
                                .map(attr => [attr.name, attr.value])
                        ),
                        position: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        },
                        styles: {
                            display: styles.display,
                            visibility: styles.visibility,
                            opacity: styles.opacity,
                            zIndex: styles.zIndex
                        },
                        isVisible: rect.width > 0 && rect.height > 0 && 
                                  styles.visibility !== 'hidden' && 
                                  styles.display !== 'none',
                        isEnabled: !el.disabled,
                        isRequired: el.required || false,
                        isReadOnly: el.readOnly || false
                    };
                }
                """
            )

            return info

        except Exception as e:
            logger.warning(f"Ошибка анализа элемента {selector}: {e}")
            return None

    def analyze_page_structure(self) -> Dict[str, Any]:
        """
        Анализирует структуру страницы.

        Returns:
            Информация о структуре страницы
        """
        if not self.cdp_client.page:
            return {}

        try:
            structure = self.cdp_client.page.evaluate(
                """
                () => {
                    const elements = {
                        buttons: document.querySelectorAll('button, [role="button"]').length,
                        links: document.querySelectorAll('a[href]').length,
                        inputs: document.querySelectorAll('input, textarea, select').length,
                        forms: document.querySelectorAll('form').length,
                        headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                        images: document.querySelectorAll('img').length,
                        tables: document.querySelectorAll('table').length,
                        lists: document.querySelectorAll('ul, ol').length
                    };
                    
                    return {
                        title: document.title,
                        url: window.location.href,
                        elements: elements,
                        totalElements: document.querySelectorAll('*').length
                    };
                }
                """
            )

            return structure

        except Exception as e:
            logger.error(f"Ошибка анализа структуры страницы: {e}")
            return {}

    def find_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Находит все интерактивные элементы на странице.

        Returns:
            Список интерактивных элементов
        """
        if not self.cdp_client.page:
            return []

        try:
            elements = self.cdp_client.page.evaluate(
                """
                () => {
                    const selectors = [
                        'button',
                        'a[href]',
                        'input:not([type="hidden"])',
                        'textarea',
                        'select',
                        '[role="button"]',
                        '[role="link"]',
                        '[onclick]',
                        '[tabindex]'
                    ];
                    
                    const found = [];
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                found.push({
                                    tagName: el.tagName.toLowerCase(),
                                    id: el.id || null,
                                    className: el.className || null,
                                    textContent: el.textContent?.trim() || '',
                                    type: el.type || null,
                                    role: el.getAttribute('role') || null,
                                    selector: selector,
                                    position: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height
                                    }
                                });
                            }
                        });
                    });
                    
                    return found;
                }
                """
            )

            return elements

        except Exception as e:
            logger.error(f"Ошибка поиска интерактивных элементов: {e}")
            return []

    def get_element_hierarchy(self, selector: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получает иерархию элементов от корня до указанного элемента.

        Args:
            selector: Селектор элемента

        Returns:
            Список элементов в иерархии
        """
        if not self.cdp_client.page:
            return None

        try:
            hierarchy = self.cdp_client.page.evaluate(
                """
                (selector) => {
                    const el = document.querySelector(selector);
                    if (!el) return null;
                    
                    const path = [];
                    let current = el;
                    
                    while (current && current !== document.body) {
                        const tag = current.tagName.toLowerCase();
                        const id = current.id ? `#${current.id}` : '';
                        const classes = current.className ? 
                            `.${current.className.split(' ').join('.')}` : '';
                        const selector = `${tag}${id}${classes}`;
                        
                        path.unshift({
                            tag: tag,
                            id: current.id || null,
                            className: current.className || null,
                            selector: selector
                        });
                        
                        current = current.parentElement;
                    }
                    
                    return path;
                }
                """,
                selector,
            )

            return hierarchy

        except Exception as e:
            logger.warning(f"Ошибка получения иерархии для {selector}: {e}")
            return None

