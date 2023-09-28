import asyncio
import random

from kts_backend.users.views.models import Player
from kts_backend.games.models import Company, Stock


class Game:
    def __init__(
            self,
            id: int,
            players: dict[int, Player],
            companys: dict[str, Company],
            max_rounds: int,
            game_id: int = None,
            is_active: bool = None,
            chat_id: int = None,
            round_in_progress: bool = False,
            current_round: int = 0,
    ):
        self.current_round = current_round
        self.round_in_progress = round_in_progress
        self.companys = companys
        self.players = players
        self.is_active = is_active
        self.game_id = game_id
        self.chat_id = chat_id
        self.max_rounds = max_rounds
        self.id = id

    async def start(self):
        self.current_round = 0
        self.is_active = True

    async def start_round(self):
        if self.is_active is False:
            return 'Нет активных игр'
        self.current_round += 1
        self.round_in_progress = True
        asyncio.get_running_loop().call_later(
            60,
            lambda: asyncio.ensure_future(self.stop_round())
        )
        return 'Раунд начался'

    async def stop_round(self):
        self.round_in_progress = False
        self.current_round += 1
        for _, player in self.players.items():
            player.capital = 0
        for _, company in self.companys.items():
            state = random.randint(0, 1)
            if state == 1:
                company.current_stock_price *= random.randint(
                    1, 3
                )
            else:
                company.current_stock_price /= random.randint(
                    1, 3
                )
            for _, player in self.players.items():
                player.capital += len(
                    player.stocks[company.title]
                ) * company.current_stock_price
            if self.current_round == self.max_rounds:
                self.is_active = False

    async def buy_stock(self, company_title, user_id):
        if self.round_in_progress is False:
            return 'Раунд закончился или не начался'
        if company_title not in self.companys:
            return 'такой компании нет'
        user = self.players[user_id]
        company = self.companys[company_title]
        if user.clear_capital >= company.current_stock_price:
            user.stocks[company.title].append(Stock(
                id=None,
                owner_id=user.id,
                company_id=company.id,
                game_id=self.game_id
            ))
            user.clear_capital -= company.current_stock_price
            user.capital += company.current_stock_price
            return 'Успешная покупка'
        return 'Не хватает денег'

    async def sell_stock(self, company_title, user_id):
        if self.round_in_progress is False:
            return 'Раунд закончился или не начался'
        if company_title not in self.companys:
            return 'Такой компании нет'
        user = self.players[user_id]
        company = self.companys[company_title]
        if len(user.stocks[company.title]) > 0:
            user.stocks[company.title].pop()
        user.capital -= company.current_stock_price
        user.clear_capital += company.current_stock_price
        return 'Продано'

    async def stop_game(self):
        self.is_active = False

    async def get_current_stats(self):
        message = ''
        for _, player in self.players.items():
            message += f'{player.name}: {player.capital} в акциях, {player.clear_capital} - на руках.<br>'
        return message

    async def get_company_stats(self):
        message = ''
        for _, company in self.companys.items():
            message += f'{company.title}: цена акций {company.current_stock_price}.<br>'
        return message

    async def get_game_stats(self):
        message = ''
        message += (
            await self.get_current_stats()
            + await self.get_company_stats()
            + str(self.current_round) + ' - текущий раунд'
        )
        return message
