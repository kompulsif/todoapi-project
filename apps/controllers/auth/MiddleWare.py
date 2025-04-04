from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from apps.controllers.utils import get_redis_connection
from config import JTI_REDIS_DB, JWT_SECRET_KEY, TOKEN_ALGORITHM


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Istek basligindaki authorization token kullanilmissa veya kullanici hesabini silmis ise,
    suanki aktif hesaptan cikisi saglanir. Bu nedenle her istekte blacklist jti ve user kontrol yapilir.

    Hem authorization token manipulasyonunu engeller hem de farkli tarayici/cihazdan cikis yapilmasi durumunda
    atilan herhangi bir istekte anlik olarak diger tarayicilardan/cihazlardan cikisi yapilir
    """

    async def dispatch(self, request: Request, call_next):
        access_token = request.headers.get("authorization")

        if access_token and access_token.startswith("Bearer "):
            """
            Her kullanici isleminde access token yoktur
            Ornegin; Yeni bir kullanici olusturulurken JWT veya Refresh token kullanilmaz
            Veya kullanici dogrulamasi yapilirken vs.
            Bu nedenle burada bunu kontrol ediyoruz.
            """
            access_token = access_token[7:]
            try:
                payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
                jti = payload.get("jti")
                user_id = payload.get("sub")
                redis = await get_redis_connection(JTI_REDIS_DB)
                if await redis.exists(f"blacklist_jti:{jti}") or await redis.exists(f"blacklist_user:{user_id}"):
                    if request.url.path != "/user/logout":  # Logout yonlendirmesindeki sonsuz donguyu onler
                        response = RedirectResponse(url="/user/logout", status_code=307)
                        return response

                return await call_next(request)

            except JWTError:
                # user_depends islemlerinin calismasi icin pass gecilir
                pass

        return await call_next(request)
