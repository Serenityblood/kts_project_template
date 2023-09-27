from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from kts_backend.games.models import Stock
from kts_backend.store.database.sqlalchemy_database import db


@dataclass
class Player:
    id: int
    vk_id: int
    name: str
    last_name: str
    game_id: str
    capital: int
    clear_capital: int
    stocks: dict[str, list[Stock]]


class PlayerModel(db):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    last_name = Column(String)
    game_id = Column(ForeignKey('games.id', ondelete='CASCADE'))
    game = relationship('GameModel', back_populates='players')
    capital = Column(Integer, nullable=False, default=0)
    clear_capital = Column(Integer, nullable=False, default=1000)
    stocks = relationship('StockModel', back_populates='player')
