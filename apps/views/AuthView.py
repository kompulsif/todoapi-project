from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import JSONResponse

from apps.controllers.auth.UserAuth import UserAuthController
from apps.controllers.auth.utils import get_current_user, get_tfa_code_exp
from apps.controllers.UserController import UserController
from apps.controllers.utils import create_custom_json_response, other_exception_handle
from apps.models.body.User import TFACode
from apps.models.exceptions import UserNotFound
from apps.models.response.auth import KeyExpResponse, DirectLoginResponse
from apps.models.response.success import SuccessResponse
from logger import setup_logger

view_auth = APIRouter(prefix="/auth", tags=["Authorization/Authentication"])
logger = setup_logger("VIEW_AUTH")
user_controller = UserController()
user_auth_controller = UserAuthController()
user_depens = Annotated[dict, Depends(get_current_user)]


@view_auth.post("/tfa/login", response_model=DirectLoginResponse)
async def tfa_verify_for_login(
    request: Request, tfa_code_body: TFACode, tfa_token: Annotated[str | None, Cookie()] = None
) -> JSONResponse:
    """
    Iki asamali giris istegini isler
    """
    if tfa_token is not None:
        code = tfa_code_body.tfa_code
        resp = await user_auth_controller.login_with_tfa(request.client.host, tfa_token, code)
        return resp
    else:
        return JSONResponse({"detail": "TFA Token should be sent"})


@view_auth.post("/refresh", response_model=SuccessResponse)
async def show_refresh(request: Request, refresh_token: Annotated[str | None, Cookie()] = None) -> JSONResponse:
    """
    Yeni bir refresh token alinmasi istegini isler
    """
    if refresh_token is not None and refresh_token != "":
        json_response = await user_auth_controller.user_token_refresh(request.client.host, refresh_token)
        return json_response
    else:
        return await create_custom_json_response({"detail": "Refresh token is not valid!"}, 404, ["refresh_token"])


@view_auth.get("/tfa/exp", response_model=KeyExpResponse)
async def get_tfa_exp(tfa_token: Annotated[str | None, Cookie()] = None) -> JSONResponse:
    """
    TFA Kodunun gecerlilik suresini getirir
    """
    if tfa_token is not None:
        resp = await get_tfa_code_exp(tfa_token)
        return resp
    else:
        return JSONResponse({"detail": "TFA Token should be sent"})


@view_auth.get("/verify/{token}", response_model=SuccessResponse)
async def verify_account(request: Request, token: str) -> JSONResponse:
    """
    Kullanicinin hesap dogrulama istegini isler
    """
    try:
        verified_info_resp = await user_auth_controller.user_verify_account(request.client.host, token)
        return verified_info_resp

    except UserNotFound as exc:
        logger.info("Verify failed. User not found.", extra={"ip": request.client.host})
        return JSONResponse({"detail": exc.message}, 400)

    except Exception as exc:
        return other_exception_handle(
            exc,
            {"ip": request.client.host},
            user_controller.columnDescriptions,
            logger,
        )
