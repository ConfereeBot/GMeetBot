import asyncio
import json
import os
import threading

import aiormq
import nodriver as uc
from aiormq.abc import AbstractChannel
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse

import gmeetbot.responses as res

from . import utils
from .gmeet import GMeet
from .responses import Req, Res

logger = utils.logger.setup_logger(__name__)

app = FastAPI()


def remove_file(filepath: str):
    """Удаление файла после скачивания.

    Args:
        filepath (str): Путь до файла.
    """
    try:
        if filepath.endswith(".mp4"):
            return
        os.remove(filepath)
        logger.debug(f"File {filepath} removed successfuly")
    except Exception as e:
        logger.error(f"Cannot remove file after uploading: {e}")


@app.get("/download/{filepath}")
async def download(filepath: str, background_tasks: BackgroundTasks):
    """Отдача файла по сети.

    Args:
        filepath (str): Путь до файла.
        background_tasks (BackgroundTasks): Ссылка на фукнцию для удаления файла после загрузки.

    Raises:
        HTTPException: HTTPException
    """
    filepath = "videos/" + filepath
    if not os.path.exists(filepath) or not (
        filepath.endswith(".png") or filepath.endswith(".mp4")
    ):
        raise HTTPException(status_code=404, detail="File not found")

    background_tasks.add_task(remove_file, filepath)
    return FileResponse(
        filepath,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filepath}"},
    )


async def run_task(message: aiormq.abc.DeliveredMessage):
    """Запуск записи конференции по сообщению из брокера.

    Args:
        message (aiormq.abc.DeliveredMessage): Сообщение из брокера.
    """
    link = message.body.decode().replace("'", '"')
    logger.info(f"Received run task: {link}")
    await message.channel.basic_ack(delivery_tag=message.delivery.delivery_tag)
    try:
        if GMeet().is_running:
            await answer_producer(message.channel, res.prepare(Res.BUSY, link))
            return
        await answer_producer(message.channel, res.prepare(Res.STARTED, link))
        filename = await GMeet().record_meet(link)
        await answer_producer(message.channel, res.prepare(Res.SUCCEDED, link, -1, filename))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await answer_producer(message.channel, res.prepare(Res.ERROR, link))


async def manage_task(message: aiormq.abc.DeliveredMessage):
    """Обработчик заданий от продюсера.

    Args:
        message (aiormq.abc.DeliveredMessage): Сообщение из брокера.
    """
    body = message.body.decode().replace("'", '"')
    logger.info(f"Received manage task: {body}")
    await message.channel.basic_ack(delivery_tag=message.delivery.delivery_tag)
    try:
        msg: dict = json.loads(body)
        user_id = msg.get("user_id")
        req_type = Req(msg.get("type"))
        if req_type == Req.SCREENSHOT:
            filepath = await GMeet().get_screenshot()
            await answer_producer(
                message.channel,
                res.prepare(Req.SCREENSHOT, GMeet().get_link(), user_id, filepath),
            )
        elif req_type == Req.TIME:
            await answer_producer(
                message.channel,
                res.prepare(Req.TIME, GMeet().get_link(), user_id, GMeet().recording_time),
            )
        elif req_type == Req.STOP_RECORD:
            GMeet().stop_recording()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await answer_producer(message.channel, res.prepare(Res.ERROR, body))


async def answer_producer(channel: AbstractChannel, res: bytes):
    """Создание ответа продюсеру.

    Args:
        channel (AbstractChannel): _description_
        res (bytes): Ответ в формате responses.prepare()
    """
    logger.debug(f"Send msg to gmeet_res: {res.decode()}")
    await channel.basic_publish(
        body=res,
        exchange="conferee_direct",
        routing_key="gmeet_res",
    )


async def start_listener():
    """Подписка на топики брокера."""
    print("Starting listening to queues...")
    connection = await aiormq.connect(os.getenv("AMQP"))
    async with connection as conn:
        channel = await conn.channel()
        q_tasks = channel.basic_consume(queue="gmeet_tasks", consumer_callback=run_task)
        q_manage = channel.basic_consume(queue="gmeet_manage", consumer_callback=manage_task)

        await asyncio.gather(q_tasks, q_manage)
        print("Listeners are ready!")
        await asyncio.Future()
    print("Stopped listening to queues.")


def start_web():
    """Запуск веб-севера, необходимого для скачивания с хоста видео и фото."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    """Точка входа в программу.
    В отдельном потоке запускается веб-сервер.
    Асинхронно запускается listener топиков брокера.
    """
    logger.info("Start web server in detached thread.")
    web_thread = threading.Thread(target=start_web)
    web_thread.daemon = True
    web_thread.start()

    logger.info("Start gmeet recorder module.")
    uc.loop().run_until_complete(start_listener())
    logger.info("Finished gmeet recording.")
