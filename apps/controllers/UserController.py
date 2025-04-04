from apps.models.body.User import BodyUser
from apps.models.db import DBUser
from apps.models.exceptions import UserNotFound
from .StatusController import StatusController
from .PriorityController import PriorityController
from database import db_session
from logger import setup_logger

logger = setup_logger("USER_CONTROLLER")


class UserController:
    """
    Kullanici veritabani islemlerini yonetir
    """

    columnDescriptions = {
        "visibility_name": "Visibility Name",
        "email": "Email",
        "password": "Password",
    }

    @staticmethod
    async def get_user_info(id: int) -> dict:
        """
        Kullanici bilgisini doner
        """
        with db_session() as session:
            user = session.query(DBUser).where(DBUser.id == id).limit(1).one_or_none()
            if user:
                return user.user_info()
            else:
                logger.info("User not found for information", extra={"user_id": id})
                raise UserNotFound("User not found!")

    @staticmethod
    async def add_new_user(user_data: BodyUser) -> dict:
        """
        Yeni bir kullanici olusturur
        """
        with db_session() as session:
            new_user = DBUser(**user_data.model_dump())
            session.add(new_user)
            session.flush()
        await StatusController.status_create(new_user.id, "Done", True)
        await PriorityController.priority_create(new_user.id, "High")
        return {"detail": "New user created!"}

    @staticmethod
    async def update_user(user_data: BodyUser, user_id: int) -> dict:
        """
        Kullaniciyi verilen bilgilerle gunceller
        """

        with db_session() as session:
            user = session.query(DBUser).where(DBUser.id == user_id).limit(1).one_or_none()
            if user:
                for column, value in user_data.model_dump(exclude_unset=True, exclude_none=True).items():
                    if hasattr(user, column):
                        setattr(user, column, value)

                return {"detail": "User update successfully!"}
            else:
                user_data = user_data.model_dump()
                user_data["user_id"] = user_id
                logger.info("User not found for update", extra=user_data)
                raise UserNotFound("User not found!")

    @staticmethod
    async def delete_user(user_id: int) -> dict:
        """
        Kullaniciyi siler
        """
        with db_session() as session:
            user = session.query(DBUser).where(DBUser.id == user_id).limit(1).one_or_none()
            if user:
                session.delete(user)
                return {"detail": "User delete is successfully!"}
            else:
                logger.info("User not found for delete", extra={"user_id": user_id})
                raise UserNotFound("User not found!")
