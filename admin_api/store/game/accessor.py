from admin_api.base.base_accessor import BaseAccessor

from sqlalchemy import select, delete
from sqlalchemy.exc import NoResultFound

from admin_api.game.models import Company, CompanyModel


class GameAccessor(BaseAccessor):
    async def create_company(
            self, title: str, current_stock_price: int
    ):
        company = CompanyModel(
            title=title,
            current_stock_price=current_stock_price
        )
        async with self.app.database.session.begin() as session:
            session.add(company)
            await session.commit()
        return Company(
            id=company.id,
            capital=0,
            title=company.title,
            current_stock_price=company.current_stock_price
        )

    async def list_companys(self) -> list[Company] or None:
        async with self.app.database.session.begin() as session:
            res = await session.execute(select(CompanyModel))
            try:
                companys = res.scalars().all()
                result = []
                for company in companys:
                    result.append(Company(
                        id=company.id,
                        capital=0,
                        title=company.title,
                        current_stock_price=company.current_stock_price
                        )
                    )
            except NoResultFound:
                return None
            return result

    async def clear_companys(self) -> True or False:
        async with self.app.database.session.begin() as session:
            session.execute(delete(CompanyModel))
            await session.commit()
        return True

    async def get_company_by_title(self, title: str):
        async with self.app.database.session.begin() as session:
            res = await session.execute(select(CompanyModel).where(CompanyModel.title == title))
            try:
                company = res.scalar_one()
                return Company(
                    id=company.id,
                    capital=0,
                    title=company.title,
                    current_stock_price=company.current_stock_price
                )
            except NoResultFound:
                return None
