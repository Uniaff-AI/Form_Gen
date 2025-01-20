from tortoise import fields, models
from schemas import OfferRead, CountryRead
from datetime import datetime

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
    country = fields.ForeignKeyField("models.Country", related_name="offers")  # Привязка к стране

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "offers"

    def to_read_model(self) -> OfferRead:
        # Получаем язык страны, к которой привязан оффер
        country_language = self.country.language

        # Переводы для разных языков
        translations = {
            'ru': {
                "remaining": "Осталось",
                "discount": "Скидка",
                "name": "Имя",
                "phone": "Номер Телефона"
            },
            'es': {
                "remaining": "Quedan",
                "discount": "Descuento",
                "name": "Nombre",
                "phone": "Número de Teléfono"
            },
            'en': {
                "remaining": "Remaining",
                "discount": "Discount",
                "name": "Name",
                "phone": "Phone Number"
            }
        }

        # Используем перевод в зависимости от языка страны
        lang = translations.get(country_language, translations['en'])

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
            country_code=self.country.code if self.country else None,
            language=country_language,
            remaining_text=lang['remaining'],
            discount_text=lang['discount'],
            name_text=lang['name'],
            phone_text=lang['phone']
        )
