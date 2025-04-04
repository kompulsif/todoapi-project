from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from database import Base


class DBTask(Base):
    """
    Veritabani Task tablosu modeli
    """

    __tablename__ = "Task"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"))
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Integer, ForeignKey("TaskStatus.id", ondelete="CASCADE", onupdate="CASCADE"))
    priority = Column(Integer, ForeignKey("TaskPriority.id", ondelete="CASCADE", onupdate="CASCADE"))
    estimated_end_date = Column(DateTime(timezone=True), nullable=True, server_default=None)
    date_created = Column(DateTime(timezone=True), default=func.now())
    date_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def task_info(self) -> dict:
        """
        Ilgili kayita ait tum kolonlarin bilgilerini doner
        datetime tipindeki kolonlar JSONResponse ile serialize edilemez
        Bu nedenle burada direkt strftime yapilarak dondurulur
        """
        info = {}
        for db_column in self.__table__.columns:
            column = getattr(self, db_column.name)
            if isinstance(column, datetime):
                info[db_column.name] = column.strftime("%Y-%m-%d %H:%M:%S")
            else:
                info[db_column.name] = column
        return info
