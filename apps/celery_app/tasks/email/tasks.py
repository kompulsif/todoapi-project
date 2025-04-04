import asyncio
import socket
from datetime import datetime
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException

from celery.exceptions import Ignore
from celery.states import IGNORED

from apps.celery_app import app
from apps.celery_app.constants import task_retry_kwargs
from apps.celery_app.tasks import DBActionTask
from apps.controllers.auth.utils import get_active_user
from apps.controllers.MailController import MailController
from apps.controllers.StatusController import StatusController
from apps.models.db.TaskModel import DBTask
from apps.models.exceptions.celery import RetryTaskException
from apps.models.exceptions.query import StatusNotFound, UserNotFound
from logger import setup_logger

email_task_logger = setup_logger("EMAIL_TASKS")


@app.task(bind=True, base=DBActionTask)
def check_end_dates(self):
    """
    Tasklerin tarihlerini ve durumlarini kontrol eder.
    Eger tarihi gecmis ve task tamamlanmamis durumda ise
    Task kullanicisina hatirlatma amacli mail gonderilir
    """

    with self.session as session:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tasks: list[DBTask] = (
            session.query(DBTask).where((DBTask.estimated_end_date != None) & (DBTask.estimated_end_date <= now)).all()
        )
        for task in tasks:
            end_date = task.estimated_end_date.strftime("%Y-%m-%d %H:%M:%S")
            send_todo_estimate_mail.apply_async((task.user_id, task.status, task.title, end_date))


@app.task(**task_retry_kwargs)
def send_activate_account_mail(self, link: str, email: str, username: str):
    """
    Aktivasyon islemi tamamlanmamis kullanicinin mail gonderimini tetikler
    """
    try:
        mail_controller = MailController(email, username)
        mail_controller.send_verify_mail(link)
    except socket.gaierror:
        email_task_logger.error("Mail Server Address Error")
        raise RetryTaskException

    except SMTPAuthenticationError:
        email_task_logger.error("Authentication error", exc_info=True)
        raise RetryTaskException

    except SMTPConnectError:
        email_task_logger.error("Connection error", exc_info=True)
        raise RetryTaskException

    except (SMTPException, socket.timeout):
        email_task_logger.error("SMTP error", exc_info=True)
        raise RetryTaskException

    except Exception:
        email_task_logger.error("Unexpected error", exc_info=True)
        raise RetryTaskException


@app.task(**task_retry_kwargs)
def send_tfa_code_mail(self, code: str, email: str, username: str):
    """
    TFA ile giris yapan kullanicinin mailine kod gonderimini tetikler
    """
    try:
        mail_controller = MailController(email, username)
        mail_controller.send_tfa_mail(code)
    except socket.gaierror:
        email_task_logger.error("Mail Server Address Error")
        raise RetryTaskException

    except SMTPAuthenticationError:
        email_task_logger.error("Authentication error", exc_info=True)
        raise RetryTaskException

    except SMTPConnectError:
        email_task_logger.error("Connection error", exc_info=True)
        raise RetryTaskException

    except (SMTPException, socket.timeout):
        email_task_logger.error("SMTP error", exc_info=True)
        raise RetryTaskException

    except Exception:
        email_task_logger.error("Unexpected error", exc_info=True)
        raise RetryTaskException


@app.task(**task_retry_kwargs)
def send_todo_estimate_mail(self, user_id: int, status_id: int, task_name: str, task_estimate_date: str):
    """
    Tahmini bitis suresi gecmis ve Statu degeri "Tamamlandi/Done" statusu(default_status) olmayan
    task'lerin hepsine dair kullaniciya mail gonderimini tetikler
    """
    try:
        status = asyncio.run(StatusController.get_status_info(user_id, status_id))
        if status["default_status"]:
            user = asyncio.run(get_active_user(user_id))
            try:
                mail_controller = MailController(user.email, user.visibility_name)
                mail_controller.send_task_overdue_mail(task_name, task_estimate_date)
            except socket.gaierror:
                email_task_logger.error("Mail Server Address Error")
                raise RetryTaskException

            except SMTPAuthenticationError:
                email_task_logger.error("Authentication error", exc_info=True)
                raise RetryTaskException

            except SMTPConnectError:
                email_task_logger.error("Connection error", exc_info=True)
                raise RetryTaskException

            except (SMTPException, socket.timeout):
                email_task_logger.error("SMTP error", exc_info=True)
                raise RetryTaskException

            except Exception:
                email_task_logger.error("Unexpected error", exc_info=True)
                raise RetryTaskException
        else:
            raise StatusNotFound("Status is not default")  # Status default degilse yukseltilebilir
    except UserNotFound:
        email_task_logger.info("User not found", extra={"user_id": user_id})
        self.update_state(state=IGNORED, meta={"reason": "User not found!"})
        raise Ignore()

    except StatusNotFound:
        email_task_logger.info(
            "Status is not default", extra={"user_id": user_id, "status_id": status_id, "task_name": task_name}
        )
        self.update_state(state=IGNORED, meta={"reason": "Status is not default"})
        raise Ignore()
