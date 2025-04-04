from apps.models.db import DBTaskStatus
from apps.models.exceptions import StatusNotFound, DefaultStatusFound
from database import db_session
from logger import setup_logger

logger = setup_logger("STATUS_CONTROLLER")


class StatusController:
    """
    Status ile ilgili islemleri kontrol eder
    """

    columnDescriptions = {"title": "Title"}

    @staticmethod
    async def get_status_info(user_id: int, status_id: int) -> dict:
        """
        verilen spesifik statunun bilgisini doner
        """
        with db_session() as session:
            status = (
                session.query(DBTaskStatus)
                .where((DBTaskStatus.user_id == user_id) & (DBTaskStatus.id == status_id))
                .limit(1)
                .one_or_none()
            )
            if status:
                return status.status_info()
            else:
                logger.info("Status not found for information", extra={"user_id": user_id, "status_id": status_id})
                raise StatusNotFound("Status not found!")

    @staticmethod
    async def get_status_list(user_id: int) -> dict:
        """
        verilen kullanci id bilgisine ait statu listesini doner
        """
        with db_session() as session:
            status_list = session.query(DBTaskStatus).where(DBTaskStatus.user_id == user_id).all()
            dictStatus = [status.status_info() for status in status_list]
            return {"count": len(dictStatus), "results": dictStatus}

    @staticmethod
    async def status_create(user_id: int, title: str, default_status: bool = False) -> dict:
        """
        yeni bir status olusturur

        default_status parametresi, sadece yeni kullanici olusturuldugunda kullanilir
        bu parametre ile ilgili kullaniciya ait hangi status degerinin;
        "Tamamlandi/Done" bilgisine esit oldugu belirlenir
        Bu bilgi task reminder celery gorevinde kullanilir.
        Bu sayede hangi statunun bitis statusu oldugu bilinir.
        Kullanici controller ile bunu degistiremez. Sadece adini guncelleyebilir.
        """
        with db_session() as session:
            new_status = DBTaskStatus(title=title, user_id=user_id, default_status=default_status)
            session.add(new_status)
            return {"detail": "Status create successfully!"}

    @staticmethod
    async def status_update(user_id: int, status_id: int, title: str) -> dict:
        """
        Mevcut status bilgisini gunceller
        """
        with db_session() as session:
            status = (
                session.query(DBTaskStatus)
                .where((DBTaskStatus.user_id == user_id) & (DBTaskStatus.id == status_id))
                .limit(1)
                .one_or_none()
            )
            if status:
                status.title = title
                return {"message": "Status update successfully!"}
            else:
                logger.info("Status not found for update", extra={"user_id": user_id, "status_id": status_id})
                raise StatusNotFound("Status not found!")

    @staticmethod
    async def status_delete(user_id: int, status_id: int) -> dict:
        """
        Status bilgisini siler
        """
        with db_session() as session:
            status = (
                session.query(DBTaskStatus)
                .where((DBTaskStatus.id == status_id) & (DBTaskStatus.user_id == user_id))
                .limit(1)
                .one_or_none()
            )
            if status:
                if status.default_status:
                    # Bu statu bilgisi "Tamamlandi" statusunu temsil eder
                    # Task Mail islemleri bu id degerine gore yapilir
                    # Dolayisiyla silinemez. Sadece adi degistirilebilir.
                    raise DefaultStatusFound("This status is the default. Indelible!")
                session.delete(status)
                return {"detail": "Status delete successfully!"}
            else:
                logger.info("Status not found for information", extra={"user_id": user_id, "status_id": status_id})
                raise StatusNotFound("Status not found!")
