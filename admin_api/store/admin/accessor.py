import typing
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound

from admin_api.admin.models import AdminModel
from admin_api.base.base_accessor import BaseAccessor
from admin_api.web.app import Application

if typing.TYPE_CHECKING:
    from admin_api.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        self.app = app
        try:
            await self.create_admin(
                email=self.app.config.admin.email,
                password=sha256(
                    self.app.config.admin.password.encode()
                ).hexdigest()
            )
        except IntegrityError:
            return None

    async def get_by_email(self, email: str) -> AdminModel:
        async with self.app.database.session.begin() as session:
            result = await session.execute(select(AdminModel).where(
                AdminModel.email == email
            ))
            try:
                admin = result.scalar_one()
                return admin
            except NoResultFound:
                return None

    async def create_admin(self, email: str, password: str) -> AdminModel:
        admin = AdminModel(email=email, password=password)
        async with self.app.database.session.begin() as session:
            session.add(admin)
            await session.commit()
        return admin
