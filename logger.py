from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger
import logging
import os


class LoggerJsonFormatter(jsonlogger.JsonFormatter):
    """
    JSON biciminde loglari tutabilmemizi saglar
    """

    def add_fields(self, log_record, record, message_dict):
        message_dict = {} if not message_dict else message_dict
        super().add_fields(log_record, record, message_dict)

        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()

        else:
            log_record["level"] = record.levelname


def setup_logger(name: str, file_name: str = ""):
    """
    Yeni bir logger nesnesi olusturur
    Bu sekilde her dosyada loglama yapilabilir
    """
    file_name = "process.log" if not file_name else file_name

    base_dir = os.path.dirname(__file__)
    log_path = os.path.join(base_dir, "logs", file_name)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = LoggerJsonFormatter("%(timestamp)s | [%(level)s] - [%(name)s] - [%(message)s]")

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
