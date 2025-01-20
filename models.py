from tortoise import fields, models
from datetime import datetime
from schemas import OfferRead, CountryRead

# Модель для страны (Country)
class Country(models.Model):
    code = fields.IntField(pk=True)  # Код страны (номер)
    name = fields.CharField(max_length=255)  # Имя страны
    currency = fields.CharField(max_length=50)  # Валюта
    language = fields.CharField(max_length=50)  # Язык
    actions = fields.CharField(max_length=255)  # Действия (например, описание операций)

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
            actions=self.actions,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=f"http://localhost:8000/static/countries/country_{self.code}.html"
        )


# Модель для перевода (Translation)
class OfferTranslation(models.Model):
    offer = fields.ForeignKeyField("models.Offer", related_name="translations")
    language = fields.CharField(max_length=50)  # Язык перевода
    offer_text = fields.CharField(max_length=255)
    description = fields.TextField()
    button_text = fields.CharField(max_length=100)

    class Meta:
        table = "offer_translations"


# Модель для оффера (Offer)
class Offer(models.Model):
    id = fields.IntField(pk=True)
    offer = fields.CharField(max_length=255)
    geo = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    discount = fields.IntField()
    button_text = fields.CharField(max_length=100)
    description = fields.TextField()
    image = fields.CharField(max_length=255)
    link = fields.CharField(max_length=255, null=True)
    country = fields.ForeignKeyField("models.Country", related_name="offers")  # Добавляем страну

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "offers"

    def to_read_model(self) -> OfferRead:
        return OfferRead(
            id=self.id,
            offer=self.offer,
            geo=self.geo,
            price=float(self.price),
            discount=self.discount,
            button_text=self.button_text,
            description=self.description,
            image=self.image,
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=f"http://localhost:8000/static/offers/offer_{self.id}.html",
            country_code=self.country.code if self.country else None  # Код страны
        )
