import re
from dataclasses import dataclass
from pathlib import Path

LESSONS_DIR = Path("lessons")
SUBMISSIONS_DIR = Path("submissions")


@dataclass
class TestCase:
    name: str
    input: str
    expected: str


@dataclass
class Submission:
    id: int
    student_name: str
    lesson: str
    task: str
    code: str = ""
    status: str = "⏳ Тестируется..."


# Состояние в памяти (инициализируется при старте)
TESTS_CACHE: dict[str, dict[str, list[TestCase]]] = {}
TASK_DESCRIPTIONS: dict[str, dict[str, str]] = {}
LESSONS: dict[str, list[str]] = {}
SUBMISSIONS: dict[int, Submission] = {}

_next_id: int = 1


def _sanitize(name: str) -> str:
    """Очищает строку для безопасного использования в именах файлов и папок."""
    clean = re.sub(r"[^\w\s-]", "", str(name))
    return clean.strip().replace(" ", "_")


def create_submission(student_name: str, lesson: str, task: str, code: str) -> Submission:
    """Мгновенно выделяет уникальный ID в памяти и регистрирует посылку."""
    global _next_id
    sub = Submission(
        id=_next_id,
        student_name=student_name,
        lesson=_sanitize(lesson),
        task=_sanitize(task),
        code=code,
    )
    _next_id += 1
    SUBMISSIONS[sub.id] = sub
    return sub


def save_submission_file(sub: Submission) -> None:
    """Записывает файл конкретной посылки на диск (вызывается в отдельном потоке)."""
    dir_path = SUBMISSIONS_DIR / sub.lesson / sub.task
    dir_path.mkdir(parents=True, exist_ok=True)

    safe_student = _sanitize(sub.student_name)
    filepath = dir_path / f"{sub.id:04d}_{safe_student}.py"
    content = f"# STATUS: {sub.status}\n\n{sub.code}"

    try:
        filepath.write_text(content, encoding="utf-8")
    except OSError as e:
        print(f"Ошибка сохранения файла посылки {filepath.name}: {e}")


def get_submissions_by_task(lesson_name: str, task_code: str) -> list[Submission]:
    """Возвращает посылки для конкретного задания из памяти (новые сверху)."""
    subs = [
        s for s in SUBMISSIONS.values()
        if s.lesson == lesson_name and s.task == task_code
    ]
    subs.sort(key=lambda s: s.id, reverse=True)
    return subs


def _load_existing_submissions() -> None:
    """Один раз при старте читает существующие посылки и вычисляет _next_id."""
    global _next_id
    SUBMISSIONS.clear()

    if not SUBMISSIONS_DIR.exists():
        _next_id = 1
        return

    for filepath in SUBMISSIONS_DIR.glob("*/*/*.py"):
        parts = filepath.stem.split("_", 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue

        sub_id = int(parts[0])
        student_name = parts[1].replace("_", " ")
        lesson_name = filepath.parent.parent.name
        task_name = filepath.parent.name

        status = "Неизвестно"
        try:
            with filepath.open("r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("# STATUS:"):
                    status = first_line.removeprefix("# STATUS:").strip()
        except OSError:
            pass

        SUBMISSIONS[sub_id] = Submission(
            id=sub_id,
            student_name=student_name,
            lesson=lesson_name,
            task=task_name,
            status=status,
        )

    _next_id = max(SUBMISSIONS.keys(), default=0) + 1


def _load_lessons() -> None:
    """Один раз при старте загружает структуру занятий, условия и тесты."""
    TESTS_CACHE.clear()
    TASK_DESCRIPTIONS.clear()
    LESSONS.clear()

    if not LESSONS_DIR.exists():
        LESSONS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Создана папка {LESSONS_DIR}.")
        return

    for lesson_dir in sorted(LESSONS_DIR.iterdir()):
        if not lesson_dir.is_dir():
            continue

        lesson_name = lesson_dir.name
        LESSONS[lesson_name] = []
        TESTS_CACHE[lesson_name] = {}
        TASK_DESCRIPTIONS[lesson_name] = {}

        for task_dir in sorted(lesson_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            task_code = task_dir.name
            desc_path = task_dir / "desc.txt"
            TASK_DESCRIPTIONS[lesson_name][task_code] = (
                desc_path.read_text(encoding="utf-8").strip()
                if desc_path.exists()
                else "Описание отсутствует."
            )

            tests = []
            for in_path in sorted(task_dir.glob("*.in")):
                out_path = in_path.with_suffix(".out")
                if out_path.exists():
                    tests.append(
                        TestCase(
                            name=in_path.stem,
                            input=in_path.read_text(encoding="utf-8"),
                            expected=out_path.read_text(encoding="utf-8"),
                        )
                    )

            if tests:
                TESTS_CACHE[lesson_name][task_code] = tests
                LESSONS[lesson_name].append(task_code)


def init_storage() -> None:
    """Инициализирует все данные с диска при запуске сервера."""
    _load_lessons()
    _load_existing_submissions()
    print(f"Загружены занятия: {list(LESSONS.keys())}. Посылок в базе: {len(SUBMISSIONS)}.")
