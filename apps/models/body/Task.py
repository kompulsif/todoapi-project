from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class BodyTask(BaseModel):
    """
    Gelen isteklerde kullanilacak Task modeli
    """

    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_end_date: Optional[str] = None

    model_config = ConfigDict(coerce_numbers_to_str=True)

    def get_all_setted_fields(self):
        """
        Sadece degeri kesin olarak verilmis olan alanlari dondurur
        """
        fields = self.model_dump(
            exclude_unset=True,  # Atanmamislari disla
            exclude_defaults=True,  # Varsayilan degerine esit olanlari disla
            exclude_none=True,  # None olanlari disla
        )
        return fields

    def check_task_for_create(self):
        """
        Task olusturma isleminde tum alanlar sart
        Opsiyonel olmamali,
        Update islemlerinde parca parca update yapabilecegimiz icinde
        opsiyonel kalmalilar
        """
        setted_fields = self.get_all_setted_fields()
        setted_fields.pop("estimated_end_date", None)
        return len(setted_fields) == 4

    @field_validator("title", "content")
    @classmethod
    def validate_title_content(cls, value: str):
        if not isinstance(value, str) or len(value.strip()) < 3:
            raise ValueError("Title and Content length should be more than 2")
        return value

    @field_validator("status", "priority")
    @classmethod
    def validate_status_title(cls, value: str):
        if not isinstance(value, str) or not value.isnumeric():
            raise ValueError("Status and Priority must be numeric!")
        return value

    @field_validator("estimated_end_date")
    @classmethod
    def validate_date(cls, value: str):
        if isinstance(value, str):
            try:
                datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                raise ValueError("Estimated end date should be valid format!")
        return value
