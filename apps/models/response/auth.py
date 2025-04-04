from pydantic import BaseModel


class DirectLoginResponse(BaseModel):
    access_token: str
    token_type: str
    login_type: str

class RefreshTokenResponse(BaseModel):
    refresh_token: str


class KeyExpResponse(BaseModel):
    key: str
    key_exp: int
