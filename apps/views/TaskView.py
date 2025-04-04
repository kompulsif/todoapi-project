from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.controllers.auth.utils import get_current_user
from apps.controllers.TaskController import TaskController
from apps.controllers.utils import other_exception_handle
from apps.models.body.Task import BodyTask
from apps.models.exceptions import (
    PriorityNotFound,
    StatusNotFound,
    TaskNotFound,
)
from apps.models.response.success import SuccessResponse
from apps.models.response.task import Task, TaskListResponse
from logger import setup_logger

view_task = APIRouter(prefix="/task", tags=["Task"])
logger = setup_logger("view_task")
task_controller = TaskController()
user_depens = Annotated[dict, Depends(get_current_user)]


@view_task.get("/get/{task_id}/", response_model=Task)
async def get_task_info_by_id(user: user_depens, task_id: str) -> JSONResponse:
    """
    id bilgisine karsilik gelen task bilgisini doner
    """
    if task_id.isnumeric():
        try:
            resp = await task_controller.get_task(user["user_id"], task_id)
            return JSONResponse(resp, 200)

        except TaskNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(
                exc,
                {"task_id": task_id, "user": user},
                task_controller.columnDescriptions,
                logger,
            )
    else:
        return JSONResponse({"detail": "The task id must be numerical!"}, 400)


@view_task.get("/list/", response_model=TaskListResponse)
async def task_list(user: user_depens) -> JSONResponse:
    """
    kullaniciya ait task listesini doner
    """
    try:
        resp = await task_controller.get_task_list(user["user_id"])

        return JSONResponse(resp, 200)

    except Exception as exc:
        return other_exception_handle(
            exc,
            user,
            task_controller.columnDescriptions,
            logger,
        )


@view_task.post("/create/", response_model=SuccessResponse)
async def create_task(user: user_depens, task_data: BodyTask) -> JSONResponse:
    """
    gelen task body bilgisiyle yeni bir task olusturur
    """
    if task_data.check_task_for_create():
        data = task_data.model_dump()
        data.update(user)
        try:
            resp = await task_controller.task_create(user["user_id"], task_data)
            return JSONResponse(resp, 200)

        except (PriorityNotFound, StatusNotFound) as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(
                exc,
                data,
                task_controller.columnDescriptions,
                logger,
            )
    else:
        return JSONResponse({"required": "title, content, status, priority", "optional": "estimated_end_date"}, 400)


@view_task.patch("/update/{task_id}/", response_model=SuccessResponse)
async def update_task_by_id(user: user_depens, task_id: str, task_data: BodyTask) -> JSONResponse:
    """
    gelen id bilgisine gore ilgili taski, task body verisiyle gunceller
    """
    if task_id.isnumeric():
        data = task_data.model_dump()
        data["task_id"] = task_id
        try:
            resp = await task_controller.task_update(user["user_id"], int(task_id), task_data)
            return JSONResponse(resp, 200)

        except TaskNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(
                exc,
                data,
                task_controller.columnDescriptions,
                logger,
            )
    else:
        return JSONResponse({"detail": "The task id must be numerical!"}, 400)


@view_task.delete("/delete/{task_id}/", response_model=SuccessResponse)
async def delete_task_by_id(user: user_depens, task_id: str) -> JSONResponse:
    """
    gelen id bilgisine karislik gelen taski siler
    """
    if task_id.isnumeric():
        user.update({"task_id": task_id})
        try:
            resp = await task_controller.task_delete(user["user_id"], task_id)
            return JSONResponse(resp, 200)

        except TaskNotFound as exc:
            return JSONResponse({"detail": exc.message}, 400)

        except Exception as exc:
            return other_exception_handle(
                exc,
                user,
                task_controller.columnDescriptions,
                logger,
            )
    else:
        return JSONResponse({"detail": "The task id must be numerical!"}, 400)
