from pydantic import BaseModel, field_validator
from passlib.context import CryptContext
from typing import Optional
from re import fullmatch


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TFACode(BaseModel):
    """
    Body ile gonderilecek TFA Code icin kullanilir
    """

    tfa_code: str


class BodyUser(BaseModel):
    """
    User islemlerindeki gelen requestler icin kullanilir
    """

    visibility_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    user_approved: Optional[bool] = False
    two_factor_auth: Optional[bool] = False

    def get_all_setted_fields(self):
        fields = self.model_dump(
            exclude_defaults=True,
            exclude_unset=True,
            exclude_none=True,
        )
        return fields

    def check_user_for_create(self):
        """
        Update isleminden oturu, null olabiliyor bu alanlar
        fakat olusutrma isleminde null olmamali
        """
        setted_fields = self.get_all_setted_fields()
        setted_fields.pop("user_approved", None)
        setted_fields.pop("two_factor_auth", None)
        return len(setted_fields) == 3

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value is None or not isinstance(value, str):
            raise ValueError("Password should be valid string!")
        if len(value) < 6:
            raise ValueError("Password length should be more than 6")

        hashed_pass = bcrypt_context.hash(value)
        return hashed_pass

    @field_validator("visibility_name")
    @classmethod
    def validate_visibility_name(cls, value: str):
        if not isinstance(value, str) or len(value) == 0:
            raise ValueError("Visibility name should be valid string!")
        if not fullmatch(r"\w+", value) and not value.replace("_", "").isalnum():
            raise ValueError(
                "Visibility name can only include A-Z and _ characters and should be alphabetical or alphanumeric"
            )
        if len(value) < 3:
            raise ValueError("Visibility Name length should be more than 3")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        if value is None or not isinstance(value, str):
            raise ValueError("Email should be valid string!")
        if not fullmatch(r"^\S+@\S+\.\S+$", value):
            raise ValueError("Email is not valid!")
        return value
