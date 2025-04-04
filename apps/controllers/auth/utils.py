import random
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from itsdangerous import URLSafeTimedSerializer
from jose import JWTError, jwt
from passlib.context import CryptContext
from logger import setup_logger

from apps.controllers.utils import get_redis_connection
from apps.models.db.UserModel import DBUser
from apps.models.exceptions.query import UserNotFound
from config import (
    ACCESS_TOKEN_EXP,
    TFA_TOKEN_EXP,
    TOKEN_ALGORITHM,
    JWT_SECRET_KEY,
    TFA_SECRET_KEY,
    REFRESH_TOKEN_EXP,
    TFA_LOGIN_REDIS_DB,
)
from database import db_session

bcrypt.__about__ = bcrypt

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/user/login")

logger = setup_logger("AUTH_CONTROLLER_UTILS")


async def get_refresh_jti_and_exp(refresh_token: str) -> tuple[str, int] | tuple[bool]:
    """
    refresh token JTI bilgisini ve token kalan zamanini saniye cinsinden doner
    """
    try:
        payload_refresh_token = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        jti_refresh_token = payload_refresh_token.get("jti")

        jti_refresh_exp = payload_refresh_token.get("exp")
        redis_jti_refresh_exp = int(jti_refresh_exp - time.time())  # seconds

        return jti_refresh_token, redis_jti_refresh_exp

    except JWTError:
        return False, False


async def authenticate_user(username: str, password: str) -> DBUser | bool:
    """
    Kullanici bilgileri eslesirse True
    Eslesmezse False Doner
    """
    with db_session() as session:
        user = session.query(DBUser).where(DBUser.visibility_name == username).limit(1).one_or_none()
        if not user:
            return False
        if not bcrypt_context.verify(password, user.password):
            return False
        return user


async def create_tokens(
    user_id: str, username: str, include_refresh_token: bool = True, code_type: str = "0"
) -> tuple[str]:
    """
    Kullaniciya ait, belirli paremetrelerle erisim tokenleri olusturur
    """
    if code_type == "0":
        """
        code_type 0 ise, kullanici girisi dogrulanmistir ve tokenler gereklidir
        """
        access_token_exp = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXP)
        access_token_encode = {"sub": user_id, "name": username, "exp": access_token_exp, "jti": str(uuid4())}
        access_token = jwt.encode(access_token_encode, JWT_SECRET_KEY, algorithm=TOKEN_ALGORITHM)

        if include_refresh_token:
            refresh_token_exp = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_EXP)
            refresh_token_encode = {"sub": user_id, "name": username, "exp": refresh_token_exp, "jti": str(uuid4())}
            refresh_token = jwt.encode(refresh_token_encode, JWT_SECRET_KEY, algorithm=TOKEN_ALGORITHM)
            return access_token, refresh_token

        return access_token

    elif code_type == "1":
        """
        code_type 1 ise, kullanici login islemini TFA ile yapiyordur bilgileri daha dogrulanmamistir
        Bu nedenle oncelikle TFA_TOKEN ile dogrulama icin diger islemleri tamamlamalidir
        """
        tfa_token_payload_exp = datetime.now(tz=timezone.utc) + timedelta(minutes=TFA_TOKEN_EXP)
        tfa_token_encode = {"sub": user_id, "name": username, "exp": tfa_token_payload_exp, "jti": str(uuid4())}
        tfa_token = jwt.encode(tfa_token_encode, TFA_SECRET_KEY, algorithm=TOKEN_ALGORITHM)
        return tfa_token


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> dict:
    """
    Gelen isteklerde Authorization Header kontrol edilerek
    istegi atan kullanicinin bilgilerinii alir
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id: int = payload.get("sub", None)
        username: str = payload.get("name", None)

        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")

        return {"username": username, "user_id": user_id}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")


async def create_authorized_response(
    user_id: str,
    username: str,
    auth_type: str = "direct",
    delete_cookie_list: list = [],
    response_code: int = 200,
):
    """
    Kullanici yetkilendirme islemleri icin ozellestirilmis cevaplar olusturur
    """
    if auth_type == "direct":
        access_token, refresh_token = await create_tokens(user_id, username)

        response = JSONResponse(
            {"access_token": access_token, "token_type": "bearer", "login_type": auth_type},
            response_code,
        )
        cookie_exp = REFRESH_TOKEN_EXP * 86400
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=cookie_exp,
        )
        for cookie in delete_cookie_list:
            response.delete_cookie(cookie)

        return response

    elif auth_type == "two_factor":
        tfa_token = await create_tokens(user_id, username, code_type="1")
        response = JSONResponse({"login_type": auth_type}, response_code)
        cookie_exp = TFA_TOKEN_EXP * 60
        response.set_cookie(
            key="tfa_token",
            value=tfa_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=cookie_exp,
        )
        for cookie in delete_cookie_list:
            response.delete_cookie(cookie)

        return response


async def check_jwt_exp(token: str):
    """
    Verilen tokenin suresinin gecerlilik durumunu doner
    """
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
    except JWTError:
        return False
    return True


async def get_active_user(user_id: int):
    """
    Verilen id bilgisine sahip kullaniciyi doner
    """
    with db_session() as session:
        user = session.query(DBUser).where(DBUser.id == user_id).limit(1).one_or_none()
    if user is None:
        raise UserNotFound("User not found!")
    return user


async def get_tfa_code_exp(tfa_token: str):
    """
    Gelen token bilgisini cozumleyerek, ilgili kullanciya ait
    TFA Kodu (eger varsa) son kullanim suresini dondurur
    """
    try:
        payload = jwt.decode(tfa_token, TFA_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        user_id = payload.get("sub")

        redis_client = await get_redis_connection(TFA_LOGIN_REDIS_DB)
        key = f"tfa_code:{user_id}"
        exp = await redis_client.ttl(key)
        if exp is None or exp <= 0:
            return JSONResponse({"key": key, "exp": 0})
        return JSONResponse({"key": key, "exp": exp})

    except JWTError:
        return JSONResponse({"detail": "TFA Token is not valid!"})


async def create_verify_token_with_user_info(user_id: int):
    """
    Kullanici hesabi dogrulamasi icin token olusturur
    Kullancinin bilgileri ile beraber doner
    """
    user = await get_active_user(user_id)
    serializer = URLSafeTimedSerializer(JWT_SECRET_KEY)
    data = {"user_id": user_id, "jti": str(uuid4())}
    token = serializer.dumps(data)
    return user.email, user.visibility_name, token


async def create_tfa_code_with_user_info(user_id: int):
    """
    TFA icin kod olusturur ve kullanici bilgileri ile doner
    """
    user = await get_active_user(user_id)
    redis_client = await get_redis_connection(TFA_LOGIN_REDIS_DB)
    code = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(6))
    second = TFA_TOKEN_EXP * 60
    await redis_client.setex(f"tfa_code:{user_id}", second, code)
    return user.email, user.visibility_name, code
