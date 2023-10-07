from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from sqlalchemy import Column, BigInteger, String

from kts_backend.store.database.sqlalchemy_database import db


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(BigInteger, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(), nullable=False)

    def is_password_valid(self, password: str) -> bool:
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(id=session["admin"]["id"], email=session["admin"]["email"])
