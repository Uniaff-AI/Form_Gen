from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

# Модель для создания оффера
class OfferCreate(BaseModel):
    offer: str
    geo: str
    price: float
    discount: float  # Изменено с int на float для поддержки дробных значений
    button_text: str = Field(..., alias="buttonText")
    description: Optional[str] = None  # Сделано необязательным
    image: HttpUrl
    link: Optional[HttpUrl] = None
    country_code: int = Field(..., alias="countryCode")  # Используем alias для поддержки camelCase

    class Config:
        populate_by_name = True  # Заменяет allow_population_by_field_name


# Модель для чтения оффера (отправка в ответ API)
class OfferRead(BaseModel):
    id: int
    offer: str
    geo: str
    price: float
    discount: float  # Изменено с int на float
    button_text: str
    description: str
    image: HttpUrl
    created_at: datetime
    updated_at: datetime
    url: HttpUrl
    country_code: int  # Код страны

    class Config:
        from_attributes = True  # Заменяет orm_mode


# Модель для создания страны
class CountryCreate(BaseModel):
    code: int
    name: str
    currency: str
    language: str
    actions: str

    class Config:
        populate_by_name = True


# Модель для чтения страны (отправка в ответ API)
class CountryRead(BaseModel):
    code: int
    name: str
    currency: str
    language: str
    actions: str
    created_at: datetime
    updated_at: datetime
    url: HttpUrl  # URL для статической страницы страны

    class Config:
        populate_by_name = True
        from_attributes = True


# Модель для создания перевода оффера
class OfferTranslationCreate(BaseModel):
    offer_id: int
    language: str
    offer_text: str
    description: str
    button_text: str

    class Config:
        populate_by_name = True
