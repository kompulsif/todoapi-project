from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base


class DBUser(Base):
    """
    Veritabani User tablosu modeli
    """

    __tablename__ = "User"

    id = Column(Integer, primary_key=True)
    visibility_name = Column(String(30), nullable=False, unique=True)
    email = Column(String(254), nullable=False, unique=True)
    user_approved = Column(Boolean(), default=False, nullable=False)
    two_factor_auth = Column(Boolean(), default=False, nullable=False)
    password = Column(String(100), nullable=False)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def user_info(self) -> dict:
        """
        Ilgili kayita ait tum kolonlarin bilgilerini doner
        """
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}
