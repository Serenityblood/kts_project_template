from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.users.views.models import PlayerModel, Player


class UserAccessor(BaseAccessor):
    async def create_players(self, players: list[Player]) -> list[PlayerModel]:
        players_models = []
        result = []
        for player in players:
            p = await self.get_player_by_vk_id(player.vk_id)
            if p is not None:
                result.append(p)
                continue
            players_models.append(
                PlayerModel(
                    vk_id=player.vk_id,
                    name=player.name,
                    last_name=player.last_name,
                    game_id=player.game_id,
                    capital=player.capital,
                    clear_capital=player.clear_capital
                )
            )
        async with self.app.database.session.begin() as session:
            session.add_all(players_models)
            await session.commit()
        result.extend(players_models)
        return result

    async def get_player_by_vk_id(self, vk_id: int):
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(PlayerModel).where(PlayerModel.vk_id == vk_id)
            )
            try:
                player = resp.scalar_one()
                return player
            except NoResultFound:
                return None
