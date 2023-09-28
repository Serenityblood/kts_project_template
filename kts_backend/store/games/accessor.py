import asyncio

from sqlalchemy import delete, select,  update as upd
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload, subqueryload
from admin_api.web.app import Application

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.games.game_process import Game
from kts_backend.games.models import GameModel, InGameCompanyModel, Stock, StockModel
from kts_backend.store.vk_api.dataclasses import Message
from kts_backend.users.views.models import PlayerModel


class GameAccessor(BaseAccessor):
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

    async def update_game_conditions(self, game: Game):
        async with self.app.database.session.begin() as session:
            await session.execute(
                upd(GameModel).where(
                    GameModel.id == game.id
                ).values(
                    {
                        GameModel.is_active: game.is_active,
                        GameModel.current_round: game.current_round,
                    }

                )
            )
            for _, company in game.companys.items():
                await session.execute(
                    upd(InGameCompanyModel).where(
                        InGameCompanyModel.id == company.id
                    ).values(
                        {InGameCompanyModel.current_stock_price: company.current_stock_price}
                    )
                )
            for _, player in game.players.items():
                reg_stocks = []
                for title, stocks in player.stocks.items():
                    result = []
                    unreg_stocks = []
                    for stock in stocks:
                        if stock.id is None:
                            unreg_stocks.append(stock)
                        else:
                            reg_stocks.append(stock.id)
                            result.append(stock)
                    if len(unreg_stocks) > 0:
                        stocks_created = await self.create_stocks(
                            game.id, unreg_stocks
                        )
                        result.extend(stocks_created)
                        for stock in stocks_created:
                            reg_stocks.append(stock.id)
                    player.stocks[title] = result
                if len(reg_stocks) > 0:
                    await session.execute(
                        delete(StockModel).where(
                            StockModel.owner_id == player.id
                        ).where(
                            StockModel.id.not_in(reg_stocks)
                        ).where(StockModel.game_id == game.id)
                    )
                await session.execute(
                    upd(PlayerModel).where(
                        PlayerModel.id == player.id
                    ).values(
                        {
                            PlayerModel.capital: player.capital,
                            PlayerModel.clear_capital: player.clear_capital
                        }
                    )
                )
            await session.commit()
            return game

    async def get_all_active_games(self):
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.players).
                    subqueryload(PlayerModel.stocks).
                    subqueryload(StockModel.company),
                    joinedload(GameModel.companys),
                ).where(
                    GameModel.is_active == True
                )
            )
            try:
                games = resp.scalars().unique().all()
                return games
            except NoResultFound:
                return None

    async def create_stocks(self, game_id, stocks: list[Stock]) -> list[Stock]:
        stock_models = []
        for stock in stocks:
            stock_models.append(
                StockModel(
                    owner_id=stock.owner_id,
                    company_id=stock.company_id,
                    game_id=game_id
                )
            )
        async with self.app.database.session.begin() as session:
            session.add_all(stock_models)
            await session.commit()
        result = []
        for stock in stock_models:
            result.append(
                Stock(
                    id=stock.id,
                    owner_id=stock.owner_id,
                    company_id=stock.company_id,
                    game_id=stock.game_id
                )
            )
        return result

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
