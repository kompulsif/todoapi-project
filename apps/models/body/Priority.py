from pydantic import BaseModel, field_validator


class BodyPriority(BaseModel):
    """
    Gelen isteklerde kullanilacak Priority modeli
    """

    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str):
        if len(value.strip()) < 3:
            raise ValueError("Priority title length should be more than 2")
        return value
