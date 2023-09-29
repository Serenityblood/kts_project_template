import asyncio
import random
import os
import sys
import json

from aiohttp.client import ClientSession
from aiohttp import TCPConnector

from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from kts_backend.web.utils import config_from_yaml, build_query


API_PATH = "https://api.vk.com/method/"


class Sender:
    def __init__(self):
        self.rabbit_connect = None
        self.config = None
        self.session = None

    async def start(self):
        self.session = ClientSession(connector=TCPConnector(ssl=False))
        self.config = config_from_yaml(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "etc/config.yaml"
            )
        )
        self.rabbit_connect = await connect(
            "amqp://guest:guest@rabbitmq:5672/"
        )
        async with self.rabbit_connect:
            channel = await self.rabbit_connect.channel()
            await channel.set_qos(prefetch_count=1)

            queue = await channel.declare_queue(
                "send_queue",
                durable=True,
            )

            await queue.consume(self.send_message)
            await asyncio.Future()

    async def send_message(self, message: AbstractIncomingMessage):
        async with message.process():
            data = json.loads(message.body)
            request_link = build_query(
                host=API_PATH,
                method='messages.send',
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": data['peer_id'],
                    "message": data['text'],
                    "access_token": self.config['bot']['token'],
                    'group_id': self.config['bot']['group_id']
                }
            )
            async with self.session.get(
                request_link
            ) as resp:
                print(resp)


def run_sender():
    sender = Sender()
    asyncio.run(sender.start())


if __name__ == "__main__":
    run_sender()
