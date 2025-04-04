from database import Base, engine


async def create_dbs():
    """
    Her baslatilista bu fonksiyon calistirilir.
    Veritabanlari yoksa olusturur
    """
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
