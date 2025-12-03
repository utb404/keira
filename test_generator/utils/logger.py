"""Настройка логирования."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any


def setup_logger(
    name: str = "test_generator",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Настраивает логгер для библиотеки.

    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов (опционально)
        format_string: Формат строки логирования (опционально)

    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Удаляем существующие обработчики
    logger.handlers.clear()

    # Формат по умолчанию
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик (если указан)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "test_generator") -> logging.Logger:
    """
    Получает логгер по имени.

    Args:
        name: Имя логгера

    Returns:
        Логгер
    """
    return logging.getLogger(name)

