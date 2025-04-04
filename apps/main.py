from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.controllers.auth.MiddleWare import AuthMiddleware
from apps.controllers.RedisController import RedisController
from apps.controllers.utils import check_mail_server
from apps.models.db.utils import create_dbs
from apps.views.AuthView import view_auth
from apps.views.PriorityView import view_priority
from apps.views.StatusView import view_status
from apps.views.TaskView import view_task
from apps.views.UserView import view_user
from logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI uygulamasi calistigi anda yapilacak on kontrolleri calistirir
    """
    try:
        manager = RedisController(0)
        await manager.get_redis()
        logger.info("Redis server active")
        await create_dbs()
        logger.info("Database setup completed")
        await check_mail_server()
        logger.info("Mail server active")
        yield
    except Exception:
        logger.error("FastAPI Lifespan Error", exc_info=True)
        await manager.close()
        raise


app = FastAPI(lifespan=lifespan)
logger = setup_logger("MAIN_LOGGER")


@app.exception_handler(RequestValidationError)
async def http_exception_accept_handler(request: Request, exc: RequestValidationError) -> Response:
    """
    Isteklerde olusabilecek pydantic value error hatalarini ele alir

    Bu hatalar isteklerde gonderilen body datanin gecerli olmadigi
    veya beklenen model ile uyusmadiginda olusur
    """
    logger.error("User body data validation error", exc_info=True)
    msg_list: dict[str, str] = {}
    for err in exc.errors():
        if err["type"] == "missing":
            try:
                columnName = err["loc"][1]
                msg_list["required"] = msg_list.get("required", []) + [columnName]
            except IndexError:
                msg_list["Post Data Error"] = "Body data is required!"

        elif err["type"] == "json_invalid":
            msg_list["Json Error"] = "Invalid request body!"

        elif err["type"] == "value_error":
            msg_list["Value Error"] = err["msg"]

        elif err["type"].endswith("_type"):
            inputs = ",".join(err["loc"][1:])
            msg_list["Type Eror"] = f"{inputs}; {err['msg']}"

        elif err["type"] == "bool_parsing":
            inputs = ",".join(err["loc"][1:])
            msg_list["Parsing Error"] = f"{inputs}; {err['msg']}"

    return JSONResponse(content={"detail": msg_list}, status_code=400)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization"],
)

app.add_middleware(AuthMiddleware)

logger.debug("CORS & MiddleWare Configured!")

app.include_router(view_auth)
app.include_router(view_user)
app.include_router(view_priority)
app.include_router(view_status)
app.include_router(view_task)

logger.debug("Views Configured!")
