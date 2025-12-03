"""Форматирование кода."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from test_generator.utils.exceptions import OutputError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class CodeFormatter:
    """Форматировщик кода."""

    @staticmethod
    def format_code(code: str, style: str = "black") -> str:
        """
        Форматирует код согласно стилю.

        Args:
            code: Исходный код
            style: Стиль форматирования (black, ruff, autopep8)

        Returns:
            Отформатированный код

        Raises:
            OutputError: При ошибках форматирования
        """
        if style == "black":
            return CodeFormatter._format_with_black(code)
        elif style == "ruff":
            return CodeFormatter._format_with_ruff(code)
        elif style == "autopep8":
            return CodeFormatter._format_with_autopep8(code)
        else:
            logger.warning(f"Неизвестный стиль форматирования: {style}, возвращаю исходный код")
            return code

    @staticmethod
    def _format_with_black(code: str) -> str:
        """Форматирует код с помощью black."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                ["black", "--quiet", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(temp_path, "r", encoding="utf-8") as f:
                    formatted = f.read()
                Path(temp_path).unlink()
                return formatted
            else:
                logger.warning(f"Black вернул ошибку: {result.stderr}")
                Path(temp_path).unlink()
                return code

        except FileNotFoundError:
            logger.warning("Black не установлен, пропускаю форматирование")
            return code
        except Exception as e:
            logger.error(f"Ошибка форматирования black: {e}")
            return code

    @staticmethod
    def _format_with_ruff(code: str) -> str:
        """Форматирует код с помощью ruff."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                ["ruff", "format", temp_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(temp_path, "r", encoding="utf-8") as f:
                    formatted = f.read()
                Path(temp_path).unlink()
                return formatted
            else:
                logger.warning(f"Ruff вернул ошибку: {result.stderr}")
                Path(temp_path).unlink()
                return code

        except FileNotFoundError:
            logger.warning("Ruff не установлен, пропускаю форматирование")
            return code
        except Exception as e:
            logger.error(f"Ошибка форматирования ruff: {e}")
            return code

    @staticmethod
    def _format_with_autopep8(code: str) -> str:
        """Форматирует код с помощью autopep8."""
        try:
            import autopep8

            formatted = autopep8.fix_code(code)
            return formatted

        except ImportError:
            logger.warning("autopep8 не установлен, пропускаю форматирование")
            return code
        except Exception as e:
            logger.error(f"Ошибка форматирования autopep8: {e}")
            return code

