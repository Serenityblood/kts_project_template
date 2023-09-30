from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import request_schema, response_schema, docs

from admin_api.game.schemes import GameSchema, PlayerSchem
from admin_api.web.app import View
from admin_api.web.middlewares import HTTP_ERROR_CODES
from admin_api.web.mixins import AuthRequiredMixin
from admin_api.web.utils import json_response, error_json_response


class ListGamesView(AuthRequiredMixin, View):
    @docs(tags=['games'], summary='Return all games')
    async def get(self):
        games = await self.request.app.store.games.list_games()
        if games is None:
            raise HTTPForbidden('No games in db')
        data = []
        for game in games:
            data.append(
                GameSchema().dump(game)
            )
        return json_response(
            data={'games': data}
        )


class ListGamesInChatView(AuthRequiredMixin, View):
    @docs(tags=['games'], summary='Return games in chat by chat_id')
    async def get(self, chat_id):
        games = await self.request.app.store.games.get_games_in_chat(
            chat_id
        )
        if games is None:
            raise HTTPForbidden('No games in chat')
        data = []
        for game in games:
            data.append(
                GameSchema().dump(game)
            )
        return json_response(
            data={'games': data}
        )


class ListPlayersView(AuthRequiredMixin, View):
    @docs(tags=['players'], summary='list players')
    async def list_players(self):
        players = await self.request.app.store.games.list_players()
        if players is None:
            raise HTTPForbidden('No players in db')
        data = []
        for player in players:
            data.append(
                PlayerSchem().dump(player)
            )
        return json_response(
            data={'players': data}
        )
