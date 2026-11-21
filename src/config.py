import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    FORM_URL: str = os.getenv("FORM_URL", "")
    FORM_LESSON_FIELD: str = os.getenv("FORM_LESSON_FIELD", "lesson")
    FORM_TASK_FIELD: str = os.getenv("FORM_TASK_FIELD", "task")
    FORM_NAME_FIELD: str = os.getenv("FORM_NAME_FIELD", "SFname")

    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "17"))

    DOCKER_IMAGE: str = os.getenv("DOCKER_IMAGE", "python:3.11-alpine")
    DOCKER_TIMEOUT: int = int(os.getenv("DOCKER_TIMEOUT", "3"))


settings = Settings()
