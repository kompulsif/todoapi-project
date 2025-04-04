from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    DB_CONNECTION_STRING: str
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int
    DB_POOL_TIMEOUT: int
    DB_POOL_RECYCLE: int
    LOG_FILE_NAME: str
    ACCESS_TOKEN_EXP: int
    REFRESH_TOKEN_EXP: int
    TFA_TOKEN_EXP: int
    ACCOUNT_VERIFY_TOKEN_EXP: int
    JWT_SECRET_KEY: str
    TFA_SECRET_KEY: str
    TOKEN_ALGORITHM: str
    REDIS_ADDR: str
    REDIS_PORT: int
    REDIS_USERNAME: str
    REDIS_PASSWORD: str
    JTI_REDIS_DB: int
    TFA_LOGIN_REDIS_DB: int
    redis_db: int
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SITE_DOMAIN: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


try:
    load_dotenv(Env.model_config.get("env_file"), override=True)  # type: ignore
    env = Env()  # type: ignore

except ValidationError:
    print("Env dosyaniz okunamadi!")
    quit()

DB_CONNECTION_STRING = env.DB_CONNECTION_STRING
DB_POOL_SIZE = env.DB_POOL_SIZE
DB_MAX_OVERFLOW = env.DB_MAX_OVERFLOW
DB_POOL_TIMEOUT = env.DB_POOL_TIMEOUT
DB_POOL_RECYCLE = env.DB_POOL_RECYCLE

LOG_FILE_NAME = env.LOG_FILE_NAME

ACCESS_TOKEN_EXP = env.ACCESS_TOKEN_EXP
REFRESH_TOKEN_EXP = env.REFRESH_TOKEN_EXP
TFA_TOKEN_EXP = env.TFA_TOKEN_EXP
ACCOUNT_VERIFY_TOKEN_EXP = env.ACCOUNT_VERIFY_TOKEN_EXP

REDIS_ADDR = env.REDIS_ADDR
REDIS_PORT = env.REDIS_PORT
REDIS_USERNAME = env.REDIS_USERNAME
REDIS_PASSWORD = env.REDIS_PASSWORD

JTI_REDIS_DB = env.JTI_REDIS_DB
TFA_LOGIN_REDIS_DB = env.TFA_LOGIN_REDIS_DB
redis_db = env.redis_db

JWT_SECRET_KEY = env.JWT_SECRET_KEY
TFA_SECRET_KEY = env.TFA_SECRET_KEY
TOKEN_ALGORITHM = env.TOKEN_ALGORITHM

SMTP_SERVER = env.SMTP_SERVER
SMTP_PORT = env.SMTP_PORT
SMTP_USER = env.SMTP_USER
SMTP_PASSWORD = env.SMTP_PASSWORD

SITE_DOMAIN = env.SITE_DOMAIN
