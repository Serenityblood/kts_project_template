from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import request_schema, response_schema, docs

from admin_api.game.schemes import CompanySchema, GameSchema, GameInChat, PlayerSchema
from admin_api.web.app import View
from admin_api.web.middlewares import HTTP_ERROR_CODES
from admin_api.web.mixins import AuthRequiredMixin
from admin_api.web.utils import json_response


class ListGamesView(AuthRequiredMixin, View):
    @docs(tags=['games'], summary='Return all games')
    async def get(self):
        games = await self.request.app.store.games.list_games()
        if games is None:
            raise HTTPForbidden('No games in db')
        return json_response(
            data=GameSchema().dump(games, many=True)
        )


class ListGamesInChatView(AuthRequiredMixin, View):
    @docs(tags=['games'], summary='Return games in chat by chat_id')
    @request_schema(GameInChat)
    async def get(self):
        chat_id = self.data['chat_id']
        games = await self.request.app.store.games.get_games_in_chat(
            chat_id
        )
        if not games:
            raise HTTPForbidden('No games in chat')
        return json_response(
            data=GameSchema().dump(games, many=True)
        )


class ListPlayersView(AuthRequiredMixin, View):
    @docs(tags=['players'], summary='List players')
    async def get(self):
        players = await self.request.app.store.games.list_players()
        if not players:
            raise HTTPForbidden('No players in db')
        return json_response(
            data=PlayerSchema().dump(players, many=True)
        )


class ListCompanysView(AuthRequiredMixin, View):
    @docs(tags=['companys'], summary='List companys')
    async def get(self):
        companys = await self.request.app.store.games.list_companys()
        if not companys:
            raise HTTPForbidden('No companys in db')
        return json_response(
            data=CompanySchema().dump(companys, many=True)
        )
