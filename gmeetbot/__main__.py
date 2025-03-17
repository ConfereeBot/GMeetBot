import asyncio
import json
import os

import aiormq
import nodriver as uc
from aiormq.abc import AbstractChannel

import gmeetbot.responses as res

from . import utils
from .gmeet import GMeet
from .responses import Req, Res

logger = utils.logger.setup_logger(__name__)


async def run_task(message: aiormq.abc.DeliveredMessage):
    link = message.body.decode()
    logger.info(f"Received run task: {link}")
    await message.channel.basic_ack(delivery_tag=message.delivery.delivery_tag)
    await answer_producer(message.channel, Res.STARTED.format(link=link))
    try:
        if GMeet().is_running:
            await answer_producer(message.channel, res.prepare(Res.BUSY, link))
            return
        await GMeet().record_meet(link)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await answer_producer(message.channel, res.prepare(Res.ERROR, link))
    else:
        await answer_producer(message.channel, res.prepare(Res.SUCCEDED, link))


async def manage_task(message: aiormq.abc.DeliveredMessage):
    body = message.body.decode()
    logger.info(f"Received manage task: {body}")
    await message.channel.basic_ack(delivery_tag=message.delivery.delivery_tag)
    try:
        msg: dict = json.loads(body)
        req_type = Req(msg.get("req"))
        if req_type == Req.SCREENSHOT:
            filepath = await GMeet().get_screenshot()
            with open(filepath, "rb") as file:
                data = file.file()
            await answer_producer(message.channel, res.prepare(Req.SCREENSHOT, data))
        elif req_type == Req.TIME:
            await answer_producer(message.channel, res.prepare(Req.TIME, GMeet().recording_time))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await answer_producer(message.channel, res.prepare(Res.ERROR, body))


async def answer_producer(channel: AbstractChannel, res: bytes):
    logger.debug(f"Send msg to gmeet_res: {res.decode()}")
    await channel.basic_publish(
        body=res,
        exchange="conferee_direct",
        routing_key="gmeet_res",
    )


async def main():
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


if __name__ == "__main__":
    logger.info("Start gmeet recorder module.")
    uc.loop().run_until_complete(main())
    logger.info("Finished gmeet recording.")
