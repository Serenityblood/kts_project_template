from admin_api.base.base_accessor import BaseAccessor

from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.exc import NoResultFound

from kts_backend.games.models import GameModel, InGameCompanyModel, Company, StockModel
from kts_backend.users.views.models import PlayerModel


class GameAccessor(BaseAccessor):
    async def list_companys(self) -> list[InGameCompanyModel] or None:
        async with self.app.database.session.begin() as session:
            res = await session.execute(select(InGameCompanyModel))
            try:
                companys = res.scalars().all()
                return companys
            except NoResultFound:
                return None

    async def clear_companys(self) -> True or False:
        async with self.app.database.session.begin() as session:
            await session.execute(delete(InGameCompanyModel))
        return True

    async def get_companys_by_game_id(self, game_id) -> Company or None:
        async with self.app.database.session.begin() as session:
            res = await session.execute(
                select(InGameCompanyModel).where(
                    InGameCompanyModel.game_id == game_id
                )
            )
            try:
                companys = res.scalars().unique().all()
                return companys
            except NoResultFound:
                return None

    async def list_games(self) -> list[GameModel] or None:
        async with self.app.database.session.begin() as session:
            res = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.companys),
                    joinedload(GameModel.players)
                )
            )
            try:
                games = res.scalars().unique().all()
                return games
            except NoResultFound:
                return None

    async def get_games_in_chat(self, chat_id):
        async with self.app.database.session.begin() as session:
            res = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.companys),
                    joinedload(GameModel.players)
                ).where(
                    GameModel.chat_id == chat_id
                )
            )
            try:
                games = res.scalars().unique().all()
                return games
            except NoResultFound:
                return None

    async def clear_games(self) -> True:
        async with self.app.database.session.begin() as session:
            await session.execute(delete(GameModel))
        return True

    async def list_players(self) -> list[PlayerModel]:
        async with self.app.database.session.begin() as session:
            res = await session.execute(
                select(PlayerModel)
            )
            try:
                players = res.scalars().unique().all()
                return players
            except NoResultFound:
                return None
