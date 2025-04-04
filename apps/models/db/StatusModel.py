from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Boolean

from database import Base


class DBTaskStatus(Base):
    """
    Veritabani Status tablosu modeli
    """

    __tablename__ = "TaskStatus"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"))
    title = Column(String(30), CheckConstraint("title!=''"), nullable=False, unique=True)
    default_status = Column(Boolean(), nullable=False, default=False)

    def status_info(self) -> dict:
        """
        Ilgili kayita ait tum kolonlarin bilgilerini doner
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
