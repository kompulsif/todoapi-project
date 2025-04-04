from apps.models.db import DBTaskPriority
from apps.models.exceptions import PriorityNotFound
from database import db_session
from logger import setup_logger

logger = setup_logger("PRIORITY_CONTROLLER")


class PriorityController:
    """
    Priority ile ilgili islemleri kontrol eder
    """

    columnDescriptions = {"title": "Title"}

    @staticmethod
    async def get_priority_info(user_id: int, priority_id: int) -> dict:
        """
        Verilen spesifik prority'in bilgisini doner
        """
        with db_session() as session:
            priority = (
                session.query(DBTaskPriority)
                .where((DBTaskPriority.user_id == user_id) & (DBTaskPriority.id == priority_id))
                .limit(1)
                .one_or_none()
            )
            if priority:
                return priority.priority_info()
            else:
                logger.info(
                    "Priority not found for information", extra={"user_id": user_id, "priority_id": priority_id}
                )
                raise PriorityNotFound("Priority not found!")

    @staticmethod
    async def get_priority_list(user_id: int) -> dict:
        """
        Verilen kullanici id bilgisine ait priority listesini doner
        """
        with db_session() as session:
            priority_list = session.query(DBTaskPriority).where(DBTaskPriority.user_id == user_id).all()
            dictPriority = [priority.priority_info() for priority in priority_list]
            return {"count": len(dictPriority), "results": dictPriority}

    @staticmethod
    async def priority_create(user_id: int, title: str) -> dict:
        """
        Yeni bir priority olusturur
        """
        with db_session() as session:
            newPriority = DBTaskPriority(title=title, user_id=user_id)
            session.add(newPriority)
            return {"detail": "Priority create successfully!"}

    @staticmethod
    async def priority_update(user_id: int, priority_id: int, new_title: str) -> dict:
        """
        Mevcut priority bilgisini gunceller
        """
        with db_session() as session:
            task = (
                session.query(DBTaskPriority)
                .where((DBTaskPriority.id == priority_id) & (DBTaskPriority.user_id == user_id))
                .limit(1)
                .one_or_none()
            )
            if task:
                task.title = new_title
                return {"detail": "Priority update successfully!"}
            else:
                logger.info("Priority not found for update", extra={"user_id": user_id, "priority_id": priority_id})
                raise PriorityNotFound("Priority not found!")

    @staticmethod
    async def priority_delete(user_id: int, priority_id: str) -> dict:
        """
        Priority bilgisini siler
        """
        with db_session() as session:
            priority = (
                session.query(DBTaskPriority)
                .where((DBTaskPriority.id == priority_id) & (DBTaskPriority.user_id == user_id))
                .limit(1)
                .one_or_none()
            )
            if priority:
                session.delete(priority)
                return {"detail": "Priority delete successfully!"}
            else:
                logger.info("Priority not found for delete", extra={"user_id": user_id, "priority_id": priority_id})
                raise PriorityNotFound("Priority not found!")
