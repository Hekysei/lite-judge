import html
from urllib.parse import urlencode

from src.config import settings
from src.storage import (
    LESSONS,
    TASK_DESCRIPTIONS,
    get_best_results_by_lesson,
    get_submissions_by_task,
)

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
    """Собирает страницу занятия со списком заданий, регистрацией и таблицей результатов."""
    if lesson_name not in LESSONS:
        return

    safe_lesson = html.escape(lesson_name)
    task_codes = LESSONS[lesson_name]

    if task_codes:
        items = [
            f'<li><a href="/{safe_lesson}/{html.escape(code)}">Задание {idx}: {html.escape(code)}</a></li>'
            for idx, code in enumerate(task_codes, start=1)
        ]
        links = "<ul>\n" + "\n".join(items) + "\n</ul>"
    else:
        links = "<p>В этом занятии нет задач.</p>"

    # Заголовки столбцов: ФИ и порядковые номера начиная с 1
    header_cells = ["<th>ФИ</th>"] + [
        f'<th><a href="/{safe_lesson}/{html.escape(code)}" title="{html.escape(code)}">{idx}</a></th>'
        for idx, code in enumerate(task_codes, start=1)
    ]
    table_header = "<tr>" + "".join(header_cells) + "</tr>"

    # Строки участников с лучшими результатами
    best_results = get_best_results_by_lesson(lesson_name)
    table_rows = []
    for student_name in sorted(best_results.keys()):
        student_tasks = best_results[student_name]
        cells = [f"<td>{html.escape(student_name)}</td>"]
        for code in task_codes:
            status = student_tasks.get(code, "—")
            cells.append(f"<td>{html.escape(status)}</td>")
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    rows_html = (
        "\n".join(table_rows)
        if table_rows
        else f'<tr><td colspan="{len(task_codes) + 1}">Пока нет посылок</td></tr>'
    )

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
        .container {{ max-width: 900px; margin: 0 auto; }}
        .reg-box {{ background: #f9f9f9; border: 1px solid #ddd; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .reg-box input {{ padding: 8px; font-size: 14px; width: 250px; margin-right: 8px; }}
        .reg-box button {{ padding: 8px 14px; font-size: 14px; cursor: pointer; }}
        .reg-status {{ margin-top: 8px; font-size: 14px; color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
        th:first-child, td:first-child {{ text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        th a {{ font-size: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <a class="back-link" href="/">&larr; Вернуться к списку занятий</a>
        <h1>Занятие: {safe_lesson}</h1>

        <div class="reg-box">
            <strong>Регистрация на занятие</strong>
            <div style="margin-top: 10px;">
                <input type="text" id="sfname-input" placeholder="Введите ваши ФИ">
                <button type="button" onclick="registerStudent()">Зарегистрироваться</button>
            </div>
            <div class="reg-status" id="reg-status"></div>
        </div>

        <h2>Выберите задание</h2>
        {links}

        <h2>Таблица результатов</h2>
        <table>
            {table_header}
            {rows_html}
        </table>
    </div>

    <script>
        const STORAGE_KEY = "SFname";

        function updateRegUI() {{
            const savedName = localStorage.getItem(STORAGE_KEY) || "";
            const input = document.getElementById("sfname-input");
            const status = document.getElementById("reg-status");
            input.value = savedName;
            if (savedName) {{
                status.textContent = "Вы зарегистрированы как: " + savedName;
            }} else {{
                status.textContent = "ФИ не указано. Зарегистрируйтесь для автозаполнения формы.";
            }}
        }}

        function registerStudent() {{
            const input = document.getElementById("sfname-input");
            const name = input.value.trim();
            if (name) {{
                localStorage.setItem(STORAGE_KEY, name);
            }} else {{
                localStorage.removeItem(STORAGE_KEY);
            }}
            updateRegUI();
        }}

        document.addEventListener("DOMContentLoaded", updateRegUI);
    </script>
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
    safe_name_field = html.escape(settings.FORM_NAME_FIELD)

    if settings.FORM_URL:
        params = urlencode({
            settings.FORM_LESSON_FIELD: lesson_name,
            settings.FORM_TASK_FIELD: task_code,
        })
        separator = "&" if "?" in settings.FORM_URL else "?"
        prefilled_url = f"{settings.FORM_URL}{separator}{params}"
        form_block = (
            f'<p><a id="submit-form-link" href="{html.escape(prefilled_url)}" '
            f'target="_blank">Отправить решение</a> '
            f'<span id="student-label" style="color: #555; font-size: 14px;"></span></p>'
        )
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

    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            const link = document.getElementById("submit-form-link");
            const label = document.getElementById("student-label");
            const savedName = localStorage.getItem("SFname");

            if (link && savedName) {{
                const url = new URL(link.href, window.location.origin);
                url.searchParams.set("{safe_name_field}", savedName);
                link.href = url.toString();
                if (label) {{
                    label.textContent = "(ФИ: " + savedName + ")";
                }}
            }}
        }});
    </script>
</body>
</html>"""


def rebuild_all_cache() -> None:
    """Полная сборка кэша при старте сервера."""
    rebuild_index_page()
    for lesson_name, task_codes in LESSONS.items():
        rebuild_lesson_page(lesson_name)
        for task_code in task_codes:
            rebuild_task_page(lesson_name, task_code)
