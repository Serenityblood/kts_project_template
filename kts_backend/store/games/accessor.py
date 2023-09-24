from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.games.models import GameModel, ScoreModel
from kts_backend.users.views.models import PlayerModel


class GameAccessor(BaseAccessor):
    async def start_game(self, peer_id):
        game = GameModel(
            chat_id=peer_id, is_active=True
        )
        async with self.app.database.session.begin() as session:
            session.add(game)
            await session.commit()

    async def create_scores(
            self, players: list[PlayerModel],
            game_id) -> list[ScoreModel]:
        scores: list[ScoreModel] = []
        for player in players:
            scores.append(
                ScoreModel(
                    player_id=player.id,
                    capital=0,
                    clear_capital=1000,
                    game_id=game_id
                )
            )
        async with self.app.database.session.begin() as session:
            session.add_all(scores)
            await session.commit()
        return scores

    async def get_game_by_peer_id(self, peer_id) -> list[GameModel] or None:
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(GameModel).options(
                    joinedload(GameModel.scores).where(
                        GameModel.chat_id == peer_id
                    )
                )
            )
            try:
                games = resp.scalars().unique()
                return games
            except NoResultFound:
                return None

    async def start_round(self, peer_id):
        pass

    async def stop_game(self, peer_id):
        pass

    async def buy_stock(self, vk_id, company):
        pass

    async def sell_stock(self, vk_id, company):
        pass

    async def create_ingame_companys(self, game_id):
        pass


