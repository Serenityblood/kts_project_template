from dataclasses import dataclass

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from kts_backend.store.database.sqlalchemy_database import db


@dataclass
class Stock:
    id: int
    owner_id: int
    company_id: int
    game_id: int


@dataclass
class Company:
    id: int
    title: str
    current_stock_price: int
    game_id: int


class GameModel(db):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, nullable=False)
    players = relationship('PlayerModel', back_populates='game')
    is_active = Column(Boolean, nullable=False, default=False)
    current_round = Column(Integer, default=0)
    companys = relationship('InGameCompanyModel', back_populates='game')
    max_rounds = Column(Integer, nullable=False)
    stocks = relationship('StockModel', back_populates='game')


class InGameCompanyModel(db):
    __tablename__ = 'ingamecompanys'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    current_stock_price = Column(Integer)
    game_id = Column(ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    game = relationship('GameModel', back_populates='companys')
    stocks = relationship('StockModel', back_populates='company')


class StockModel(db):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    owner_id = Column(ForeignKey('players.id', ondelete='CASCADE'))
    player = relationship('PlayerModel', back_populates='stocks')
    company_id = Column(ForeignKey('ingamecompanys.id', ondelete='CASCADE'))
    company = relationship('InGameCompanyModel', back_populates='stocks')
    game_id = Column(ForeignKey('games.id', ondelete='CASCADE'))
    game = relationship('GameModel', back_populates='stocks')
