"""Управление файлами."""

from pathlib import Path
from typing import List

from test_generator.models import GeneratedFile
from test_generator.utils.exceptions import OutputError
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """Менеджер файлов для сохранения сгенерированного кода."""

    @staticmethod
    def save_files(
        files: List[GeneratedFile],
        output_dir: Path,
        overwrite: bool = False,
    ) -> Path:
        """
        Сохраняет файлы в директорию.

        Args:
            files: Список файлов для сохранения
            output_dir: Директория для сохранения
            overwrite: Перезаписывать существующие файлы

        Returns:
            Путь к директории с сохраненными файлами

        Raises:
            OutputError: При ошибках сохранения
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            file_path = output_dir / file.path

            # Проверка существования
            if file_path.exists() and not overwrite:
                raise OutputError(f"Файл уже существует: {file_path}")

            # Создание директорий
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Сохранение
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file.content)

                logger.debug(f"Файл сохранен: {file_path} ({file.size_bytes} байт)")
            except Exception as e:
                raise OutputError(f"Ошибка сохранения файла {file_path}: {e}") from e

        logger.info(f"Сохранено {len(files)} файлов в {output_dir}")
        return output_dir

