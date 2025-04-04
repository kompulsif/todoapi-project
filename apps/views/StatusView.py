from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.controllers.auth.utils import get_current_user
from apps.controllers.StatusController import StatusController
from apps.controllers.utils import other_exception_handle
from apps.models.body.Status import BodyStatus
from apps.models.exceptions import DefaultStatusFound, StatusNotFound
from apps.models.response.status import Status, StatusListResponse
from apps.models.response.success import SuccessResponse
from logger import setup_logger

view_status = APIRouter(prefix="/status", tags=["Status"])
status_controller = StatusController()
user_depends = Annotated[dict, Depends(get_current_user)]

logger = setup_logger("bp_logger")


@view_status.get("/get/{status_id}/", response_model=Status)
async def get_status_by_id(user: user_depends, status_id: str) -> JSONResponse:
    """
    Status id bilgisine gore status bilgilerini getirir
    """
    if status_id.isnumeric():
        user["status_id"] = status_id
        try:
            resp = await status_controller.get_status_info(user["user_id"], int(status_id))
            return JSONResponse(resp, 200)

        except StatusNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(
                exc,
                user,
                status_controller.columnDescriptions,
                logger,
            )

    else:
        return JSONResponse({"detail": "The task id must be numerical!"}, 400)


@view_status.get("/list/", response_model=StatusListResponse)
async def get_status_list(user: user_depends) -> JSONResponse:
    """
    Status listesini getirir
    """
    try:
        resp = await status_controller.get_status_list(user["user_id"])
        return JSONResponse(resp)

    except Exception as exc:
        return other_exception_handle(
            exc,
            user,
            status_controller.columnDescriptions,
            logger,
        )


@view_status.post("/create/", response_model=SuccessResponse)
async def create_status(user: user_depends, status_data: BodyStatus) -> JSONResponse:
    """
    Body ile yeni bir status bilgisi alir
    Ve uyumluysa yeni bir status olusturur
    """
    try:
        resp = await status_controller.status_create(user["user_id"], status_data.title)
        return JSONResponse(resp, 200)

    except Exception as exc:
        return other_exception_handle(
            exc,
            status_data.model_dump(),
            status_controller.columnDescriptions,
            logger,
        )


@view_status.patch("/update/{status_id}/", response_model=SuccessResponse)
async def update_status_by_id(user: user_depends, status_id: str, status_data: BodyStatus) -> JSONResponse:
    """
    Status id bilgisine gore, gelen status body bilgisiyle
    statusu gunceller
    """
    if status_id.isnumeric():
        try:
            resp = await status_controller.status_update(user["user_id"], int(status_id), status_data.title)
            return JSONResponse(resp, 200)

        except StatusNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            data = user.update(status_data.model_dump())
            return other_exception_handle(exc, data, status_controller.columnDescriptions, logger)
    else:
        return JSONResponse({"detail": "The status id must be numerical!"}, 400)


@view_status.delete("/delete/{status_id}/", response_model=SuccessResponse)
async def delete_status_by_id(user: user_depends, status_id: str) -> JSONResponse:
    """
    Status id bilgisine karsilik gelen statusu siler
    """
    if status_id.isnumeric():
        user["status_id"] = status_id
        try:
            resp = await status_controller.status_delete(user["user_id"], int(status_id))
            return JSONResponse(resp, 200)

        except (StatusNotFound, DefaultStatusFound) as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(exc, user, status_controller.columnDescriptions, logger)
    else:
        return JSONResponse({"detail": "The status id must be numerical!"}, 400)
