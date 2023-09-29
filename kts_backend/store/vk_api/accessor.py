import asyncio
import json
import random
import typing
from typing import Optional

from aiohttp import TCPConnector
# from aio_pika import connect, Message as PikaMes
# from aio_pika.abc import DeliveryMode
from aiohttp.client import ClientSession
from sqlalchemy import select

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.store.vk_api.dataclasses import Message, Update, UpdateObject
from kts_backend.store.vk_api.poller import Poller
from kts_backend.users.views.models import Player


if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None
        self.rabbit_connect = None
        self.rabbit_channel = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        # self.rabbit_connect = await connect("amqp://guest:guest@localhost/")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session is not None:
            await self.session.close()
        if self.poller is not None:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": "a_check",
                    "key": self.key,
                    "ts": self.ts,
                    "wait": 30,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                if update['type'] == 'message_new':
                    updates.append(
                        Update(
                            type=update["type"],
                            object=UpdateObject(
                                id=update["object"]['message']["id"],
                                user_id=update["object"]['message']["from_id"],
                                body=update["object"]['message']["text"],
                                peer_id=update['object']['message']['peer_id']
                            ),
                        )
                    )
            # channel = await self.rabbit_connect.channel()
            # queue = await channel.declare_queue(
            #         "task_queue_test",
            #         durable=True,
            #     )
            # message_body = json.dumps(updates)
            # await channel.default_exchange.publish(
            #     PikaMes(
            #         message_body.encode(), delivery_mode=DeliveryMode.PERSISTENT
            #     ),
            #     routing_key='task_queue_test'
            # )
            await self.app.store.bots_manager.handle_updates(updates)

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params={
                    "random_id": random.randint(1, 2**32),
                    "peer_id": message.peer_id,
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                    'group_id': self.app.config.bot.group_id
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    async def get_vk_users_info(self, user_ids: int) -> list[Player]:
        async with self.session.get(
            self._build_query(
                API_PATH,
                'users.get',
                params={
                    'user_id': ','.join(user_ids)
                }
            )
        ) as resp:
            data = await resp.json()['response']
        players = []
        for user in data:
            players.append(
                Player(
                    vk_id=user['id'],
                    name=user['first_name'],
                    last_name=user['last_name']
                )
            )
        return players

    async def get_conversation_members(self, peer_id: int):
        async with self.session.get(
            self._build_query(
                API_PATH,
                'messages.getConversationMembers',
                params={
                    'peer_id': peer_id,
                    'group_id': self.app.config.bot.group_id,
                    'access_token': self.app.config.bot.token
                }
            )
        ) as resp:
            resp = await resp.json()
            print(resp)
            profiles = resp['response']['profiles']
            players: list[Player] = []
            for user in profiles:
                players.append(
                    Player(
                        vk_id=user['id'],
                        name=user['first_name'],
                        last_name=user['last_name'],
                        id=None,
                        game_id=None,
                        capital=None,
                        clear_capital=None,
                        stocks=None
                    )
                )
            return players
