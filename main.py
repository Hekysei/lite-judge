import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api import router
from src.cache import rebuild_all_cache
from src.config import settings
from src.sandbox import ensure_docker_image
from src.storage import init_storage
from src.tester import worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_docker_image()
    init_storage()
    rebuild_all_cache()
    workers = [asyncio.create_task(worker(i)) for i in range(settings.MAX_WORKERS)]
    yield
    for w in workers:
        w.cancel()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
