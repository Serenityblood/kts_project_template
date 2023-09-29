import asyncio
import json
import os
import sys
from asyncio import Task
from typing import Optional
from logging import getLogger

from aio_pika import connect, Message as PikaMes
from aio_pika.abc import DeliveryMode
from aiohttp import TCPConnector
from aiohttp.client import ClientSession

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from kts_backend.web.utils import config_from_yaml, build_query

API_PATH = "https://api.vk.com/method/"


class Poller:
    def __init__(self):
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.session: ClientSession or None = None
        self.key = None
        self.server = None
        self.ts = None
        self.config: dict = None
        self.rabbit_connect = None
        self.logger = None

    async def start(self):
        self.logger = getLogger('Poller')
        self.rabbit_connect = await connect(
            "amqp://guest:guest@rabbitmq:5672/"
        )
        self.config = config_from_yaml(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "etc/config.yaml"
            )
        )
        self.session = ClientSession(connector=TCPConnector(ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            print(f"{e}")
        self.is_running = True
        async with self.rabbit_connect:
            while self.is_running:
                await self.poll()

    async def stop(self):
        self.is_running = False
        await self.poll_task

    async def _get_long_poll_service(self):
        async with self.session.get(
            build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.config['bot']['group_id'],
                    "access_token": self.config['bot']['token'],
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]

    async def poll(self):
        request_link = build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "key": self.key,
                "ts": self.ts,
                "wait": 30,
            },
        )
        async with self.session.get(
            request_link
        ) as resp:
            data = await resp.json()
            print(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                if update['type'] == 'message_new':
                    updates.append(
                        update
                    )
            channel = await self.rabbit_connect.channel()
            await channel.declare_queue(
                    "test_queue",
                    durable=True,
                )
            message_body = json.dumps(updates)
            await channel.default_exchange.publish(
                PikaMes(
                    message_body.encode(),
                    delivery_mode=DeliveryMode.PERSISTENT
                ),
                routing_key='test_queue'
            )
            # if updates is not None:
            #     await self.store.bots_manager.handle_updates(updates)


if __name__ == '__main__':
    poller = Poller()
    asyncio.run(poller.start())
