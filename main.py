import os
import asyncpg
from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from typing import List
from models import Offer, Country
from schemas import OfferCreate, OfferRead, CountryCreate, CountryRead
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from fastapi.staticfiles import StaticFiles

# Инициализация приложения
app = FastAPI(
    title="Offers Generator API",
    description="API для генерации HTML-страниц офферов и получения ссылок на них",
    version="1.0.0"
)

# Настройка CORS
origins = [
    "http://localhost",
    "http://localhost:5173",
    # Добавьте другие разрешённые источники
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешённые источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получение абсолютного пути к папке templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")

# Настройка Jinja2 Environment для генерации HTML
env = Environment(loader=FileSystemLoader(templates_dir))

# Убедитесь, что директория для сохранения офферов существует
static_offers_dir = os.path.abspath(os.path.join(current_dir, "static", "offers"))
os.makedirs(static_offers_dir, exist_ok=True)

# Смонтировать директорию static для обслуживания статических файлов
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")


# Функция для создания базы данных, если она не существует
async def create_database():
    db_url = os.getenv("DATABASE_URL", "postgres://postgres@localhost:5432")
    conn = await asyncpg.connect(dsn=db_url)
    try:
        # Проверка существования базы данных
        result = await conn.fetch('SELECT 1 FROM pg_database WHERE datname = $1', 'offers_db')
        if not result:
            await conn.execute('CREATE DATABASE offers_db')
            print("База данных 'offers_db' была создана.")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        await conn.close()


# Асинхронная инициализация Tortoise ORM
async def init_tortoise():
    # Убедитесь, что база данных создана перед запуском Tortoise ORM
    await create_database()

    # Строка подключения для PostgreSQL
    db_url = os.getenv("DATABASE_URL", "postgres://postgres@localhost:5432/offers_db")

    # Регистрация Tortoise ORM
    register_tortoise(
        app,
        db_url=db_url,  # Строка подключения к PostgreSQL
        modules={'models': ['models']},  # Модели из файла models.py
        generate_schemas=True,  # Автоматическая генерация схем
        add_exception_handlers=True,
    )


# Запуск инициализации базы данных и Tortoise ORM в стартапе приложения FastAPI
@app.on_event("startup")
async def startup():
    # Инициализация базы данных и подключения Tortoise ORM
    await init_tortoise()


# Эндпоинт для генерации оффера
@app.post("/generate_offer/", response_model=dict)
async def generate_offer(offer: OfferCreate):
    # Получаем страну по коду
    country = await Country.get_or_none(code=offer.country_code)
    if not country:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    # Создание записи оффера в базе данных
    offer_obj = await Offer.create(
        offer=offer.offer,
        geo=offer.geo,
        price=offer.price,
        discount=offer.discount,
        button_text=offer.button_text,
        description=offer.description,
        image=str(offer.image),
        link=str(offer.link) if offer.link else None,
        country=country
    )

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

    # Получаем перевод для нужного языка
    lang = translations.get(country.language, translations['en'])

    # Генерация HTML-контента с использованием шаблона
    try:
        template = env.get_template("offer_template.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки шаблона: {str(e)}")

    # Передаем нужные данные в шаблон, включая переводы
    html_content = template.render(offer=offer_obj, translations=lang)

    # Определение пути для сохранения HTML-файла
    html_filename = f"offer_{offer_obj.id}.html"
    html_path = os.path.join(static_offers_dir, html_filename)

    # Сохранение HTML-файла
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения HTML файла: {str(e)}")

    # Генерация полной ссылки на HTML-страницу
    offer_url = f"http://localhost:8000/static/offers/{html_filename}"

    return {"url": offer_url}

# Эндпоинт для получения всех офферов
@app.get("/api/offers/", response_model=List[OfferRead])
async def api_get_offers():
    # Используем prefetch_related для оптимизации запросов, если есть связанные данные
    offers = await Offer.all().prefetch_related('country')
    return [offer.to_read_model() for offer in offers]

# Эндпоинт для удаления оффера
@app.delete("/api/offers/{offer_id}", response_model=dict)
async def api_delete_offer(offer_id: int):
    offer = await Offer.get_or_none(id=offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Оффер не найден")
    await offer.delete()
    return {"message": "Оффер удален успешно"}


# Эндпоинт для добавления новой страны
@app.post("/api/countries/", response_model=CountryRead)
async def api_create_country(country: CountryCreate):
    # Проверка на уникальность кода страны
    existing_country = await Country.get_or_none(code=country.code)
    if existing_country:
        raise HTTPException(status_code=400, detail="Страна с таким кодом уже существует.")

    country_obj = await Country.create(
        code=country.code,
        name=country.name,
        currency=country.currency,
        language=country.language,
        actions=country.actions
    )
    return country_obj.to_read_model()


# Эндпоинт для получения всех стран
@app.get("/api/countries/", response_model=List[CountryRead])
async def api_get_countries():
    countries = await Country.all()
    return [country.to_read_model() for country in countries]


# Запуск приложения
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
