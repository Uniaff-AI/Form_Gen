from tortoise import fields, models
from datetime import datetime
from schemas import OfferRead, CountryRead  # Импортируем необходимые схемы

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

    # Метод для преобразования в Pydantic-модель
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

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "offers"

    # Метод для преобразования в Pydantic-модель
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
            link=self.link if self.link else "",  # Если link None, отдаем пустую строку
            created_at=self.created_at,
            updated_at=self.updated_at,
            url=f"http://localhost:8000/static/offers/offer_{self.id}.html"
        )
