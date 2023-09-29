import asyncio
import random
import os
import json
import yaml

from aiohttp.client import ClientSession
from aiohttp import TCPConnector

from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage

from kts_backend.web.config import Config, BotConfig


class Sender:
    def __init__(self):
        self.rabbit_connect = None
        self.config = None

    async def start(self):
        await self.build_config(
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

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def build_config(self, config_path):
        with open(config_path, "r") as f:
            raw_config = yaml.safe_load(f)

            self.config = {'bot': {
                'group_id': raw_config['bot']['group_id'],
                'token': raw_config['bot']['token']
            }}

    async def send_message(self, message: AbstractIncomingMessage):
        async with message.process():
            async with ClientSession(
                    connector=TCPConnector(verify_ssl=False)
            ) as session:
                raw_data = json.loads(message.body.decode())

                params = {
                    "random_id": random.randint(1, 2**32),
                    "peer_id": raw_data["peer_id"],
                    "group_id": self.config['bot']['group_id'],
                    "access_token": self.config['bot']['token'],
                    "message": raw_data["text"],
                }

                request_link = self._build_query(
                    host="api.vk.com",
                    method="/method/messages.send",
                    params=params
                )
                await session.post(request_link)


def run_sender():
    sender = Sender()
    asyncio.run(sender.start())


if __name__ == "__main__":
    run_sender()
