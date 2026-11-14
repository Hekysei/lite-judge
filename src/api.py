import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.cache import get_index_page, get_lesson_page, get_task_page
from src.tester import submit_task

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def view_index():
    return get_index_page()


@router.post("/webhook")
async def handle_yandex_form(request: Request):
    data = await request.json()
    answers_raw = data.get("params", {}).get("answers")

    if answers_raw:
        answers = json.loads(answers_raw)
        student_name = answers.get("Ваше ФИ", "Аноним")
        lesson_name = answers.get("Код занятия", "Неизвестно")
        task_code = answers.get("Код задания", "Неизвестно")
        code = answers.get("Ваш код", "")

        print(f"[{student_name}] Получено решение {task_code} ({lesson_name}).")
        await submit_task(student_name, lesson_name, task_code, code)

    return {"status": "success"}


@router.get("/{lesson_name}", response_class=HTMLResponse)
async def view_lesson(lesson_name: str):
    return get_lesson_page(lesson_name)


@router.get("/{lesson_name}/{task_code}", response_class=HTMLResponse)
async def view_task(lesson_name: str, task_code: str):
    return get_task_page(lesson_name, task_code)
