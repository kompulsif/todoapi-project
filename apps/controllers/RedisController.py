import redis.asyncio as redis
from fastapi import HTTPException
from redis.asyncio import ConnectionPool

from config import (
    REDIS_ADDR,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_USERNAME,
)
from logger import setup_logger

logger = setup_logger("REDIS_CONTROLLER")


class RedisController:
    """
    Redis islemlerini yoneten sinif
    Havuz mekanizmasi kullanir
    """

    _pools: dict[int, ConnectionPool] = {}

    def __init__(self, db_index: int = 0) -> None:
        self.host: str = REDIS_ADDR
        self.port: int = REDIS_PORT
        self.db_index: int = db_index
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Redis baglantisini baslatir (eger yoksa)"""
        if self.db_index not in RedisController._pools:
            RedisController._pools[self.db_index] = redis.ConnectionPool(
                host=self.host, port=self.port, db=self.db_index, decode_responses=True
            )

        self._redis = redis.Redis(
            connection_pool=RedisController._pools[self.db_index],
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
            socket_timeout=10,
        )

    async def get_redis(self) -> redis.Redis:
        """Redis baglantisini dondurur"""
        if self._redis is None:
            await self.connect()

        assert isinstance(self._redis, redis.Redis)  # mypy
        if not await self._redis.ping():
            logger.error("Redis Server connection refused")
            raise HTTPException(status_code=500, detail="Redis Server Error")
        return self._redis

    @classmethod
    async def close(cls) -> None:
        """Tum redis havuzunu kapatir"""
        for db_index, pool in cls._pools.items():
            await pool.disconnect()
            logger.info(f"Redis connection closed for DB_{db_index}")
        cls._pools.clear()
        logger.info("Redis pool is clean")
