from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from typing import List
from models import Offer, Country
from schemas import OfferCreate, OfferRead, CountryRead, CountryCreate
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
import os
from fastapi.staticfiles import StaticFiles  # Для обслуживания статических файлов

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

# Регистрация Tortoise ORM
register_tortoise(
    app,
    db_url='sqlite://offers.db',  # Используется SQLite
    modules={'models': ['models']},  # Модели из файла models.py
    generate_schemas=True,  # Автоматическая генерация схем
    add_exception_handlers=True,
)

# Эндпоинт для генерации оффера
@app.post("/generate_offer/", response_model=dict)
async def generate_offer(offer: OfferCreate):
    # Создание записи в базе данных
    offer_obj = await Offer.create(
        offer=offer.offer,
        geo=offer.geo,
        price=offer.price,
        discount=offer.discount,
        button_text=offer.button_text,
        description=offer.description,
        image=str(offer.image),
        link=str(offer.link) if offer.link else None  # Если link None, передаем None
    )

    # Генерация HTML-контента с использованием шаблона
    try:
        template = env.get_template("offer_template.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки шаблона: {str(e)}")

    html_content = template.render(offer=offer_obj)

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
    offers = await Offer.all()
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

# Эндпоинт для удаления страны
@app.delete("/api/countries/{country_code}", response_model=dict)
async def api_delete_country(country_code: int):
    country = await Country.get_or_none(code=country_code)
    if not country:
        raise HTTPException(status_code=404, detail="Страна не найдена")
    await country.delete()
    return {"message": "Страна удалена успешно"}

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
