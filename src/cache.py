import html
from src.config import settings
from src.storage import LESSONS, TASK_DESCRIPTIONS, get_submissions_by_lesson

_index_page: str = "<h2>Инициализация сервера...</h2>"
_lesson_pages: dict[str, str] = {}


def get_index_page() -> str:
    return _index_page


def get_lesson_page(lesson_name: str) -> str:
    return _lesson_pages.get(
        lesson_name,
        '<h2>Занятие не найдено. <a href="/">На главную</a></h2>',
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
        {form_block}
        <h2>Выберите занятие</h2>
        <ul>{links}</ul>
    </div>
</body>
</html>"""


def rebuild_lesson_page(lesson_name: str) -> None:
    """Точечно пересобирает страницу одного занятия из памяти."""
    if lesson_name not in LESSONS:
        return

    task_codes = LESSONS[lesson_name]
    if not task_codes:
        tasks_html = "<p>В этом занятии нет задач.</p>"
    else:
        blocks = []
        for code in task_codes:
            desc = TASK_DESCRIPTIONS.get(lesson_name, {}).get(code, "Описание отсутствует.")
            safe_code = html.escape(str(code))
            safe_desc = html.escape(str(desc)).replace("\n", "<br>")
            blocks.append(f"<h3>Задание: {safe_code}</h3>\n<p>{safe_desc}</p>")
        tasks_html = "\n".join(blocks)

    rows = "\n".join(
        f"<tr>"
        f"<td>{sub.id}</td>"
        f"<td>{html.escape(sub.student_name)}</td>"
        f"<td>{html.escape(sub.task)}</td>"
        f"<td>{html.escape(sub.status)}</td>"
        f"</tr>"
        for sub in get_submissions_by_lesson(lesson_name)
    )

    safe_lesson = html.escape(lesson_name)
    _lesson_pages[lesson_name] = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Занятие: {safe_lesson}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; max-width: 800px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ margin-top: 20px; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
        h2 {{ margin-top: 40px; }}
        .back-link {{ display: inline-block; margin-bottom: 10px; text-decoration: none; color: #007BFF; font-size: 16px; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <a class="back-link" href="/">&larr; Вернуться к списку занятий</a>
    <h1>Занятие: {safe_lesson}</h1>
    <h2>Описания задач</h2>
    {tasks_html}
    <h2>Таблица результатов</h2>
    <table>
        <tr><th>#</th><th>ФИО</th><th>Задание</th><th>Статус</th></tr>
        {rows}
    </table>
</body>
</html>"""


def rebuild_all_cache() -> None:
    """Полная сборка кэша при старте сервера."""
    rebuild_index_page()
    for lesson_name in LESSONS:
        rebuild_lesson_page(lesson_name)
