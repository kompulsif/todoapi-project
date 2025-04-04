from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from apps.controllers.auth.UserAuth import UserAuthController
from apps.controllers.auth.utils import check_jwt_exp, get_current_user
from apps.controllers.UserController import UserController
from apps.controllers.utils import other_exception_handle
from apps.models.body.User import BodyUser
from apps.models.exceptions import (
    UserDeleteFailed,
    UserNotFound,
    UserUpdateFailed,
    UserValidateException,
)
from apps.models.response.success import SuccessResponse
from apps.models.response.auth import DirectLoginResponse
from apps.models.response.user import User
from config import REFRESH_TOKEN_EXP
from logger import setup_logger

view_user = APIRouter(prefix="/user", tags=["User"])
logger = setup_logger("VIEW_USER")
user_controller = UserController()
user_auth_controller = UserAuthController()
user_depens = Annotated[dict, Depends(get_current_user)]


@view_user.post("/login", response_model=DirectLoginResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    authorization: Annotated[str, Header()] = None,
) -> JSONResponse:
    """
    Kullanici JWT login isteklerini isler

    Acik bir oturumu varsa istek islenmez

    Iki asamali dogrulama aciksa, mail adresine kod gonderir
    tfa_token cookie olusturulur
    /auth/tfa/login adresinden kodun girilmesi gerekir
    """
    if authorization is None or await check_jwt_exp(authorization):
        json_response = await user_auth_controller.login(form_data.username, form_data.password, request.client.host)
        return json_response
    else:
        logger.info(f"User session already open. Login failed. IP: {request.client.host}")
        return JSONResponse({"detail": "Your session is already open"}, status_code=400)


@view_user.post("/logout", response_model=SuccessResponse)
async def logout_user(
    user: user_depens,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    refresh_token: Annotated[str | None, Cookie()] = None,
    delete_user: Annotated[str | None, Cookie()] = None,
) -> JSONResponse:
    """
    Kullanici logout istegini isler
    """
    json_response = await user_auth_controller.logout(authorization, refresh_token, delete_user, request.client.host)
    return json_response


@view_user.post("/info/", response_model=User)
async def get_user(user: user_depens) -> JSONResponse:
    """
    JWT Token bilgisine gore kullanicinin bilgilerini doner
    """
    try:
        resp = await user_controller.get_user_info(user["user_id"])
        return JSONResponse(resp, 200)

    except UserNotFound as exc:
        return JSONResponse({"detail": exc.message}, 400)

    except Exception as exc:
        return other_exception_handle(
            exc,
            user,
            user_controller.columnDescriptions,
            logger,
        )


@view_user.post("/create/", response_model=SuccessResponse)
async def create_user(user_data: BodyUser, authorization: Annotated[str, Header()] = None) -> JSONResponse:
    """
    Yeni kullanici burada olusturulur
    Olusturulmasi icin oturumun kapali olmasi gerekmektedir ve bunu kontrol eder

    Yeni kullanici olusturulduktan sonra mail adresine aktivasyon linki gonderilir
    """

    if not authorization:
        if user_data.check_user_for_create():
            try:
                resp = await user_controller.add_new_user(user_data)
                return JSONResponse(resp, 201)

            except UserValidateException as exc:
                logger.info("User data is not valid for create", extra=user_data.model_dump())
                return JSONResponse({"detail": exc.message}, 400)

            except Exception as exc:
                return other_exception_handle(
                    exc,
                    user_data.model_dump(),
                    user_controller.columnDescriptions,
                    logger,
                )
        else:
            return JSONResponse({"detail": "visibility_name, email and password should be sent"}, 400)
    else:
        return JSONResponse({"detail": "Your session is already open"}, 404)


@view_user.patch("/update/", response_model=SuccessResponse)
async def update_user(user_data: BodyUser, user: user_depens) -> JSONResponse:
    """
    Kullanici guncelleme istegini isler
    """
    try:
        resp = await user_controller.update_user(user_data, user["user_id"])
        return JSONResponse(resp, 200)

    except (UserUpdateFailed, UserNotFound) as exc:
        return JSONResponse({"detail": exc.message}, 400)

    except Exception as exc:
        return other_exception_handle(
            exc,
            user_data.model_dump(),
            user_controller.columnDescriptions,
            logger,
        )


@view_user.post("/delete/", response_model=SuccessResponse)
async def delete_user(user: user_depens) -> JSONResponse:
    """
    Kullanici hesabi silme istegini isler
    Hesap silindikten sonra /user/logout yonlendirilmesi yapilir
    """
    try:
        await user_controller.delete_user(user["user_id"])
        response = RedirectResponse(url="/user/logout", status_code=307)
        cookie_exp = REFRESH_TOKEN_EXP * 86400
        response.set_cookie(
            "delete_user",
            "true",
            max_age=cookie_exp,
            httponly=True,
            secure=True,
            samesite="strict",
        )
        return response

    except (UserNotFound, UserDeleteFailed) as exc:
        return JSONResponse({"detail": exc.message}, 400)

    except Exception as exc:
        return other_exception_handle(
            exc,
            user,
            user_controller.columnDescriptions,
            logger,
        )
