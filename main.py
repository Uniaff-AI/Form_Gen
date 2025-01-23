import os
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from models import Offer, Country  # Импортируем модели
from schemas import OfferCreate, OfferRead, CountryCreate, CountryRead
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv  # Импортируем для работы с .env файлом
from translations import translations  # Импортируем переводы
from country import countries_info  # Импортируем данные о странах из country.py
from tortoise.contrib.fastapi import register_tortoise  # Импортируем register_tortoise
from datetime import datetime
from pathlib import Path  # Для более надежной работы с путями

# Загружаем переменные из .env
load_dotenv()

# Инициализация приложения
app = FastAPI(
    title="Offers Generator API",
    description="API для генерации HTML-страниц офферов и получения ссылок на них",
    version="1.0.0"
)

# Настройка CORS
origins = os.getenv("ALLOWED_ORIGINS")
if origins is None:
    raise ValueError("Переменная окружения 'ALLOWED_ORIGINS' не установлена!")

origins = origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешённые источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Получение абсолютного пути к папке templates
current_dir = Path(__file__).resolve().parent
templates_dir = Path(os.getenv("TEMPLATES_DIR", "templates")).resolve()  # Default to 'templates'
if not templates_dir.exists():
    raise ValueError(f"Директория шаблонов не найдена: {templates_dir}")

# Настройка Jinja2 Environment для генерации HTML
env = Environment(loader=FileSystemLoader(str(templates_dir)))

# Получаем путь для сохранения офферов
static_offers_dir = Path(os.getenv("STATIC_OFFERS_DIR", "static/offers")).resolve()  # Default to 'static/offers'
static_offers_dir.mkdir(parents=True, exist_ok=True)

# Смонтировать директорию static для обслуживания статических файлов
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


# Асинхронная инициализация Tortoise ORM
async def init_tortoise():
    # Строка подключения для PostgreSQL
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        raise ValueError("Переменная окружения 'DATABASE_URL' не установлена!")

    # Регистрация Tortoise ORM
    register_tortoise(
        app,
        db_url=db_url,  # Строка подключения к PostgreSQL
        modules={'models': ['models']},  # Модели из файла models.py
        generate_schemas=True,  # Автоматическая генерация схем
        add_exception_handlers=True,
    )


# Запуск инициализации Tortoise ORM в стартапе приложения FastAPI
@app.on_event("startup")
async def startup():
    # Инициализация подключения Tortoise ORM
    await init_tortoise()


# Эндпоинт для генерации оффера
@app.post("/generate_offer/", response_model=dict)
async def generate_offer(offer: OfferCreate):
    # Получаем страну по коду из списка с использованием get_or_none
    country = await Country.filter(code=offer.country_code).first()
    if not country:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    # Создание оффера
    offer_obj = Offer(
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

    # Сохранение оффера в БД
    await offer_obj.save()

    # Получаем перевод для нужного языка из файла translations
    lang = translations.get(country.language, translations['English'])

    # Генерация HTML-контента с использованием шаблона
    try:
        template = env.get_template("offer_template.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки шаблона: {str(e)}")

    # Передаем нужные данные в шаблон, включая переводы и валюту
    html_content = template.render(
        offer=offer_obj,
        translations=lang,
        currency=country.currency  # Добавляем валюту
    )

    # Определение пути для сохранения HTML-файла
    html_filename = f"offer_{offer_obj.id}.html"
    html_path = static_offers_dir / html_filename

    # Сохранение HTML-файла
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения HTML файла: {str(e)}")

    # Генерация полной ссылки на HTML-страницу
    base_url = os.getenv('BASE_URL')
    if base_url is None:
        raise ValueError("Переменная окружения 'BASE_URL' не установлена!")

    offer_url = f"{base_url}/static/offers/{html_filename}"

    return {"url": offer_url}


# Эндпоинт для получения всех стран
@app.get("/api/countries/", response_model=List[CountryRead])
async def api_get_countries():
    countries = []
    for country_info in countries_info:
        country = Country(code=country_info['code'], name=country_info['name'],
                         currency=country_info['currency'], language=country_info['language'],
                         actions="Some actions",  # Установите значение по умолчанию для actions
                         created_at=datetime.now(),  # Установите значение по умолчанию для created_at
                         updated_at=datetime.now())  # Установите значение по умолчанию для updated_at
        countries.append(country)
    # Сохраняем все страны если их нет
    for country in countries:
        if not await Country.filter(code=country.code).exists():
            await country.save()

    return [country.to_read_model() for country in await Country.all()]


# Эндпоинт для получения всех офферов с возможностью фильтрации по стране
@app.get("/api/offers/", response_model=List[OfferRead])
async def api_get_offers(country: Optional[str] = Query(None)):
    if country:
        # Фильтруем офферы по стране, если параметр передан
        offers = await Offer.filter(country__code=country).prefetch_related('country')
    else:
        # Возвращаем все офферы, если параметр не передан
        offers = await Offer.all().prefetch_related('country')

    return [offer.to_read_model() for offer in offers]


# Эндпоинт для удаления оффера по ID
@app.delete("/api/offers/{offer_id}", response_model=dict)
async def delete_offer(offer_id: int):
    # Попытка получить оффер по ID
    offer = await Offer.filter(id=offer_id).first()

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Удаление оффера из базы данных
    await offer.delete()

    return {"message": f"Offer with ID {offer_id} has been deleted successfully"}


# Запуск приложения
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
