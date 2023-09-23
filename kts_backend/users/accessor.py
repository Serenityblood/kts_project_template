from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from kts_backend.base.base_accessor import BaseAccessor
from kts_backend.users.views.models import PlayerModel, Player


class UserAccessor(BaseAccessor):
    async def create_players(self, players: list[Player]):
        players_models = []
        for player in players:
            if await self.get_player_by_vk_id(player.vk_id) is not None:
                continue
            players_models.append(
                PlayerModel(
                    vk_id=player.vk_id,
                    name=player.name,
                    last_name=player.last_name
                )
            )
        async with self.app.database.session.begin() as session:
            session.add_all(players_models)
            await session.commit()

    async def get_player_by_vk_id(self, vk_id: int):
        async with self.app.database.session.begin() as session:
            resp = await session.execute(
                select(PlayerModel).where(PlayerModel.vk_id == vk_id)
            )
            try:
                player = resp.scalar_one()
                return Player(
                    vk_id=player.vk_id,
                    name=player.name,
                    last_name=player.last_name
                )
            except NoResultFound:
                return None
