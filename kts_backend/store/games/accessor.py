import asyncio
import time 

from sqlalchemy import select, update as upd
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload
from admin_api.web.app import Application

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.games.models import GameModel, InGameCompanyModel
from kts_backend.store.vk_api.dataclasses import Message
from kts_backend.users.views.models import PlayerModel
from kts_backend.web.utils import Timer


class GameAccessor(BaseAccessor):
    # async def __init__(self, app: Application, *args, **kwargs):
    #     super().__init__(app, *args, **kwargs)
    #     self.game_store = {}

    async def connect(self, app: Application) -> GameModel:
        self.game_store = {}

    async def create_game(self, peer_id, max_rounds=5):
        game = GameModel(
            chat_id=peer_id, is_active=True,
            max_rounds=max_rounds, current_round=0
        )
        async with self.app.database.session.begin() as session:
            session.add(game)
            await session.commit()
        return game

    async def get_games_by_peer_id(self, peer_id) -> list[GameModel] or None:
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.players),
                    joinedload(GameModel.companys)
                ).where(
                    GameModel.chat_id == peer_id
                )
            )
            try:
                games = resp.scalars().unique()
                return games
            except NoResultFound:
                return None

    async def get_active_game(self, peer_id):
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.players),
                    joinedload(GameModel.companys)
                ).where(
                    GameModel.chat_id == peer_id,
                    GameModel.is_active == True
                )
            )
            try:
                game = resp.scalars().unique().one()
                return game
            except NoResultFound:
                return None

    async def create_companys(self, game_id):
        names = ['a', 'b', 'c']
        companys = []
        for i in range(0, 3):
            companys.append(
                InGameCompanyModel(
                    game_id=game_id,
                    title=names[i],
                    current_stock_price=100
                )
            )
        async with self.app.database.session.begin() as session:
            session.add_all(companys)
            await session.commit()
        return companys

    async def update_game_condition(self, game_id):
        pass

    async def get_all_active_games(self):
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.players),
                    joinedload(GameModel.companys)
                ).where(
                    GameModel.is_active == True
                )
            )
            try:
                games = resp.scalars().unique().all()
                return games
            except NoResultFound:
                return None

    async def check(self, update):
        loop = asyncio.get_running_loop().call_later(
            30,
            lambda: asyncio.ensure_future(
                self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text='mess',
                        peer_id=update.object.peer_id
                    )
                )
            )
        )

    async def check2(self, update):
        peer_id = update.object.peer_id
        players = await self.app.store.vk_api.get_conversation_members(peer_id)
        message = ''
        for player in players:
            message += player.name + ' '
        await self.app.store.vk_api.send_message(
            Message(
                user_id=update.object.user_id,
                text=message,
                peer_id=update.object.peer_id
            )
        )
