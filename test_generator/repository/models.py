"""Модели для индексации репозитория."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Тип файла в репозитории."""

    TEST = "test"
    PAGE_OBJECT = "page_object"
    FIXTURE = "fixture"
    CONFIG = "config"
    OTHER = "other"


class IndexedFile(BaseModel):
    """Индексированный файл."""

    path: Path = Field(..., description="Путь к файлу относительно корня репозитория")
    file_type: FileType = Field(..., description="Тип файла")
    content_hash: str = Field(..., description="Хеш содержимого для отслеживания изменений")
    size_bytes: int = Field(..., description="Размер файла в байтах")
    last_modified: Optional[datetime] = Field(default=None, description="Время последнего изменения")
    imports: List[str] = Field(default_factory=list, description="Список импортов")
    classes: List[str] = Field(default_factory=list, description="Список классов")
    functions: List[str] = Field(default_factory=list, description="Список функций")


class ProjectStructure(BaseModel):
    """Структура проекта."""

    root_path: Path = Field(..., description="Корневой путь проекта")
    test_directories: List[Path] = Field(default_factory=list, description="Директории с тестами")
    page_object_directories: List[Path] = Field(
        default_factory=list, description="Директории с Page Objects"
    )
    fixture_files: List[Path] = Field(default_factory=list, description="Файлы фикстур")
    config_files: List[Path] = Field(default_factory=list, description="Конфигурационные файлы")


class NamingPattern(BaseModel):
    """Паттерн именования."""

    file_naming: str = Field(default="snake_case", description="Стиль именования файлов")
    class_naming: str = Field(default="PascalCase", description="Стиль именования классов")
    function_naming: str = Field(default="snake_case", description="Стиль именования функций")
    test_prefix: str = Field(default="test_", description="Префикс тестовых функций")
    page_suffix: str = Field(default="Page", description="Суффикс Page Object классов")


class CodePatterns(BaseModel):
    """Паттерны кода."""

    uses_qautils: bool = Field(default=False, description="Используется ли qautils")
    uses_allure: bool = Field(default=False, description="Используется ли Allure")
    base_page_class: Optional[str] = Field(
        default=None, description="Базовый класс для Page Objects"
    )
    browser_launcher: Optional[str] = Field(
        default=None, description="Класс для запуска браузера"
    )
    common_imports: List[str] = Field(default_factory=list, description="Часто используемые импорты")
    common_decorators: List[str] = Field(
        default_factory=list, description="Часто используемые декораторы"
    )


class TemplateInfo(BaseModel):
    """Информация о шаблонах."""

    page_object_template: Optional[str] = Field(
        default=None, description="Шаблон Page Object класса"
    )
    test_template: Optional[str] = Field(default=None, description="Шаблон тестового метода")
    fixture_template: Optional[str] = Field(default=None, description="Шаблон фикстуры")
    common_code_snippets: List[str] = Field(
        default_factory=list, description="Общие фрагменты кода"
    )


class RepositoryIndex(BaseModel):
    """Индекс репозитория."""

    # Метаданные
    repository_url: Optional[str] = Field(default=None, description="URL репозитория")
    repository_path: Optional[Path] = Field(default=None, description="Локальный путь")
    indexed_at: datetime = Field(default_factory=datetime.now, description="Время индексации")
    version: str = Field(default="1.0", description="Версия индекса")

    # Структура
    structure: ProjectStructure = Field(..., description="Структура проекта")

    # Индексированные файлы
    files: List[IndexedFile] = Field(default_factory=list, description="Индексированные файлы")

    # Паттерны
    naming_patterns: NamingPattern = Field(
        default_factory=NamingPattern, description="Паттерны именования"
    )
    code_patterns: CodePatterns = Field(
        default_factory=CodePatterns, description="Паттерны кода"
    )
    templates: TemplateInfo = Field(default_factory=TemplateInfo, description="Шаблоны")

    # Статистика
    total_files: int = Field(default=0, description="Общее количество файлов")
    test_files_count: int = Field(default=0, description="Количество тестовых файлов")
    page_object_files_count: int = Field(default=0, description="Количество Page Object файлов")

    def get_test_files(self) -> List[IndexedFile]:
        """Возвращает список тестовых файлов."""
        return [f for f in self.files if f.file_type == FileType.TEST]

    def get_page_object_files(self) -> List[IndexedFile]:
        """Возвращает список Page Object файлов."""
        return [f for f in self.files if f.file_type == FileType.PAGE_OBJECT]

    def get_example_code(self, file_type: FileType, limit: int = 3) -> List[str]:
        """
        Возвращает примеры кода указанного типа.

        Args:
            file_type: Тип файла
            limit: Максимальное количество примеров

        Returns:
            Список путей к файлам-примерам
        """
        files = [f for f in self.files if f.file_type == file_type]
        return [str(f.path) for f in files[:limit]]

