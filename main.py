import os
from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from models import Offer, Country
from schemas import OfferCreate, OfferRead, CountryCreate, CountryRead
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from translations import translations
from country import countries_info
from tortoise.contrib.fastapi import register_tortoise
from datetime import datetime
from pathlib import Path

# Загружаем переменные из .env
load_dotenv()

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к папке с шаблонами
current_dir = Path(__file__).resolve().parent
templates_dir = Path(os.getenv("TEMPLATES_DIR", "templates")).resolve()
if not templates_dir.exists():
    raise ValueError(f"Директория шаблонов не найдена: {templates_dir}")

env = Environment(loader=FileSystemLoader(str(templates_dir)))

# Путь к папке static/offers
static_offers_dir = Path(os.getenv("STATIC_OFFERS_DIR", "static/offers")).resolve()
static_offers_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")


async def init_tortoise():
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        raise ValueError("Переменная окружения 'DATABASE_URL' не установлена!")

    register_tortoise(
        app,
        db_url=db_url,
        modules={'models': ['models']},
        generate_schemas=True,
        add_exception_handlers=True,
    )

@app.on_event("startup")
async def startup():
    await init_tortoise()


@app.post("/generate_offer/", response_model=dict)
async def generate_offer(offer: OfferCreate):
    # Проверяем, есть ли такая страна
    country = await Country.filter(code=offer.country_code).first()
    if not country:
        raise HTTPException(status_code=404, detail="Страна не найдена")

    # Создаём оффер (без button_text и description)
    offer_obj = Offer(
        offer=offer.offer,
        geo=offer.geo,
        price=offer.price,
        discount=offer.discount,
        image=str(offer.image),
        link=str(offer.link) if offer.link else None,
        country=country
    )
    await offer_obj.save()

    # Получаем перевод для нужного языка
    lang = translations.get(country.language, translations['English'])

    # Генерация HTML-контента через Jinja2
    try:
        template = env.get_template("offer_template.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки шаблона: {str(e)}")

    html_content = template.render(
        offer=offer_obj,
        translations=lang,
        currency=country.currency
    )

    html_filename = f"offer_{offer_obj.id}.html"
    html_path = static_offers_dir / html_filename

    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения HTML файла: {str(e)}")

    base_url = os.getenv('BASE_URL')
    if base_url is None:
        raise ValueError("Переменная окружения 'BASE_URL' не установлена!")

    offer_url = f"{base_url}/static/offers/{html_filename}"
    return {"url": offer_url}


@app.get("/api/countries/", response_model=List[CountryRead])
async def api_get_countries():
    # Сначала загружаем базовый список из country.py, затем сохраняем в БД, если нет
    countries = []
    for country_info in countries_info:
        country = Country(
            code=country_info['code'],
            name=country_info['name'],
            currency=country_info['currency'],
            language=country_info['language'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        countries.append(country)

    for country in countries:
        if not await Country.filter(code=country.code).exists():
            await country.save()

    return [country.to_read_model() for country in await Country.all()]


@app.get("/api/offers/", response_model=List[OfferRead])
async def api_get_offers(country: Optional[str] = Query(None)):
    if country:
        offers = await Offer.filter(country__code=country).prefetch_related('country')
    else:
        offers = await Offer.all().prefetch_related('country')

    return [offer.to_read_model() for offer in offers]


@app.delete("/api/offers/{offer_id}", response_model=dict)
async def delete_offer(offer_id: int):
    offer = await Offer.filter(id=offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    await offer.delete()
    return {"message": f"Offer with ID {offer_id} has been deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
