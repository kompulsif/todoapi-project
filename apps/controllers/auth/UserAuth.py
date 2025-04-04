import time

from fastapi import status
from fastapi.responses import JSONResponse
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadData
from jose import JWTError, jwt

from apps.celery_app.tasks.email.tasks import send_activate_account_mail, send_tfa_code_mail
from apps.controllers.auth.utils import (
    authenticate_user,
    create_authorized_response,
    create_tfa_code_with_user_info,
    create_tokens,
    create_verify_token_with_user_info,
)
from apps.controllers.utils import create_custom_json_response, get_redis_connection
from apps.models.db.UserModel import DBUser
from apps.models.exceptions.query import UserNotFound
from config import (
    ACCESS_TOKEN_EXP,
    ACCOUNT_VERIFY_TOKEN_EXP,
    JTI_REDIS_DB,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXP,
    SITE_DOMAIN,
    TFA_LOGIN_REDIS_DB,
    TFA_SECRET_KEY,
    TOKEN_ALGORITHM,
)
from database import db_session
from logger import setup_logger

from .utils import get_refresh_jti_and_exp

logger = setup_logger("AUTH_CONTROLLER")


class UserAuthController:
    @staticmethod
    async def login(username: str, password: str, ip_addr: str):
        """
        Kullanici hesap durumuna gore login islemlerini calistirir
        Hesabi acilmis fakat aktiflestirilmemis olanlara aktivasyon maili gonderilir
        Aktive edilmis fakat hesabi iki asamali dogrulama ile korunuyorsa, tfa maili gonderilir
        """
        user = await authenticate_user(username, password)
        if not user:
            return JSONResponse(
                {"detail": "Incorrect username or password"},
                status.HTTP_401_UNAUTHORIZED,
            )

        try:
            if user.user_approved is False:
                resp = await UserAuthController.send_activate_mail_for_auth(user.id)
                logger.info("User activation link is sent", extra={"username": username, "ip": ip_addr})
                return resp

            if user.two_factor_auth is True:
                resp = await UserAuthController.send_tfa_mail_for_auth(user.id)
                two_factor_response = await create_authorized_response(
                    str(user.id), username, auth_type="two_factor", response_code=401
                )
                logger.info("User TFA code is sent", extra={"username": username, "ip": ip_addr})
                return two_factor_response

        except Exception:
            logger.error("An error ocurred in user login.", extra={"username": username, "ip": ip_addr})
            return JSONResponse({"detail": "An error ocurred! Please try again later"}, 500)

        direct_response = await create_authorized_response(str(user.id), username, delete_cookie_list=["tfa_token"])
        logger.info("User direct login is successful", extra={"username": username, "ip": ip_addr})
        return direct_response

    @staticmethod
    async def logout(authorization: str, refresh_token: str | None, delete_user: str | None, ip_addr: str):
        """
        Kulanici cikis islemlerini yonetir
        JWT - JTI bilgileri cozulur ve JTI blacklist kontrolu yapilir.
        Cozulen bilgiler rediste yoksa suresi ile birlikte redise eklenir.
        Burda "yoksa" kontrolunun yapilmasinin sebebi, eger varsa ve tekrar set edilirse
        rediste saklanma suresininde yenilenecegidir bu da fazladan rediste yer tutmasini saglar

        Kullanici hesap silme islemi yapmis olabilir. Bu durumda logout yonlendirilmesi yapilir.
        delete_user bilgisi bu nedenle gonderilir
        """
        if authorization.startswith("Bearer "):
            authorization = authorization[7:]

        payload_access_token = jwt.decode(authorization, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        jti_access_token = payload_access_token.get("jti")
        username = payload_access_token.get("name")

        redis_client = await get_redis_connection(JTI_REDIS_DB)

        if not (await redis_client.exists(f"blacklist_jti:{jti_access_token}")):
            redis_jti_access_exp = ACCESS_TOKEN_EXP * 60
            await redis_client.setex(f"blacklist_jti:{jti_access_token}", redis_jti_access_exp, "")
        else:
            logger.info("User access token used", extra={"username": username, "ip": ip_addr})
            return await create_custom_json_response({"detail": "Access token used!"}, 400, ["refresh_token"])

        if refresh_token is not None:
            refresh_jti, redis_refresh_jti_exp = await get_refresh_jti_and_exp(refresh_token)
            if refresh_jti:
                await redis_client.setex(f"blacklist_jti:{refresh_jti}", redis_refresh_jti_exp, "")

        delete_cookie_list = ["refresh_token", "tfa_token"]
        if delete_user == "true":
            logger.info("User delete request for logout", extra={"username": username, "ip": ip_addr})
            delete_cookie_list.append("delete_user")
            user_id = payload_access_token.get("sub")
            await redis_client.setex(f"blacklist_user:{user_id}", REFRESH_TOKEN_EXP * 86400, "")

        logger.info("User logout successful", extra={"username": username, "ip": ip_addr})
        return await create_custom_json_response({"detail": "Logout Successful"}, 200, delete_cookie_list)

    @staticmethod
    async def user_token_refresh(ip_addr: str, refresh_token: str):
        """
        Access JWT suresi bittikten sonra tokeni yenilemek icin kullanilir
        Yeni bir access jwt token uretilir ve dondurulur.
        """
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
            jti = payload.get("jti")
            username = payload.get("name")
            redis = await get_redis_connection(JTI_REDIS_DB)

            if await redis.exists(f"blacklist_jti:{jti}"):
                logger.info("User refresh token used", extra={"username": username, "ip": ip_addr})
                return await create_custom_json_response({"detail": "Refresh token used!"}, 401, ["refresh_token"])

            user_id = payload.get("sub")
            old_exp_date = payload.get("exp")
            redis_exp_date = int(old_exp_date - time.time())
            redis_exp_date = 0 if redis_exp_date <= 0 else redis_exp_date
            last_access_token = await create_tokens(user_id, username, False)

            await redis.setex(f"blacklist_jti:{jti}", redis_exp_date, "")

            response_headers = {"Authorization": f"Bearer {last_access_token}"}
            logger.info("Last access token is created", extra={"username": username, "ip": ip_addr})
            return await create_custom_json_response(
                {"detail": "Last access token is created"}, 200, ["refresh_token", "tfa_token"], response_headers
            )

        except JWTError:
            logger.info("User refresh token is not valid", extra={"ip": ip_addr})
            return await create_custom_json_response({"detail": "Refresh token is not valid!"}, 401, ["refresh_token"])

    @staticmethod
    async def login_with_tfa(ip_addr: str, token: str, code: str):
        """
        Iki adimli dogrulama girisini kontrol eder
        """
        try:
            payload = jwt.decode(token, TFA_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
            jti = payload.get("jti")
            user_id = payload.get("sub")
            redis = await get_redis_connection(JTI_REDIS_DB)

            if await redis.exists(f"blacklist_jti:{jti}"):
                logger.info("TFA token is used", extra={"user_id": user_id, "ip": ip_addr})
                return await create_custom_json_response(
                    {"detail": "TFA Token is used!"}, 401, delete_cookie_list=["tfa_token", "refresh_token"]
                )

            if not (await UserAuthController.code_verify(f"tfa_code:{user_id}", code)):
                logger.info("TFA Code is not valid", extra={"user_id": user_id, "ip": ip_addr})
                return await create_custom_json_response(
                    {"detail": "TFA Code is not valid!"}, 401, delete_cookie_list=["refresh_token"]
                )
            await redis.delete(f"tfa_code:{user_id}")
            username = payload.get("name")
            old_exp_date = payload.get("exp")

            redis_exp_date = int(old_exp_date - time.time())
            redis_exp_date = 0 if redis_exp_date <= 0 else redis_exp_date

            await redis.setex(f"blacklist_jti:{jti}", redis_exp_date, "")
            authorized_response = await create_authorized_response(user_id, username, delete_cookie_list=["tfa_token"])

            logger.info("Login with TFA is successful", extra={"username": username, "ip": ip_addr})
            return authorized_response

        except JWTError:
            logger.info("User TFA token is not valid", extra={"ip": ip_addr})
            return await create_custom_json_response(
                {"detail": "TFA Token is not valid"}, 401, delete_cookie_list=["tfa_token", "refresh_token"]
            )

    @staticmethod
    async def user_verify_account(ip_addr: str, token: str):
        """
        Kullanici hesabi dogrulama islemlerini kontrol eder
        """
        try:
            serializer = URLSafeTimedSerializer(secret_key=JWT_SECRET_KEY)
            token_info = serializer.loads(token, max_age=ACCOUNT_VERIFY_TOKEN_EXP * 3600)
            user_id = token_info["user_id"]
            verify_token_jti = token_info["jti"]
            redis = await get_redis_connection(JTI_REDIS_DB)
            if not (await redis.exists(f"blacklist_jti:{verify_token_jti}")):
                with db_session() as session:
                    user = session.query(DBUser).where(DBUser.id == user_id).limit(1).one_or_none()
                    if user:
                        user.user_approved = True
                    else:
                        raise UserNotFound("User not found!")

                await redis.setex(f"blacklist_jti:{verify_token_jti}", ACCOUNT_VERIFY_TOKEN_EXP * 3600, "")
                logger.info("User approved", extra={"user_id": user_id, "ip": ip_addr})
                return JSONResponse({"detail": "User approved!"}, status_code=200)

            else:
                logger.info("User already approved", extra={"user_id": user_id, "ip": ip_addr})
                return JSONResponse({"detail": "User already approved!"}, status_code=409)

        except BadData:
            logger.info("Verify token is not valid", extra={"ip": ip_addr})
            return JSONResponse({"detail": "Verify token is not valid!"}, status_code=401)

    @staticmethod
    async def send_activate_mail_for_auth(user_id: int):
        """
        Controller tarafinda aktivasyon mail gonderim islemini tetikler
        """
        email, username, token = await create_verify_token_with_user_info(user_id)
        verify_link = SITE_DOMAIN + "/auth/verify/" + token
        send_activate_account_mail.apply_async(args=(verify_link, email, username))
        return JSONResponse(
            {"detail": "Your account is not verified! The verification link has been sent to your mail address"},
            status_code=401,
        )

    @staticmethod
    async def send_tfa_mail_for_auth(user_id: int):
        """
        Controller tarafinda TFA code mail gonderim islemini tetikler
        """
        email, username, code = await create_tfa_code_with_user_info(user_id)
        send_tfa_code_mail.apply_async(args=(code, email, username))

    @staticmethod
    async def code_verify(key: str, code: str):
        """
        Verilen TFA kodunun dogrulugunu kontrol eder
        """
        redis_client = await get_redis_connection(TFA_LOGIN_REDIS_DB)
        value: str = await redis_client.get(key)
        return value is not None and value == code
