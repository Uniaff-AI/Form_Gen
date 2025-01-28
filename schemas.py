from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

# Модель для создания оффера
class OfferCreate(BaseModel):
    offer: str
    geo: str
    price: int
    discount: int
    # Удалили button_text и description
    image: HttpUrl
    link: Optional[HttpUrl] = None
    country_code: str = Field(..., alias="countryCode")

    class Config:
        populate_by_name = True


# Модель для чтения оффера (отправка в ответ API)
class OfferRead(BaseModel):
    id: int
    offer: str
    geo: str
    price: int
    discount: int
    # Удалили button_text и description
    image: HttpUrl
    created_at: datetime
    updated_at: datetime
    url: HttpUrl
    country_code: str
    language: str
    remaining_text: str
    discount_text: str
    name_text: str
    phone_text: str

    class Config:
        from_attributes = True  # Заменяет orm_mode


# Модель для создания страны
class CountryCreate(BaseModel):
    code: str
    name: str
    currency: str
    language: str

    class Config:
        populate_by_name = True


# Модель для чтения страны (отправка в ответ API)
class CountryRead(BaseModel):
    code: str
    name: str
    currency: str
    language: str
    created_at: datetime
    updated_at: datetime
    url: HttpUrl

    class Config:
        populate_by_name = True
        from_attributes = True


# Модель для создания перевода оффера
class OfferTranslationCreate(BaseModel):
    language: str
    offer_text: str
    # Удалили description и button_text
    remaining_text: str = "Осталось"
    discount_text: str = "Скидка"
    name_text: str = "Имя"
    phone_text: str = "Номер Телефона"

    class Config:
        populate_by_name = True
