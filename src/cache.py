import html
from src.config import settings
from src.storage import LESSONS, TASK_DESCRIPTIONS, get_submissions_by_task
from urllib.parse import urlencode

_index_page: str = "<h2>Инициализация сервера...</h2>"
_lesson_pages: dict[str, str] = {}
_task_pages: dict[tuple[str, str], str] = {}


def get_index_page() -> str:
    return _index_page


def get_lesson_page(lesson_name: str) -> str:
    return _lesson_pages.get(
        lesson_name,
        '<h2>Занятие не найдено. <a href="/">На главную</a></h2>',
    )


def get_task_page(lesson_name: str, task_code: str) -> str:
    safe_lesson = html.escape(lesson_name)
    return _task_pages.get(
        (lesson_name, task_code),
        f'<h2>Задание не найдено. <a href="/{safe_lesson}">К занятию</a> | <a href="/">На главную</a></h2>',
    )


def rebuild_index_page() -> None:
    """Собирает главную страницу со списком занятий."""
    global _index_page

    if LESSONS:
        items = [
            f'<li><a href="/{html.escape(name)}">{html.escape(name)}</a></li>'
            for name in LESSONS
        ]
        links = "\n".join(items)
    else:
        links = "<p>Нет доступных занятий.</p>"

    form_block = (
        f'<p><a href="{html.escape(settings.FORM_URL)}" target="_blank">Отправить решение</a></p>'
        if settings.FORM_URL
        else ""
    )

    _index_page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Выбор занятия</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #007BFF; font-size: 18px; }}
        a:hover {{ text-decoration: underline; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Учебная платформа</h1>
        <h2>Выберите занятие</h2>
        <ul>{links}</ul>
    </div>
</body>
</html>"""


def rebuild_lesson_page(lesson_name: str) -> None:
    """Собирает страницу занятия со списком его заданий."""
    if lesson_name not in LESSONS:
        return

    safe_lesson = html.escape(lesson_name)
    task_codes = LESSONS[lesson_name]

    if task_codes:
        items = [
            f'<li><a href="/{safe_lesson}/{html.escape(code)}">Задание: {html.escape(code)}</a></li>'
            for code in task_codes
        ]
        links = f"<ul>\n" + "\n".join(items) + "\n</ul>"
    else:
        links = "<p>В этом занятии нет задач.</p>"

    _lesson_pages[lesson_name] = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Занятие: {safe_lesson}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #007BFF; font-size: 18px; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-bottom: 10px; font-size: 16px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <a class="back-link" href="/">&larr; Вернуться к списку занятий</a>
        <h1>Занятие: {safe_lesson}</h1>
        <h2>Выберите задание</h2>
        {links}
    </div>
</body>
</html>"""


def rebuild_task_page(lesson_name: str, task_code: str) -> None:
    """Точечно пересобирает страницу одного задания из памяти."""
    if lesson_name not in LESSONS or task_code not in LESSONS[lesson_name]:
        return

    desc = TASK_DESCRIPTIONS.get(lesson_name, {}).get(task_code, "Описание отсутствует.")
    safe_lesson = html.escape(lesson_name)
    safe_code = html.escape(str(task_code))
    safe_desc = html.escape(str(desc)).replace("\n", "<br>")


    # Внутри rebuild_task_page:
    if settings.FORM_URL:
        params = urlencode({
            settings.FORM_LESSON_FIELD: lesson_name,
            settings.FORM_TASK_FIELD: task_code,
        })
        separator = "&" if "?" in settings.FORM_URL else "?"
        prefilled_url = f"{settings.FORM_URL}{separator}{params}"
        form_block = f'<p><a href="{html.escape(prefilled_url)}" target="_blank">Отправить решение</a></p>'
    else:
        form_block = ""

    rows = "\n".join(
        f"<tr>"
        f"<td>{sub.id}</td>"
        f"<td>{html.escape(sub.student_name)}</td>"
        f"<td>{html.escape(sub.status)}</td>"
        f"</tr>"
        for sub in get_submissions_by_task(lesson_name, task_code)
    )

    _task_pages[(lesson_name, task_code)] = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Задание {safe_code} — {safe_lesson}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 800px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ margin-top: 20px; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
        h2 {{ margin-top: 30px; }}
        .back-link {{ display: inline-block; margin-bottom: 10px; text-decoration: none; color: #007BFF; font-size: 16px; }}
        .back-link:hover {{ text-decoration: underline; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <a class="back-link" href="/{safe_lesson}">&larr; К списку заданий ({safe_lesson})</a>
        <h1>Занятие: {safe_lesson} — Задание: {safe_code}</h1>
        <h2>Условие задачи</h2>
        <p>{safe_desc}</p>
        {form_block}
        <h2>Таблица результатов</h2>
        <table>
            <tr><th>#</th><th>ФИО</th><th>Статус</th></tr>
            {rows}
        </table>
    </div>
</body>
</html>"""


def rebuild_all_cache() -> None:
    """Полная сборка кэша при старте сервера."""
    rebuild_index_page()
    for lesson_name, task_codes in LESSONS.items():
        rebuild_lesson_page(lesson_name)
        for task_code in task_codes:
            rebuild_task_page(lesson_name, task_code)
