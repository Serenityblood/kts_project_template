import asyncio
import typing
from logging import getLogger

from kts_backend.games.game_process import Game
from kts_backend.games.models import GameModel, Company
from kts_backend.store.vk_api.dataclasses import Message, Update
from kts_backend.users.views.models import Player

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.game_store: dict[int, Game] = {}

    async def connect(self, app: "Application"):
        games: list[GameModel] = await self.app.store.games.get_all_active_games()
        for game in games:
            players = []
            for p in game.players:
                players.append(
                    Player(
                        id=p.id,
                        vk_id=p.vk_id,
                        name=p.name,
                        last_name=p.last_name,
                        game_id=p.game_id,
                        capital=p.capital,
                        clear_capital=p.clear_capital,
                        stocks=None
                    )
                )
            companys = []
            for c in game.companys:
                companys.append(
                    Company(
                        id=c.id,
                        title=c.title,
                        current_stock_price=c.current_stock_price,
                        game_id=c.game_id
                    )
                )
            self.game_store[game.chat_id] = Game(
                players={p.vk_id: p for p in players},
                companys={c.title: c for c in companys},
                max_rounds=game.max_rounds,
                game_id=game.id,
                is_active=game.is_active,
                chat_id=game.chat_id,
                round_in_progress=False,
                current_round=game.current_round
            )

    async def disconnect(self, app: "Application"):
        pass

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            if '/check' in update.object.body:
                await self.app.store.games.check(update)

            if '/get_users' in update.object.body:
                await self.app.store.games.check2(update)

            if '/help' in update.object.body:
                pass

            if '/start' in update.object.body:
                max_rounds = int(update.object.body.split()[1])
                game = await self.app.store.games.create_game(
                    update.object.peer_id, max_rounds
                )
                raw_players: list[Player] = (
                    await self.app.store.vk_api.get_conversation_members(
                        update.object.peer_id
                    )
                )
                for player in raw_players:
                    player.game_id = game.id
                    player.clear_capital = 1000
                    player.capital = 0
                players = await self.app.store.users.create_players(raw_players)
                companys = await self.app.store.games.create_companys(game.id)
                message = 'Игра успешно создана'
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text=message,
                        peer_id=update.object.peer_id
                    )
                )
                active_game: GameModel = await self.app.store.games.get_active_game(
                    game.chat_id
                )
                players = []
                for player in active_game.players:
                    players.append(Player(
                        id=player.id,
                        vk_id=player.vk_id,
                        name=player.name,
                        last_name=player.last_name,
                        stocks={c.title: [] for c in companys},
                        capital=player.capital,
                        clear_capital=player.clear_capital,
                        game_id=active_game.id
                    ))
                companys = []
                for company in active_game.companys:
                    companys.append(
                        Company(
                            id=company.id,
                            title=company.title,
                            current_stock_price=company.current_stock_price,
                            game_id=company.game_id
                        )
                    )

                self.game_store[game.chat_id] = Game(
                    players={p.vk_id: p for p in players},
                    companys={c.title: c for c in companys},
                    game_id=active_game.id,
                    is_active=active_game.is_active,
                    chat_id=active_game.chat_id,
                    max_rounds=active_game.max_rounds
                )
            if '/round' in update.object.body:
                await self.game_store[update.object.peer_id].start_round()
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text='Раунд начался',
                        peer_id=update.object.peer_id
                    )
                )
            if '/buy' in update.object.body:
                company_title = update.object.body.split()[1]
                message = (await self.game_store[update.object.peer_id]
                           .buy_stock(
                    company_title, update.object.user_id
                ))
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text=message,
                        peer_id=update.object.peer_id
                    )
                )
            if '/sell' in update.object.body:
                company_title = update.object.body.split()[1]
                message = (await self.game_store[update.object.peer_id]
                           .sell_stock(
                    company_title, update.object.user_id
                ))
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text=message,
                        peer_id=update.object.peer_id
                    )
                )
            if '/stats' in update.object.body:
                if update.object.peer_id not in self.game_store:
                    message = 'Нет активной игры'
                    return await self.app.store.vk_api.send_message(
                        Message(
                            user_id=update.object.user_id,
                            text=message,
                            peer_id=update.object.peer_id
                        )
                    )
                message = (
                    await self.game_store[update.object.peer_id]
                    .get_current_stats()
                )
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text=message,
                        peer_id=update.object.peer_id
                    )
                )

            if '/companys' in update.object.body:
                if update.object.peer_id not in self.game_store:
                    message = 'Нет активной игры'
                    return await self.app.store.vk_api.send_message(
                        Message(
                            user_id=update.object.user_id,
                            text=message,
                            peer_id=update.object.peer_id
                        )
                    )
                message = (
                    await self.game_store[update.object.peer_id]
                    .get_company_stats()
                )
                await self.app.store.vk_api.send_message(
                    Message(
                        user_id=update.object.user_id,
                        text=message,
                        peer_id=update.object.peer_id
                    )
                )


            # await self.app.store.vk_api.send_message(
            #     Message(
            #         user_id=update.object.user_id,
            #         text=update.object.body,
            #         peer_id=u`pdate.object.peer_id
            #     )
            # )
