import random
import json
import typing
from typing import Optional

from aiohttp import TCPConnector
from aio_pika import connect as rq_con, Message as PikaMes
from aio_pika.abc import DeliveryMode
from aiohttp.client import ClientSession

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.store.vk_api.vk_dataclasses import Message
from kts_backend.store.vk_api.poller import Poller
from kts_backend.users.views.models import Player


if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self, app: "Application"):
        if self.session is not None:
            await self.session.close()


    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

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
