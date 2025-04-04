from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String

from database import Base


class DBTaskPriority(Base):
    """
    Veritabani Priority tablosu modeli
    """

    __tablename__ = "TaskPriority"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"))
    title = Column(String(30), CheckConstraint("title!=''"), nullable=False, unique=True)

    def priority_info(self) -> dict:
        """
        Ilgili kayita ait tum kolonlarin bilgilerini doner
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
