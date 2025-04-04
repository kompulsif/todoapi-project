import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apps.celery_app.constants import TEMPLATES_DIR
from config import (
    ACCOUNT_VERIFY_TOKEN_EXP,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USER,
    SMTP_PASSWORD,
    TFA_TOKEN_EXP,
)
from logger import setup_logger

mail_logger = setup_logger("MAIL_CONTROLLER")


class MailController:
    """
    Mail gonderim islemlerini kontrol eder
    """

    verify_template: str = None
    tfa_code_template: str = None
    task_overdue_template: str = None

    def __init__(self, recipient: str, username: str) -> None:
        self.recipient = recipient
        self.username = username
        MailController.set_templates()

    @classmethod
    def set_templates(cls) -> None:
        """
        Mail template bilgilerini ayarlar
        """
        if cls.verify_template is None:
            with open(TEMPLATES_DIR / "verify_account.html", "r", encoding="utf-8") as f:
                cls.verify_template = f.read()

        if cls.tfa_code_template is None:
            with open(TEMPLATES_DIR / "tfa_code.html", "r", encoding="utf-8") as f:
                cls.tfa_code_template = f.read()

        if cls.task_overdue_template is None:
            with open(TEMPLATES_DIR / "task_overdue.html", "r", encoding="utf-8") as f:
                cls.task_overdue_template = f.read()

    def send_mail(self, msg: MIMEMultipart) -> None:
        """
        Mail Server'a baglanarak maili gonderir
        """
        with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, self.recipient, msg.as_string())

    def get_tfa_message(self, code: str) -> MIMEMultipart:
        """
        TFA icin mail bilgilerini doldurup mesaji olusturur
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "TodoAPI: Two-Factor Authentication"
        msg["From"] = f"TodoAPI Project <{SMTP_USER}>"
        msg["To"] = self.recipient
        html_template = self.tfa_code_template.format(self.username, code, TFA_TOKEN_EXP)
        html_part = MIMEText(html_template, "html")
        msg.attach(html_part)
        return msg

    def get_verify_message(self, verify_link: str) -> MIMEMultipart:
        """
        Kullanici dogrulamasi icin mail bilgilerini doldurup mesaji olusturur
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "TodoAPI: Verify Account"
        msg["From"] = f"TodoAPI Project <{SMTP_USER}>"
        msg["To"] = self.recipient
        html_template = self.verify_template.format(
            self.username,
            ACCOUNT_VERIFY_TOKEN_EXP,
            verify_link,
            verify_link,
        )
        html_part = MIMEText(html_template, "html")
        msg.attach(html_part)
        return msg

    def get_task_overdue_message(self, task_name: str, task_estimate_date: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "TodoAPI: Task Overdue Notification"
        msg["From"] = f"TodoAPI Project <{SMTP_USER}>"
        msg["To"] = self.recipient
        html_template = self.task_overdue_template.format(
            self.username,
            task_name,
            task_estimate_date,
        )
        html_part = MIMEText(html_template, "html")
        msg.attach(html_part)
        return msg

    def send_verify_mail(self, verify_link: str) -> None:
        """
        Gelen bilgilerle mesaj hazirlayip, dogrulama mailini gonderir
        """
        msg = self.get_verify_message(verify_link)
        self.send_mail(msg)
        mail_logger.info("User verify mail is sent", extra={"to_username": self.username, "to_mail": self.recipient})

    def send_tfa_mail(self, code: str) -> None:
        """
        Gelen bilgilerle mesaj hazirlayip, TFA mailini gonderir
        """
        msg = self.get_tfa_message(code)
        self.send_mail(msg)
        mail_logger.info("User TFA mail is sent", extra={"to_username": self.username, "to_mail": self.recipient})

    def send_task_overdue_mail(self, task_name: str, task_estimate_date: str) -> None:
        """
        Gelen bilgilerle mesaj hazirlayip, tarihi gecen task bildirim mailini gonderir
        """
        msg = self.get_task_overdue_message(task_name, task_estimate_date)
        self.send_mail(msg)
        mail_logger.info("User task overdue mail is sent", extra={"to_user": self.username, "to_mail": self.recipient})
