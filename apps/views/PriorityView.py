from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.controllers.auth.utils import get_current_user
from apps.controllers.PriorityController import PriorityController
from apps.controllers.utils import other_exception_handle
from apps.models.body.Priority import BodyPriority
from apps.models.exceptions import PriorityNotFound
from apps.models.response.priority import Priority, PriorityListResponse
from apps.models.response.success import SuccessResponse
from logger import setup_logger

view_priority = APIRouter(prefix="/priority", tags=["Priority"])
logger = setup_logger("view_priority")
priority_controller = PriorityController()
user_depens = Annotated[dict, Depends(get_current_user)]


@view_priority.get("/get/{priority_id}/", response_model=Priority)
async def get_priority_by_id(user: user_depens, priority_id: str) -> JSONResponse:
    """
    id bilgisine gore priority bilgisini getirir
    """
    if priority_id.isnumeric():
        try:
            resp = await priority_controller.get_priority_info(user["user_id"], int(priority_id))
            return JSONResponse(resp, 200)

        except PriorityNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            user["priority_id"] = priority_id
            return other_exception_handle(
                exc,
                user,
                priority_controller.columnDescriptions,
                logger,
            )

    else:
        return JSONResponse({"detail": "The priority id must be numerical!"}, 400)


@view_priority.get("/list/", response_model=PriorityListResponse)
async def get_priority_list(user: user_depens) -> JSONResponse:
    """
    Kullanciya ait tum priority listesini doner
    """
    try:
        resp = await priority_controller.get_priority_list(user["user_id"])
        return resp

    except Exception as exc:
        return other_exception_handle(
            exc,
            user,
            priority_controller.columnDescriptions,
            logger,
        )


@view_priority.post("/create/", response_model=SuccessResponse)
async def create_priority(user: user_depens, priority_data: BodyPriority) -> JSONResponse:
    """
    Gelen priority body bilgisi ile yeni bir priorirty olusturur
    """
    try:
        resp = await priority_controller.priority_create(user["user_id"], priority_data.title)
        return JSONResponse(resp, 201)

    except Exception as exc:
        return other_exception_handle(exc, priority_data.model_dump(), priority_controller.columnDescriptions, logger)


@view_priority.patch("/update/{priority_id}/", response_model=SuccessResponse)
async def update_priority_by_id(user: user_depens, priority_id: str, priority: BodyPriority) -> JSONResponse:
    """
    id bilgisine gore, gelen priority body ile birlikte priority gunceller
    """
    if priority_id.isnumeric():
        data = priority.model_dump()
        data["id"] = priority_id
        data.update(user)
        try:
            resp = await priority_controller.priority_update(user["user_id"], int(priority_id), priority.title)
            return JSONResponse(resp, 200)

        except PriorityNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(exc, data, priority_controller.columnDescriptions, logger)
    else:
        return JSONResponse({"detail": "The priority id must be numerical!"}, 400)


@view_priority.delete("/delete/{priority_id}/", response_model=SuccessResponse)
async def delete_priority_by_id(user: user_depens, priority_id: str) -> JSONResponse:
    """
    Id bilgisine gore priority siler
    """
    if priority_id.isnumeric():
        user["priority_id"] = priority_id
        try:
            resp = await priority_controller.priority_delete(user["user_id"], int(priority_id))
            return JSONResponse(resp, 200)

        except PriorityNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(exc, user, priority_controller.columnDescriptions, logger)
    else:
        return JSONResponse({"detail": "The priority id must be numerical!"}, 400)
