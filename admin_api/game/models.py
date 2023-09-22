from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, ForeignKey

from kts_backend.store.database.sqlalchemy_database import db


@dataclass
class Company:
    id: int
    title: str
    capital: int
    current_stock_price: int


class CompanyModel(db):
    __tablename__ = 'companys'
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    current_stock_price = Column(Integer)


class StockModel(db):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True)
    price = Column(Integer, nullable=False)
    owner_id = Column(ForeignKey('players.id', ondelete='CASCADE'))
    company_id = Column(ForeignKey('companys.id', ondelete='CASCADE'))
