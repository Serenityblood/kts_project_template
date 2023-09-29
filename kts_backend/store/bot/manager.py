import asyncio
import json
import typing
from logging import getLogger

from aio_pika import connect as rq_con, Message as PikaMes
from aio_pika.abc import AbstractIncomingMessage, DeliveryMode

from kts_backend.games.game_process import Game
from kts_backend.games.models import GameModel, Company, Stock
from kts_backend.store.vk_api.vk_dataclasses import Message, Update, UpdateObject
from kts_backend.users.views.models import Player

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.game_store: dict[int, Game] = {}
        self.rabbit_channel = None
        self.rabbit_connect = None

    async def connect(self, app: "Application"):
        games: list[GameModel] = (
            await self.app.store.games.get_all_active_games()
        )
        for game in games:
            players = []
            for p in game.players:
                stocks = {}
                for c in game.companys:
                    stocks[c.title] = []
                for s in p.stocks:
                    obj = Stock(
                        id=s.id,
                        owner_id=s.owner_id,
                        company_id=s.company_id,
                        game_id=s.game_id
                    )
                    stocks[s.company.title].append(obj)
                players.append(
                    Player(
                        id=p.id,
                        vk_id=p.vk_id,
                        name=p.name,
                        last_name=p.last_name,
                        game_id=p.game_id,
                        capital=p.capital,
                        clear_capital=p.clear_capital,
                        stocks=stocks
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
                current_round=game.current_round,
                id=game.id
            )

    async def start_consume(self, app: "Application"):
        self.rabbit_connect = await rq_con(
                "amqp://guest:guest@rabbitmq:5672/"
        )
        async with self.rabbit_connect:
            self.rabbit_channel = await self.rabbit_connect.channel()
            await self.rabbit_channel.set_qos(prefetch_count=1)

            queue = await self.rabbit_channel.declare_queue(
                "test_queue",
                durable=True,
            )

            await queue.consume(self.reciver)
            await asyncio.Future()

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            if '/help' in update.object.body:
                message = (
                    'Привет, я бот для игры Биржа.<br>'
                    'Для инициализации игры нужно написать команду:<br>'
                    '"/start <количество раундов>"<br>'
                    '<br>Все присутствуюище в чате буду считаться '
                    'как игроки, у каждого '
                    'на счету будет по 1000 очков '
                    'которые можно тратить на покупку '
                    'акций компаний.<br><br>Компаний в игре 3: a, b и с. '
                    'Изначальная цена акций - 100 очков. В ходе игры '
                    'она будет изменяться в случайном порядке.<br><br>'
                    'Игра состоит из раундов, после инициализации '
                    'нужно использовать команду "/round" для того, '
                    'чтобы его начать. Он продлится 60 секунд, в ходе '
                    'которых можно использовать две команды:<br>'
                    '"/buy <название компании>", "/sell <название компании>".'
                    '<br><br>После завершения раунда происходит рассчет '
                    'новых стоимостей акций и корректировка очков '
                    'пользователей с учетом новых цен.<br><br>'
                    'Победителем считается тот, у кого в конце игры будет '
                    'Сумарно больше всех очков "на счету" и "на руках"<br><br>'
                    'Команды доступные для использования ЛЮБОЕ время при '
                    'условии начатой игры:<br>'
                    '"/stats" - статистика игроков<br>'
                    '"/companys" - текущие цены на акции компаний<br>'
                    '"/game_stats" - общая статистика по игре<br>'
                    '"/last_game" - статистика последней завершенной игры'
                    '<br>"/stop_game" - полная остановка и завершение игры'
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/start' in update.object.body:
                if update.object.peer_id in self.game_store:
                    return await self.send_message(
                        text='Уже есть активная игра',
                        peer_id=update.object.peer_id
                    )
                splited = update.object.body.split()
                if len(splited) != 2:
                    return await self.send_message(
                        text='Нужно указать число раундов',
                        peer_id=update.object.peer_id
                    )
                try:
                    max_rounds = int(update.object.body.split()[1])
                except ValueError:
                    return await self.send_message(
                        text='Нужно указать число раундов числом',
                        peer_id=update.object.peer_id
                    )
                game = await self.app.store.games.create_game(
                    update.object.peer_id, max_rounds
                )
                raw_players: list[Player] = (
                    await self.app.store.vk_api.get_conversation_members(
                        update.object.peer_id
                    )
                )
                to_create = []
                for player in raw_players:
                    player.game_id = game.id
                    player.clear_capital = 1000
                    player.capital = 0
                    to_create.append(player)
                players = await self.app.store.users.create_players(
                    to_create
                )
                print(players)
                companys = await self.app.store.games.create_companys(game.id)
                message = 'Игра успешно создана'
                active_game: GameModel = (
                    await self.app.store.games.get_active_game(game.chat_id)
                )
                game_players = []
                for player in active_game.players:
                    game_players.append(Player(
                        id=player.id,
                        vk_id=player.vk_id,
                        name=player.name,
                        last_name=player.last_name,
                        stocks={c.title: [] for c in companys},
                        capital=player.capital,
                        clear_capital=player.clear_capital,
                        game_id=active_game.id
                    ))
                print(game_players)
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
                    players={p.vk_id: p for p in game_players},
                    companys={c.title: c for c in companys},
                    game_id=active_game.id,
                    is_active=active_game.is_active,
                    chat_id=active_game.chat_id,
                    max_rounds=active_game.max_rounds,
                    id=active_game.id
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/round' in update.object.body:
                result = (
                    await self.game_store[update.object.peer_id].start_round()
                )
                if type(result) is str:
                    return await self.send_message(
                        text=result,
                        peer_id=update.object.peer_id
                    )
                await self.send_message(
                    text='Раунд начался.',
                    peer_id=update.object.peer_id
                )
                result.add_done_callback(
                    lambda x: asyncio.create_task(
                        self._round_end_update(update)
                    )
                )

            if '/buy' in update.object.body:
                if len(update.object.body.split()) != 2:
                    return await self.send_message(
                        text='Нужно укзать название компании',
                        peer_id=update.object.peer_id
                    )
                company_title = update.object.body.split()[1]
                message = (
                    await self.game_store[update.object.peer_id].buy_stock(
                        company_title, update.object.user_id
                    )
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/sell' in update.object.body:
                if len(update.object.body.split()) != 2:
                    return await self.send_message(
                        text='Нужно укзать название компании',
                        peer_id=update.object.peer_id
                    )
                company_title = update.object.body.split()[1]
                message = (
                    await self.game_store[update.object.peer_id].sell_stock(
                        company_title, update.object.user_id
                    )
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/stats' in update.object.body:
                if update.object.peer_id not in self.game_store:
                    message = 'Нет активной игры'
                    return await self.send_message(
                        text=message,
                        peer_id=update.object.peer_id
                    )
                message = (
                    await self.game_store[update.object.peer_id]
                    .get_current_stats()
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/companys' in update.object.body:
                if update.object.peer_id not in self.game_store:
                    message = 'Нет активной игры'
                    return await self.send_message(
                        text=message,
                        peer_id=update.object.peer_id
                    )
                message = (
                    await self.game_store[update.object.peer_id]
                    .get_company_stats()
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )

            if '/game_stats' in update.object.body:
                message = (
                    await self.game_store[update.object.peer_id]
                    .get_game_stats()
                )
                await self.send_message(
                    text=message,
                    peer_id=update.object.peer_id
                )
            if '/stop_game' in update.object.body:
                if update.object.peer_id in self.game_store:
                    await self.end_game(update)
                else:
                    await self.send_message(
                        text='Нет активных игр',
                        peer_id=update.object.peer_id
                    )

            if '/last_game' in update.object.body:
                pass

    async def _round_end_update(self, update: Update):
        game: Game = self.game_store[update.object.peer_id]
        if game.is_active is True:
            text = await game.get_game_stats()
            message = f'Раунд окончен.<br>{text}'
            await self.send_message(
                text=message,
                peer_id=update.object.peer_id
            )
            game = await self.app.store.games.update_game_conditions(game)
        else:
            text = await game.get_game_stats()
            message = f'Игра завершена.<br>{text}'
            await self.send_message(
                text=message,
                peer_id=update.object.peer_id
            )
            game = await self.app.store.games.update_game_conditions(game)
            del self.game_store[update.object.peer_id]

    async def end_game(self, update):
        game: Game = self.game_store[update.object.peer_id]
        await game.stop_game()
        text = await game.get_game_stats()
        message = f'Игра завершена.<br>{text}'
        await self.send_message(
            text=message,
            peer_id=update.object.peer_id
        )
        game = await self.app.store.games.update_game_conditions(game)
        del self.game_store[update.object.peer_id]

    async def send_message(self, peer_id, text):
        queue = await self.rabbit_channel.declare_queue(
                "send_queue",
                durable=True,
                )
        mess_body = json.dumps({'peer_id': peer_id, 'text': text})
        await self.rabbit_channel.default_exchange.publish(
            PikaMes(
                mess_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key='send_queue'
        )

    async def reciver(self, mess: AbstractIncomingMessage):
        async with mess.process():
            updates = mess.body
            updates = json.loads(updates)
            to_handle = []
            for update in updates:
                to_handle.append(Update(
                    type=update["type"],
                    object=UpdateObject(
                        id=update["object"]['message']["id"],
                        user_id=update["object"]['message']["from_id"],
                        body=update["object"]['message']["text"],
                        peer_id=update['object']['message']['peer_id']
                    )
                    )
                )
            await self.handle_updates(to_handle)
