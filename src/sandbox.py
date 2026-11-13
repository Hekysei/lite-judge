import asyncio
from src.config import settings


async def ensure_docker_image() -> None:
    """Проверяет наличие Docker-образа локально и скачивает его при отсутствии."""
    inspect_proc = await asyncio.create_subprocess_exec(
        "docker", "image", "inspect", settings.DOCKER_IMAGE,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await inspect_proc.wait()

    if inspect_proc.returncode == 0:
        print(f"Docker-образ {settings.DOCKER_IMAGE} готов к работе.")
        return

    print(f"Скачивание Docker-образа {settings.DOCKER_IMAGE}...")
    pull_proc = await asyncio.create_subprocess_exec(
        "docker", "pull", settings.DOCKER_IMAGE,
    )
    await pull_proc.wait()

    if pull_proc.returncode == 0:
        print(f"Docker-образ {settings.DOCKER_IMAGE} успешно загружен.")
    else:
        print(f"Ошибка загрузки Docker-образа {settings.DOCKER_IMAGE}. Проверьте, запущен ли Docker.")


async def run_sandboxed_code(
    code_str: str, stdin_data: str, timeout_sec: int = settings.DOCKER_TIMEOUT
) -> str:
    """Асинхронный запуск изолированного Docker-контейнера без создания временных файлов."""
    cmd = [
        "docker", "run", "--rm", "-i",
        "--net", "none",
        "--read-only",
        "--memory", "64m",
        "--cpus", "0.5",
        settings.DOCKER_IMAGE,
        "timeout", "-s", "KILL", str(timeout_sec),
        "python", "-u", "-c", code_str,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=stdin_data.encode("utf-8")),
                timeout=timeout_sec + 1,
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
            return "Ошибка: Превышено время выполнения (Timeout)."

        if process.returncode in (124, 137):
            return "Ошибка: Превышено время выполнения (Timeout)."

        if process.returncode != 0:
            return f"Ошибка:\n{stderr.decode('utf-8', errors='replace').strip()}"

        return stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Внутренняя ошибка выполнения: {e}"
