# models.py

from tortoise import fields, models
from schemas import OfferRead, CountryRead
from datetime import datetime
import os
from translations import translations

# Модель для страны (Country)
class Country(models.Model):
    code = fields.CharField(max_length=3, pk=True)  # Изменено на max_length=3
    name = fields.CharField(max_length=255)  # Имя страны
    currency = fields.CharField(max_length=50)  # Валюта
    language = fields.CharField(max_length=50)  # Язык
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "countries"

    def to_read_model(self) -> CountryRead:
        return CountryRead(
            code=self.code,
            name=self.name,
            currency=self.currency,
            language=self.language,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=f"{os.getenv('BASE_URL')}/static/countries/country_{self.code}.html"  # Используем BASE_URL из .env
        )

# Модель для оффера (Offer)
class Offer(models.Model):
    id = fields.IntField(pk=True)
    offer = fields.CharField(max_length=255)
    geo = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    discount = fields.DecimalField(max_digits=10, decimal_places=2) # Изменил тип на decimal
    button_text = fields.CharField(max_length=100)
    description = fields.TextField()
    image = fields.CharField(max_length=255)
    link = fields.CharField(max_length=255, null=True)
    country = fields.ForeignKeyField("models.Country", related_name="offers")  # Привязка к стране

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "offers"

    def to_read_model(self) -> OfferRead:
         country_language = self.country.language
         lang = translations.get(country_language, translations['English'])

         return OfferRead(
            id=self.id,
            offer=self.offer,
            geo=self.geo,
            price=float(self.price),
            discount=float(self.discount), # Изменил тип на float
            button_text=self.button_text,
            description=self.description,
            image=self.image,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=f"{os.getenv('BASE_URL')}/static/offers/offer_{self.id}.html",
            country_code=self.country.code,
            language=country_language,
            remaining_text=lang['remaining'],
            discount_text=lang['discount'],
            name_text=lang['name'],
            phone_text=lang['phone']
        )