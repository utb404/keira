"""Построитель структуры директорий."""

from pathlib import Path
from typing import List

from test_generator.models import GeneratedFile
from test_generator.utils.logger import get_logger

logger = get_logger(__name__)


class DirectoryBuilder:
    """Построитель структуры директорий для тестов."""

    @staticmethod
    def build_structure(output_dir: Path, files: List[GeneratedFile]) -> None:
        """
        Создает структуру директорий для файлов.

        Args:
            output_dir: Базовая директория
            files: Список файлов
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Создание стандартной структуры
        (output_dir / "pages").mkdir(exist_ok=True)
        (output_dir / "tests").mkdir(exist_ok=True)

        # Создание __init__.py файлов
        for init_dir in [output_dir, output_dir / "pages", output_dir / "tests"]:
            init_file = init_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("", encoding="utf-8")

        logger.debug(f"Структура директорий создана в {output_dir}")

