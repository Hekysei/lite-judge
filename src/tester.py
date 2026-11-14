import asyncio

from src.cache import rebuild_task_page
from src.sandbox import run_sandboxed_code
from src.storage import (
    TESTS_CACHE,
    Submission,
    create_submission,
    save_submission_file,
)

MAX_WORKERS = 17
submission_queue: asyncio.Queue[Submission] = asyncio.Queue()


async def _update_submission(sub: Submission, status: str) -> None:
    """Обновляет статус в памяти, сохраняет файл на диск и обновляет кэш страницы задания."""
    sub.status = status
    await asyncio.to_thread(save_submission_file, sub)
    rebuild_task_page(sub.lesson, sub.task)


async def submit_task(student_name: str, lesson_name: str, task_code: str, code: str) -> None:
    sub = create_submission(student_name, lesson_name, task_code, code)
    await _update_submission(sub, "⏳ Тестируется...")
    await submission_queue.put(sub)


async def _evaluate_submission(sub: Submission) -> None:
    tests = TESTS_CACHE.get(sub.lesson, {}).get(sub.task)
    if not tests:
        await _update_submission(sub, "❌ Ошибка: Тесты не найдены")
        return

    for test in tests:
        actual_output = await run_sandboxed_code(sub.code, test.input)
        if actual_output.strip() != test.expected.strip():
            await _update_submission(sub, f"❌ Ошибка на тесте {test.name}")
            return

    await _update_submission(sub, "✅ Решено")


async def worker(worker_id: int) -> None:
    while True:
        sub = await submission_queue.get()
        try:
            await _evaluate_submission(sub)
        except Exception as e:
            print(f"[Worker {worker_id}] Ошибка при проверке посылки #{sub.id}: {e}")
        finally:
            submission_queue.task_done()
