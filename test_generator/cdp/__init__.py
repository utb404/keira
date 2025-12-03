"""Модуль интеграции с CDP."""

from test_generator.cdp.cdp_client import CDPClient
from test_generator.cdp.selector_extractor import SelectorExtractor
from test_generator.cdp.element_analyzer import ElementAnalyzer

__all__ = ["CDPClient", "SelectorExtractor", "ElementAnalyzer"]
