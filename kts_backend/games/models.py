from dataclasses import dataclass

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from admin_api.game.models import CompanyModel
from kts_backend.store.database.sqlalchemy_database import db


class GameModel(db):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, nullable=False)
    scores = relationship('ScoreModel', back_populates='game')
    is_active = Column(Boolean, nullable=False, default=True)
    current_round = Column(Integer, default=0)
    companys = relationship('InGameCompanys', back_populates='game')


class ScoreModel(db):
    __tablename__ = 'scores'

    player_id = Column(
        Integer, ForeignKey('players.id', ondelete='CASCADE'), primary_key=True
    )
    player = relationship('PlayerModel', back_populates='scores')
    game_id = Column(
        Integer, ForeignKey('games.id', ondelete='CASCADE'), primary_key=True
    )
    game = relationship('GameModel', back_populates='scores')
    capital = Column(Integer, nullable=False, default=0)
    clear_capital = Column(Integer, nullable=False, default=0)


class InGameCompanyModel(db):
    __tablename__ = 'ingamecompanys'

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    current_stock_price = Column(Integer)
    game_id = Column(ForeignKey('games.id'), nullable=False)
    game = relationship('GameModel', back_populates='companys')
    stocks = relationship('StocModel', back_populates='company')
