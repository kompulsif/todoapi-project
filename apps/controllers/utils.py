import socket
from logging import Logger
from smtplib import SMTP, SMTPAuthenticationError, SMTPConnectError, SMTPException

import redis.asyncio as redis
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from config import SMTP_PORT, SMTP_SERVER, SMTP_USER, SMTP_PASSWORD
from logger import setup_logger

from .RedisController import RedisController

logger = setup_logger("CONTROLLER_UTILS")


def other_exception_handle(exc: Exception, data: dict, columnDescriptions: dict, logger: Logger) -> JSONResponse:
    if isinstance(exc, SQLAlchemyError):
        msg = str(exc.orig).strip().lower()

        if msg.find("not null constraint") + 1:
            return JSONResponse(
                {"detail": "Please send all compulsory fields!"},
                status_code=400,
            )

        elif msg.find("unique constraint") + 1:
            excmsg, columname = msg.split(": ", 1)
            columname = columnDescriptions.get(columname.split(".", 1)[1], "Informations")
            return JSONResponse({"detail": f"{columname} is used"}, status_code=208)

        elif msg.find("FOREIGN KEY constraint failed") + 1:
            logger.error(f"Foreign key constraint error: {msg}", extra=data)
            return JSONResponse(
                {
                    "detail": "Foreign key control failed. Please make sure that the values ​​you enter agree with other table information!",
                },
                status_code=400,
            )

        elif msg.find("null value in column") + 1:
            return JSONResponse({"detail": "All necessary information should be sent"}, status_code=400)

    logger.critical(f"Unexpected error: {str(exc)}", extra=data)
    return JSONResponse({"detail": "Action Error"}, status_code=401)


async def get_redis_connection(db_index=0) -> redis.Redis:
    """
    Redis baglantisi saglar
    """
    try:
        manager = RedisController(db_index=db_index)
        redis_client = await manager.get_redis()
    except Exception:
        logger.error("Redis connection error", exc_info=True, extra={"DB": db_index})
        raise HTTPException(status_code=500, detail="Redis Server Error")

    return redis_client


async def create_custom_json_response(
    content: dict = {},
    status: int = 200,
    delete_cookie_list: list | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    """
    Ozellestirilebilir Json response olusturmamizi saglar.
    Her zaman her cookie gonderilmeyebilir, veya silinmesi istenenler olabilir
    Veya eklenmesi gereken headerlar olabilir
    Bu durumlari kontrol etmemizi kolaylastirir
    """
    response = JSONResponse(content=content, status_code=status, headers=headers)
    if delete_cookie_list is not None:
        for cookie in delete_cookie_list:
            response.delete_cookie(cookie, httponly=True, secure=True, samesite="strict")
    return response


async def check_mail_server() -> None:
    """
    Mail sunucusunun aktifligini kontrol eder
    """
    log_data = {"mail_server": SMTP_SERVER, "port": SMTP_PORT, "SMTP_USER": SMTP_USER}

    try:
        with SMTP(host=SMTP_SERVER, port=SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)

    except socket.gaierror:
        logger.error("Mail server socket error", exc_info=True, extra=log_data)
        raise

    except SMTPAuthenticationError:
        logger.error("Mail Server Authentication Error", exc_info=True, extra=log_data)
        raise

    except SMTPConnectError:
        logger.error("Mail server connection error", exc_info=True, extra=log_data)
        raise

    except (SMTPException, socket.timeout):
        logger.error("Mail server socket timout or SMTP error", exc_info=True, extra=log_data)
        raise

    except Exception:
        logger.critical("Mail server unexpected error", exc_info=True, extra=log_data)
        raise
