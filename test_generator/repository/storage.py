"""Хранение и загрузка индекса репозитория."""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from test_generator.repository.models import RepositoryIndex
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class IndexStorage:
    """Управление хранением индекса."""

    @staticmethod
    def save(index: RepositoryIndex, index_path: Path) -> None:
        """
        Сохраняет индекс в файл.

        Args:
            index: Индекс для сохранения
            index_path: Путь к файлу индекса
        """
        index_path = Path(index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # Конвертация в словарь для JSON
        index_dict = index.dict()

        # Конвертация Path в строки
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        index_dict = convert_paths(index_dict)

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Индекс сохранен: {index_path}")

    @staticmethod
    def load(index_path: Path) -> Optional[RepositoryIndex]:
        """
        Загружает индекс из файла.

        Args:
            index_path: Путь к файлу индекса

        Returns:
            Индекс или None если файл не существует
        """
        index_path = Path(index_path)
        if not index_path.exists():
            return None

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index_dict = json.load(f)

            # Конвертация строк обратно в Path
            def convert_paths_back(obj):
                if isinstance(obj, dict):
                    if "path" in obj and isinstance(obj["path"], str):
                        obj["path"] = Path(obj["path"])
                    return {k: convert_paths_back(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_paths_back(item) for item in obj]
                return obj

            index_dict = convert_paths_back(index_dict)

            index = RepositoryIndex.parse_obj(index_dict)
            logger.info(f"Индекс загружен: {index_path}")
            return index

        except Exception as e:
            logger.error(f"Ошибка загрузки индекса: {e}")
            return None

    @staticmethod
    def exists(index_path: Path) -> bool:
        """
        Проверяет существование индекса.

        Args:
            index_path: Путь к файлу индекса

        Returns:
            True если индекс существует
        """
        return Path(index_path).exists()

