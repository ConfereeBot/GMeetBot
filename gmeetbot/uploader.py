import os
from asyncio import sleep
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import yadisk

from . import utils

logger = utils.logger.setup_logger(__name__)


@asynccontextmanager
async def yadisk_session() -> AsyncGenerator[yadisk.AsyncClient, None]:
    client = yadisk.AsyncClient(token=os.getenv("TOKEN_YADISK"))
    yield client


ATTEMPTS_TO_UPLOAD = 10
ATTEMPTS_SLEEP_SEC = 5


async def upload_video(video_path: str) -> str:
    logger.info(f"Загрузка видео {video_path} на диск")

    destination = "app:/" + video_path
    attempts = 0
    link = ""
    while attempts < ATTEMPTS_TO_UPLOAD:
        attempts += 1
        try:
            async with yadisk_session() as session:
                path = await session.upload(video_path, destination, timeout=600)
                path = await session.publish(path.path)
                link = path.path
        except Exception as e:
            logger.error(
                f"Не удалось загрузить видео ({video_path}) на Яндекс Диск. \
Пробуем ещё раз ({attempts}/{ATTEMPTS_TO_UPLOAD})...\n:{e}"
            )
            await sleep(ATTEMPTS_SLEEP_SEC)
        else:
            os.remove(video_path)
            break

    return link
