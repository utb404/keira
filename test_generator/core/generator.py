"""Главный генератор автотестов."""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from test_generator.core.config import Config
from test_generator.models import (
    TestCase,
    TestStep,
    GenerationConfig,
    GenerationResult,
    GenerationStatus,
    GeneratedFile,
    LLMRequest,
    RepositoryContext,
    ValidationReport,
    ValidationLevel,
    ValidationIssue,
)
from test_generator.parser import TestCaseParser, TestCaseValidator, TestCaseNormalizer
from test_generator.llm import LLMProvider, OllamaProvider, PromptBuilder
from test_generator.code_generator import CodeProcessor, CodeFormatter
from test_generator.output import FileManager, DirectoryBuilder
from test_generator.utils.exceptions import (
    ConfigError,
    TestCaseParseError,
    LLMError,
    CodeValidationError,
    OutputError,
    RepositoryConnectionError,
    RepositoryIndexError,
)
from test_generator.utils.logger import setup_logger, get_logger
from test_generator.repository.models import RepositoryIndex
from test_generator.repository.connector import RepositoryConnector
from test_generator.repository.indexer import RepositoryIndexer
from test_generator.repository.pattern_extractor import PatternExtractor
from test_generator.repository.template_analyzer import TemplateAnalyzer
from test_generator.repository.storage import IndexStorage
from test_generator.cdp import CDPClient, SelectorExtractor, ElementAnalyzer


class TestGenerator:
    """
    Главный класс для генерации автотестов UI на основе тест-кейсов.

    Координирует работу всех компонентов: парсинг тест-кейсов, анализ репозитория,
    генерацию кода через LLM, валидацию и сохранение результатов.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[LLMProvider] = None,
        repository_context: Optional[RepositoryContext] = None,
    ) -> None:
        """
        Инициализация генератора тестов.

        Args:
            config_path: Путь к YAML конфигурационному файлу
            config_dict: Словарь с конфигурацией (альтернатива config_path)
            llm_provider: Кастомный провайдер LLM (опционально)
            repository_context: Контекст репозитория для анализа (опционально)

        Raises:
            ConfigError: При ошибках загрузки конфигурации
            ValidationError: При невалидной конфигурации
        """
        # Загрузка конфигурации
        self.config = Config(config_path=config_path, config_dict=config_dict)

        # Настройка логирования
        logging_config = self.config.get_logging_config()
        setup_logger(
            name="test_generator",
            level=logging_config.get("level", "INFO"),
            log_file=logging_config.get("file"),
            format_string=logging_config.get("format"),
        )
        self.logger = get_logger(__name__)

        # LLM провайдер
        if llm_provider:
            self.llm_provider = llm_provider
        else:
            llm_config = self.config.get_generation_config().llm
            self.llm_provider = OllamaProvider(
                url=llm_config.url or "http://localhost:11434",
                model=llm_config.model,
                timeout=llm_config.timeout,
                max_retries=llm_config.max_retries,
            )

        # Контекст репозитория
        self.repository_context = repository_context or self.config.get_repository_context()

        # Компоненты
        self.parser = TestCaseParser()
        self.validator = TestCaseValidator()
        self.normalizer = TestCaseNormalizer()
        self.prompt_builder = PromptBuilder()
        self.code_processor = CodeProcessor()
        self.code_formatter = CodeFormatter()
        self.file_manager = FileManager()
        self.directory_builder = DirectoryBuilder()

        # Индекс репозитория
        self._repository_index: Optional[RepositoryIndex] = None

        self.logger.info("TestGenerator инициализирован")

    def generate_test(
        self,
        test_case: Union[TestCase, str, Path, Dict[str, Any]],
        output_path: Optional[Union[str, Path]] = None,
        generation_config: Optional[GenerationConfig] = None,
        repository_context: Optional[RepositoryContext] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """
        Генерирует автотест на основе тест-кейса.

        Args:
            test_case: Тест-кейс в виде объекта TestCase, пути к JSON файлу,
                      словаря или строки с JSON
            output_path: Путь для сохранения сгенерированных файлов.
                        Если None, используется из конфигурации
            generation_config: Настройки генерации (переопределяют конфиг)
            repository_context: Контекст репозитория для анализа паттернов
            additional_context: Дополнительный контекст (API контракты, спецификации)

        Returns:
            GenerationResult: Результат генерации с метаданными

        Raises:
            TestCaseParseError: При ошибках парсинга тест-кейса
            LLMError: При ошибках работы с LLM
            CodeValidationError: При ошибках валидации сгенерированного кода
            OutputError: При ошибках сохранения файлов
        """
        start_time = time.time()

        # Инициализация результата
        result = GenerationResult(
            status=GenerationStatus.FAILED,
            success=False,
            test_case_id="",
            test_case_name="",
            generation_time_ms=0.0,
        )

        try:
            # Этап 1: Парсинг тест-кейса
            self.logger.info("Парсинг тест-кейса...")
            parsed_test_case = self.parser.parse(test_case)
            result.test_case_id = parsed_test_case.id
            result.test_case_name = parsed_test_case.name

            # Валидация
            self.validator.validate(parsed_test_case)

            # Нормализация
            parsed_test_case = self.normalizer.normalize(parsed_test_case)

            # Конфигурация генерации
            gen_config = generation_config or self.config.get_generation_config()

            # Контекст репозитория
            repo_context = repository_context or self.repository_context

            # Этап 2: Использование CDP для определения селекторов (если включено)
            cdp_selectors = {}
            if gen_config.use_cdp:
                self.logger.info("Использование CDP для определения селекторов...")
                cdp_selectors = self._extract_selectors_with_cdp(parsed_test_case)
                # Добавляем селекторы в дополнительный контекст
                if additional_context is None:
                    additional_context = {}
                if "selectors" not in additional_context:
                    additional_context["selectors"] = {}
                additional_context["selectors"].update(cdp_selectors)

            # Этап 3: Построение промптов
            self.logger.info("Построение промптов...")
            # Получение индекса репозитория
            repository_index = self.get_repository_index()
            prompts = self.prompt_builder.build_full_prompt(
                test_case=parsed_test_case,
                repository_index=repository_index,
                additional_context=additional_context,
                custom_prompts=gen_config.custom_prompts,
                code_style=gen_config.code_style,
            )

            # Этап 4: Генерация через LLM
            self.logger.info("Генерация кода через LLM...")
            llm_responses = self._generate_with_llm(
                prompts=prompts,
                llm_config=gen_config.llm,
                result=result,
            )

            # Этап 5: Пост-обработка ответов
            self.logger.info("Обработка сгенерированного кода...")
            processed_code = self._post_process_responses(llm_responses, parsed_test_case)

            # Этап 6: Генерация файлов
            self.logger.info("Создание файлов...")
            generated_files = self._generate_files(processed_code, parsed_test_case, gen_config)

            # Этап 7: Валидация
            if gen_config.validate_code:
                self.logger.info("Валидация кода...")
                validation_report = self._validate_code(generated_files, parsed_test_case)
                result.validation_report = validation_report

                if not validation_report.valid:
                    result.status = GenerationStatus.VALIDATION_ERROR
                    result.errors.extend([issue.message for issue in validation_report.errors])

            # Этап 8: Форматирование
            if gen_config.format_code:
                self.logger.info("Форматирование кода...")
                generated_files = self._format_files(generated_files, gen_config.format_style)

            # Этап 9: Сохранение
            self.logger.info("Сохранение файлов...")
            output_dir = output_path or self.config.get_output_path()
            output_dir = Path(output_dir)

            # Создание структуры директорий
            self.directory_builder.build_structure(output_dir, generated_files)

            # Сохранение файлов
            saved_dir = self.file_manager.save_files(
                files=generated_files,
                output_dir=output_dir,
                overwrite=gen_config.overwrite_existing,
            )

            # Успешное завершение
            result.status = GenerationStatus.SUCCESS
            result.success = True
            result.generated_files = generated_files
            result.output_directory = saved_dir

            self.logger.info(
                f"Генерация завершена успешно: {len(generated_files)} файлов, "
                f"время: {(time.time() - start_time) * 1000:.2f}мс"
            )

        except Exception as e:
            result.errors.append(str(e))
            self.logger.error(f"Ошибка генерации: {e}", exc_info=True)

        finally:
            result.generation_time_ms = (time.time() - start_time) * 1000

        return result

    def _generate_with_llm(
        self,
        prompts: Dict[str, str],
        llm_config: Any,
        result: GenerationResult,
    ) -> Dict[str, Any]:
        """
        Генерирует код через LLM.

        Args:
            prompts: Словарь промптов
            llm_config: Конфигурация LLM
            result: Результат генерации для записи метаданных

        Returns:
            Словарь с ответами LLM
        """
        responses = {}

        # Объединение промптов
        full_prompt = "\n\n".join(
            [
                prompts.get("system", ""),
                prompts.get("context", ""),
                prompts.get("task", ""),
            ]
        )

        try:
            start_time = time.time()
            response = self.llm_provider.generate(
                prompt=full_prompt,
                system_prompt=prompts.get("system"),
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
            response_time = (time.time() - start_time) * 1000

            # Запись метаданных
            llm_request = LLMRequest(
                prompt=full_prompt[:500],  # Первые 500 символов
                model=llm_config.model,
                temperature=llm_config.temperature,
                response_time_ms=response_time,
            )
            result.llm_requests.append(llm_request)

            responses["code"] = response

        except Exception as e:
            self.logger.error(f"Ошибка генерации через LLM: {e}")
            raise LLMError(f"Ошибка генерации через LLM: {e}") from e

        return responses

    def _post_process_responses(
        self,
        llm_responses: Dict[str, Any],
        test_case: TestCase,
    ) -> Dict[str, str]:
        """
        Пост-обработка ответов LLM.

        Args:
            llm_responses: Ответы от LLM
            test_case: Тест-кейс

        Returns:
            Обработанный код
        """
        processed = {}

        for key, response in llm_responses.items():
            # Логирование исходного ответа для отладки
            self.logger.debug(f"Исходный ответ LLM для {key} (первые 500 символов): {response[:500]}")
            
            # Извлечение кода из markdown
            code = self.code_processor.extract_code_from_markdown(response)
            self.logger.debug(f"Извлеченный код для {key} (длина: {len(code)} символов)")
            
            # Проверка наличия тестового класса в коде
            if "class Test" in code:
                self.logger.info("Обнаружен тестовый класс в сгенерированном коде")
            else:
                self.logger.warning("Тестовый класс не найден в сгенерированном коде")

            # Валидация синтаксиса
            if not self.code_processor.validate_syntax(code):
                raise CodeValidationError(f"Невалидный синтаксис в {key}")

            # Нормализация
            code = self.code_processor.normalize_imports(code)

            processed[key] = code

        return processed

    def _generate_files(
        self,
        processed_code: Dict[str, str],
        test_case: TestCase,
        config: GenerationConfig,
    ) -> List[GeneratedFile]:
        """
        Генерирует файлы из обработанного кода.

        Args:
            processed_code: Обработанный код
            test_case: Тест-кейс
            config: Конфигурация генерации

        Returns:
            Список сгенерированных файлов
        """
        files = []

        # Основной код теста
        if "code" in processed_code:
            code = processed_code["code"]
            self.logger.debug(f"Разделение кода на Page Object и тесты (общая длина: {len(code)} символов)")
            
            # Разделение кода на Page Object классы и тестовые функции
            page_object_code, test_code, imports = self._split_code(code, test_case)
            
            self.logger.info(f"Разделение завершено: Page Object ({len(page_object_code)} символов), "
                           f"Тесты ({len(test_code)} символов), Импорты ({len(imports)} символов)")
            
            # Генерация Page Object файла, если есть классы
            if page_object_code:
                # Извлечение имени класса
                import re
                match = re.search(r"class\s+(\w+Page)", page_object_code)
                class_name = match.group(1) if match else "Page"
                file_name = f"{class_name.lower()}.py"
                file_path = Path("pages") / file_name
                
                # Объединяем импорты и код Page Object
                full_page_code = imports + "\n\n" + page_object_code if imports else page_object_code
                
                files.append(
                    GeneratedFile(
                        path=file_path,
                        content=full_page_code,
                        file_type="page_object",
                        size_bytes=len(full_page_code.encode("utf-8")),
                    )
                )
            
            # Генерация тестового файла, если есть тестовые функции
            if test_code:
                file_name = f"test_{test_case.id.lower()}.py"
                file_path = Path("tests") / file_name
                
                # Объединяем импорты и тестовый код
                # Добавляем импорт Page Object, если он был создан
                if page_object_code:
                    match = re.search(r"class\s+(\w+Page)", page_object_code)
                    if match:
                        class_name = match.group(1)
                        page_import = f"from pages.{class_name.lower()} import {class_name}\n"
                        imports_with_page = (imports + "\n" + page_import) if imports else page_import
                    else:
                        imports_with_page = imports if imports else ""
                else:
                    imports_with_page = imports if imports else ""
                
                full_test_code = imports_with_page + "\n\n" + test_code if imports_with_page else test_code
                
                files.append(
                    GeneratedFile(
                        path=file_path,
                        content=full_test_code,
                        file_type="test",
                        size_bytes=len(full_test_code.encode("utf-8")),
                    )
                )

        return files
    
    def _split_code(self, code: str, test_case: TestCase) -> tuple[str, str, str]:
        """
        Разделяет код на Page Object классы, тестовые функции и импорты.
        
        Args:
            code: Исходный код
            test_case: Тест-кейс
            
        Returns:
            Кортеж (page_object_code, test_code, imports)
        """
        import ast
        import re
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Если не удалось распарсить, используем простую логику
            self.logger.warning("Не удалось распарсить код через AST, используется простая логика")
            return self._split_code_simple(code, test_case)
        
        imports_lines = []
        page_object_lines = []
        test_lines = []
        other_lines = []
        
        # Разделение на строки для сохранения форматирования
        code_lines = code.split("\n")
        current_section = "other"
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Импорты
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                for i in range(start_line, min(end_line, len(code_lines))):
                    if i not in [j for section in [imports_lines, page_object_lines, test_lines, other_lines] for j in section]:
                        imports_lines.append(i)
            
            elif isinstance(node, ast.ClassDef):
                # Классы - проверяем тип
                if node.name.startswith("Test"):
                    # Тестовый класс - включаем весь класс
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    for i in range(start_line, min(end_line, len(code_lines))):
                        if i not in imports_lines and i not in page_object_lines:
                            test_lines.append(i)
                elif "Page" in node.name:
                    # Page Object класс
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    for i in range(start_line, min(end_line, len(code_lines))):
                        if i not in imports_lines:
                            page_object_lines.append(i)
            
            elif isinstance(node, ast.FunctionDef):
                # Функции - проверяем, является ли это тестом (только если не в классе)
                if node.name.startswith("test_"):
                    # Проверяем родительский контекст
                    # Если функция на верхнем уровне (не в классе), добавляем в тесты
                    # Если в классе Test - уже добавлен с классом
                    # Если в классе Page - не добавляем
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    # Проверяем, не находится ли функция внутри Page Object класса
                    # Простая проверка: если перед функцией есть класс с Page в имени
                    found_page_class = False
                    for prev_i in range(max(0, start_line - 50), start_line):
                        if prev_i < len(code_lines):
                            prev_line = code_lines[prev_i].strip()
                            if prev_line.startswith("class ") and "Page" in prev_line and not prev_line.startswith("class Test"):
                                found_page_class = True
                                break
                    
                    if not found_page_class:
                        for i in range(start_line, min(end_line, len(code_lines))):
                            if i not in imports_lines and i not in page_object_lines and i not in test_lines:
                                test_lines.append(i)
        
        # Собираем код по секциям
        imports = "\n".join([code_lines[i] for i in sorted(set(imports_lines))])
        page_object_code = "\n".join([code_lines[i] for i in sorted(set(page_object_lines))])
        test_code = "\n".join([code_lines[i] for i in sorted(set(test_lines))])
        
        # Если не удалось разделить через AST, используем простую логику
        if not page_object_code and not test_code:
            return self._split_code_simple(code, test_case)
        
        return page_object_code, test_code, imports
    
    def _split_code_simple(self, code: str, test_case: TestCase) -> tuple[str, str, str]:
        """
        Простое разделение кода на основе регулярных выражений и маркеров.
        
        Args:
            code: Исходный код
            test_case: Тест-кейс
            
        Returns:
            Кортеж (page_object_code, test_code, imports)
        """
        import re
        
        # Проверка наличия маркеров разделения
        if "=== PAGE OBJECT ===" in code or "=== TEST FUNCTION ===" in code:
            return self._split_code_by_markers(code)
        
        lines = code.split("\n")
        imports = []
        page_object_lines = []
        test_lines = []
        other_lines = []
        
        in_page_class = False
        in_test_function = False
        current_indent = 0
        class_start_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Импорты
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(line)
                continue
            
            # Начало тестового класса
            if re.match(r"^class\s+Test", stripped):
                in_page_class = False
                in_test_function = True
                test_lines.append(line)
                class_start_indent = len(line) - len(line.lstrip())
                current_indent = class_start_indent
                continue
            
            # Начало класса Page Object
            if re.match(r"^class\s+\w+Page", stripped):
                in_page_class = True
                in_test_function = False
                page_object_lines.append(line)
                class_start_indent = len(line) - len(line.lstrip())
                current_indent = class_start_indent
                continue
            
            # Начало тестовой функции (только если не в классе)
            if re.match(r"^def\s+test_", stripped) and not in_page_class and not in_test_function:
                in_page_class = False
                in_test_function = True
                test_lines.append(line)
                current_indent = len(line) - len(line.lstrip())
                continue
            
            # Определение уровня вложенности
            indent = len(line) - len(line.lstrip())
            
            # Если мы внутри класса Page Object
            if in_page_class:
                # Конец класса - пустая строка после класса или новый класс/функция на том же уровне
                if (stripped == "" and indent <= class_start_indent) or \
                   (stripped and indent <= class_start_indent and 
                    (stripped.startswith("class ") or stripped.startswith("def ") or stripped.startswith("@"))):
                    # Конец класса
                    if re.match(r"^def\s+test_", stripped):
                        in_page_class = False
                        in_test_function = True
                        test_lines.append(line)
                    else:
                        in_page_class = False
                        if stripped.startswith("def test_"):
                            in_test_function = True
                            test_lines.append(line)
                        else:
                            other_lines.append(line)
                else:
                    page_object_lines.append(line)
                    if indent > current_indent:
                        current_indent = indent
                continue
            
            # Если мы внутри тестовой функции
            if in_test_function:
                # Конец функции - пустая строка или новая функция/класс
                if (stripped == "" and indent <= current_indent) or \
                   (stripped and indent <= current_indent and 
                    (stripped.startswith("def ") or stripped.startswith("class "))):
                    # Конец функции
                    in_test_function = False
                    if not stripped.startswith("def test_") and not stripped.startswith("class "):
                        other_lines.append(line)
                else:
                    test_lines.append(line)
                    if indent > current_indent:
                        current_indent = indent
                continue
            
            # Остальной код
            other_lines.append(line)
        
        imports_str = "\n".join(imports)
        page_object_code = "\n".join(page_object_lines) if page_object_lines else ""
        test_code = "\n".join(test_lines) if test_lines else ""
        
        return page_object_code, test_code, imports_str
    
    def _split_code_by_markers(self, code: str) -> tuple[str, str, str]:
        """
        Разделяет код по маркерам === PAGE OBJECT === и === TEST FUNCTION ===.
        
        Args:
            code: Исходный код
            
        Returns:
            Кортеж (page_object_code, test_code, imports)
        """
        import re
        
        lines = code.split("\n")
        imports = []
        page_object_lines = []
        test_lines = []
        
        in_page_section = False
        in_test_section = False
        
        for line in lines:
            stripped = line.strip()
            
            # Импорты (до разделителей)
            if not in_page_section and not in_test_section:
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(line)
                    continue
                elif "=== PAGE OBJECT ===" in stripped:
                    in_page_section = True
                    in_test_section = False
                    continue
                elif "=== TEST FUNCTION ===" in stripped:
                    in_page_section = False
                    in_test_section = True
                    continue
            
            # Разделители
            if "=== PAGE OBJECT ===" in stripped:
                in_page_section = True
                in_test_section = False
                continue
            elif "=== TEST FUNCTION ===" in stripped:
                in_page_section = False
                in_test_section = True
                continue
            
            # Добавление строк в соответствующие секции
            if in_page_section:
                page_object_lines.append(line)
            elif in_test_section:
                test_lines.append(line)
            elif not stripped.startswith("#") or "===" not in stripped:
                # Импорты, которые могут быть после разделителей
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(line)
        
        imports_str = "\n".join(imports)
        page_object_code = "\n".join(page_object_lines).strip()
        test_code = "\n".join(test_lines).strip()
        
        return page_object_code, test_code, imports_str

    def _format_files(
        self,
        files: List[GeneratedFile],
        format_style: Optional[str],
    ) -> List[GeneratedFile]:
        """
        Форматирует файлы.

        Args:
            files: Список файлов
            format_style: Стиль форматирования

        Returns:
            Отформатированные файлы
        """
        formatted_files = []

        for file in files:
            formatted_content = self.code_formatter.format_code(file.content, format_style or "black")
            formatted_files.append(
                GeneratedFile(
                    path=file.path,
                    content=formatted_content,
                    file_type=file.file_type,
                    size_bytes=len(formatted_content.encode("utf-8")),
                )
            )

        return formatted_files

    def _validate_code(
        self,
        files: List[GeneratedFile],
        test_case: TestCase,
    ) -> ValidationReport:
        """
        Валидирует сгенерированный код.

        Args:
            files: Список файлов
            test_case: Тест-кейс

        Returns:
            Отчет о валидации
        """
        issues = []

        for file in files:
            # Синтаксис
            if not self.code_processor.validate_syntax(file.content):
                issues.append(
                    ValidationIssue(
                        level="error",
                        message=f"Синтаксическая ошибка в {file.path}",
                        file=str(file.path),
                    )
                )

        errors = [i for i in issues if i.level == "error"]
        warnings = [i for i in issues if i.level == "warning"]
        info = [i for i in issues if i.level == "info"]

        return ValidationReport(
            valid=len(errors) == 0,
            validation_level=ValidationLevel.FULL,
            issues=issues,
            errors=errors,
            warnings=warnings,
            info=info,
            syntax_valid=len([i for i in errors if "syntax" in i.message.lower()]) == 0,
            imports_valid=True,  # TODO: реализовать проверку импортов
            structure_valid=True,  # TODO: реализовать проверку структуры
            test_case_match=None,  # TODO: реализовать проверку соответствия
        )

    def generate_tests_batch(
        self,
        test_cases: List[Union[TestCase, str, Path, Dict[str, Any]]],
        output_path: Optional[Union[str, Path]] = None,
        generation_config: Optional[GenerationConfig] = None,
        repository_context: Optional[RepositoryContext] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        parallel: bool = False,
    ) -> List[GenerationResult]:
        """
        Генерирует несколько автотестов пакетно.

        Args:
            test_cases: Список тест-кейсов
            output_path: Базовый путь для сохранения
            generation_config: Настройки генерации
            repository_context: Контекст репозитория
            additional_context: Дополнительный контекст
            parallel: Использовать параллельную генерацию (если поддерживается)

        Returns:
            Список результатов генерации
        """
        results = []

        for test_case in test_cases:
            result = self.generate_test(
                test_case=test_case,
                output_path=output_path,
                generation_config=generation_config,
                repository_context=repository_context,
                additional_context=additional_context,
            )
            results.append(result)

        return results

    def index_repository(
        self,
        repository_url: Optional[str] = None,
        repository_path: Optional[Union[str, Path]] = None,
        force: bool = False,
        incremental: bool = True,
    ) -> RepositoryIndex:
        """
        Индексирует репозиторий для извлечения паттернов и шаблонов.

        Args:
            repository_url: URL репозитория (GitLab или Git)
            repository_path: Локальный путь к репозиторию
            force: Принудительная переиндексация даже если индекс существует
            incremental: Инкрементальное обновление (только измененные файлы)

        Returns:
            RepositoryIndex: Индекс репозитория

        Raises:
            RepositoryConnectionError: При ошибках подключения
            RepositoryIndexError: При ошибках индексации
        """
        try:
            # Создание контекста репозитория
            if repository_url or repository_path:
                context = RepositoryContext(
                    repository_url=repository_url,
                    repository_path=Path(repository_path) if repository_path else None,
                )
            else:
                context = self.repository_context

            if not context:
                raise RepositoryConnectionError("Не указан контекст репозитория")

            # Проверка существующего индекса
            if not force and context.index_path and IndexStorage.exists(context.index_path):
                self.logger.info(f"Загрузка существующего индекса: {context.index_path}")
                index = IndexStorage.load(context.index_path)
                if index:
                    self._repository_index = index
                    return index

            # Индексация репозитория
            self.logger.info("Начало индексации репозитория...")

            # Подключение к репозиторию
            connector = RepositoryConnector(context)
            connector.connect()

            try:
                # Индексация
                indexer = RepositoryIndexer(connector)
                index = indexer.index(context, force=force, incremental=incremental)

                # Извлечение паттернов
                pattern_extractor = PatternExtractor()
                index = pattern_extractor.extract_patterns(index)

                # Анализ шаблонов
                repo_path = connector.get_local_path()
                if repo_path:
                    template_analyzer = TemplateAnalyzer()
                    index = template_analyzer.analyze_templates(index, repo_path)

                # Сохранение индекса
                if context.index_path:
                    IndexStorage.save(index, context.index_path)

                self._repository_index = index
                self.logger.info("Индексация завершена успешно")

                return index

            finally:
                connector.disconnect()

        except Exception as e:
            self.logger.error(f"Ошибка индексации репозитория: {e}", exc_info=True)
            if isinstance(e, (RepositoryConnectionError, RepositoryIndexError)):
                raise
            raise RepositoryIndexError(f"Ошибка индексации: {e}") from e

    def update_repository_index(self, force: bool = False) -> RepositoryIndex:
        """
        Обновляет существующий индекс репозитория.

        Args:
            force: Принудительная полная переиндексация

        Returns:
            Обновленный индекс репозитория

        Raises:
            RepositoryConnectionError: При ошибках подключения
            RepositoryIndexError: При ошибках индексации
        """
        if not self.repository_context:
            raise RepositoryIndexError("Контекст репозитория не установлен")

        return self.index_repository(
            repository_url=self.repository_context.repository_url,
            repository_path=self.repository_context.repository_path,
            force=force,
            incremental=not force,
        )

    def is_repository_indexed(self) -> bool:
        """
        Проверяет наличие индекса репозитория.

        Returns:
            True если индекс существует и валиден
        """
        # Проверка в памяти
        if self._repository_index:
            return True

        # Проверка файла индекса
        if self.repository_context and self.repository_context.index_path:
            return IndexStorage.exists(self.repository_context.index_path)

        return False

    def get_repository_index(self) -> Optional[RepositoryIndex]:
        """
        Возвращает текущий индекс репозитория.

        Returns:
            Индекс репозитория или None если не проиндексирован
        """
        # Возврат из памяти
        if self._repository_index:
            return self._repository_index

        # Загрузка из файла
        if self.repository_context and self.repository_context.index_path:
            index = IndexStorage.load(self.repository_context.index_path)
            if index:
                self._repository_index = index
                return index

        return None

    def validate_generated_code(
        self,
        code: str,
        test_case: Optional[TestCase] = None,
    ) -> ValidationReport:
        """
        Валидирует сгенерированный код теста.

        Args:
            code: Сгенерированный код Python
            test_case: Исходный тест-кейс для проверки соответствия

        Returns:
            ValidationReport: Отчет о валидации
        """
        # Создаем временный файл для валидации
        temp_file = GeneratedFile(
            path=Path("temp.py"),
            content=code,
            file_type="test",
            size_bytes=len(code.encode("utf-8")),
        )

        default_test_case = TestCase(
            id="temp",
            name="temp",
            expected_result="",
            test_layer="E2E",
            steps=[TestStep(id="1", name="temp", description="temp", expected_result="temp")]
        )
        return self._validate_code([temp_file], test_case or default_test_case)

    def format_code(self, code: str, style: Optional[str] = None) -> str:
        """
        Форматирует код согласно стандартам проекта.

        Args:
            code: Исходный код
            style: Стиль форматирования (black, ruff, autopep8)

        Returns:
            Отформатированный код
        """
        return self.code_formatter.format_code(code, style or "black")

    def _extract_selectors_with_cdp(self, test_case: TestCase) -> Dict[str, Any]:
        """
        Извлекает селекторы элементов с помощью CDP.

        Args:
            test_case: Тест-кейс

        Returns:
            Словарь с селекторами для каждого шага
        """
        selectors = {}

        try:
            # Определение URL из тест-кейса или шагов
            url = self._extract_url_from_test_case(test_case)
            if not url:
                self.logger.warning("Не удалось определить URL для CDP анализа")
                return selectors

            # Запуск CDP клиента
            with CDPClient(
                browser_type=test_case.browser or "chromium",
                headless=True,
            ) as cdp_client:
                # Переход на страницу
                cdp_client.navigate(url)

                # Извлечение селекторов для каждого шага
                selector_extractor = SelectorExtractor(cdp_client)

                for step in test_case.steps:
                    step_id = step.id
                    step_description = step.description

                    # Поиск селекторов для элементов из описания шага
                    step_selectors = selector_extractor.extract_selectors(
                        step_description, page_url=None  # Уже на странице
                    )

                    if step_selectors:
                        # Берем лучший селектор (с наивысшим приоритетом)
                        best_selector = step_selectors[0]
                        selectors[f"step_{step_id}"] = {
                            "description": step_description,
                            "selector": best_selector.get("selector"),
                            "strategy": best_selector.get("strategy"),
                            "type": best_selector.get("type"),
                            "priority": best_selector.get("priority"),
                            "alternatives": step_selectors[1:3],  # Еще 2 альтернативы
                        }

                self.logger.info(f"CDP извлечено {len(selectors)} селекторов")

        except Exception as e:
            self.logger.warning(f"Ошибка извлечения селекторов через CDP: {e}")
            # Не прерываем генерацию, просто возвращаем пустой словарь

        return selectors

    def _extract_url_from_test_case(self, test_case: TestCase) -> Optional[str]:
        """
        Извлекает URL из тест-кейса.

        Args:
            test_case: Тест-кейс

        Returns:
            URL или None
        """
        import re

        # Поиск URL в описании
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, test_case.description or "")
        if urls:
            return urls[0]

        # Поиск URL в шагах
        for step in test_case.steps:
            urls = re.findall(url_pattern, step.description or "")
            if urls:
                return urls[0]

        # Поиск URL в предусловиях
        if test_case.preconditions:
            urls = re.findall(url_pattern, test_case.preconditions)
            if urls:
                return urls[0]

        return None

