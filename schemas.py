from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime


# Модель для создания оффера
class OfferCreate(BaseModel):
    offer: str
    geo: str
    price: float
    discount: int
    button_text: str = Field(..., alias="buttonText")
    description: str
    image: HttpUrl
    # Убираем поле link, так как оно не нужно
    link: Optional[HttpUrl] = None

    class Config:
        populate_by_name = True  # Заменяет allow_population_by_field_name


# Модель для чтения оффера (отправка в ответ API)
class OfferRead(BaseModel):
    id: int
    offer: str
    geo: str
    price: float
    discount: int
    button_text: str
    description: str
    image: HttpUrl
    # Убираем поле link из модели для чтения
    created_at: datetime
    updated_at: datetime
    url: HttpUrl  # Это будет URL для статической страницы оффера

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
        populate_by_name = True  # Заменяет allow_population_by_field_name


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
        populate_by_name = True  # Заменяет allow_population_by_field_name
        from_attributes = True  # Заменяет orm_mode
