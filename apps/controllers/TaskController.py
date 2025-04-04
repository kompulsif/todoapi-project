from apps.models.body.Task import BodyTask
from apps.models.db import DBTask, DBTaskPriority, DBTaskStatus
from apps.models.exceptions import (
    PriorityNotFound,
    StatusNotFound,
    TaskNotFound,
)
from database import db_session
from logger import setup_logger

logger = setup_logger("TASK_CONTROLLER")


class TaskController:
    """
    Task veritabani islemlerini kontrol eder
    """

    columnDescriptions: dict = {
        "title": "Title",
        "content": "Content",
        "status": "Status",
        "priority": "Priority",
    }

    @staticmethod
    async def get_task(user_id: int, task_id: int) -> dict:
        """
        Kullaniciya ait task bilgisini getirir
        """
        with db_session() as session:
            task = (
                session.query(DBTask).where((DBTask.user_id == user_id) & (DBTask.id == task_id)).limit(1).one_or_none()
            )
            if task:
                return task.task_info()
            else:
                logger.info("Task not found", extra={"user_id": user_id, "task_id": task_id})
                raise TaskNotFound("Task not found!")

    @staticmethod
    async def get_task_list(user_id: int) -> dict:
        """
        Kullancinin task bilgilerini doner
        """
        with db_session() as session:
            tasks = session.query(DBTask).where((DBTask.user_id == user_id)).all()
            dictTasks = [task.task_info() for task in tasks]
            return {"count": len(dictTasks), "results": dictTasks}

    @staticmethod
    async def task_create(user_id: int, task_data: BodyTask) -> dict:
        """
        Kullaniciya ait bir task olusturur
        """
        with db_session() as session:
            priority = (
                session.query(DBTaskPriority).where(DBTaskPriority.id == task_data.priority).limit(1).one_or_none()
            )
            if priority:
                status = session.query(DBTaskStatus).where(DBTaskStatus.id == task_data.status).limit(1).one_or_none()
                if not status:
                    logger.info(
                        "Status not found for task create", extra={"user_id": user_id, "status_id": task_data.status}
                    )
                    raise StatusNotFound("Status not found!")
            else:
                logger.info(
                    "Priority not found for task create", extra={"user_id": user_id, "priority_id": task_data.priority}
                )
                raise PriorityNotFound("Priority not found!")

            model_data = task_data.model_dump()
            model_data["user_id"] = user_id
            new_task = DBTask(**model_data)
            session.add(new_task)
            return {"detail": "Task create successfully!"}

    @staticmethod
    async def task_update(user_id: int, task_id: int, task_data: BodyTask) -> dict:
        """
        Kullanciya ait taski gunceller
        """
        with db_session() as session:
            uTask = (
                session.query(DBTask).where((DBTask.user_id == user_id) & (DBTask.id == task_id)).limit(1).one_or_none()
            )
            if uTask:
                for column, value in task_data.model_dump(exclude_none=True, exclude_unset=True).items():
                    setattr(uTask, column, value)
                return {"detail": "Task update successfully!"}
            else:
                logger.info("Task not found for update", extra={"user_id": user_id, "task_id": task_id})
                raise TaskNotFound("Task not found!")

    @staticmethod
    async def task_delete(user_id: int, task_id: int) -> dict:
        """
        Kullaniciya ait taski siler
        """
        with db_session() as session:
            task = (
                session.query(DBTask).where((DBTask.user_id == user_id) & (DBTask.id == task_id)).limit(1).one_or_none()
            )
            if task:
                session.delete(task)
                return {"detail": "Task delete successfully!"}
            else:
                logger.info("Task not found for delete", extra={"user_id": user_id, "task_id": task_id})
                raise TaskNotFound("Task not found!")
