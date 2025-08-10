from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import Base, engine

# грузим .env один раз на старте (чтобы SMTP/BASE_URL и т.д. были в окружении)
from dotenv import load_dotenv
load_dotenv(dotenv_path="/var/www/qomex/.env")


# --- ваши роутеры ---
from auth import router as auth_router
from postback import router as postback_router
from check import router as check_router
from deposit_check import router as deposit_check_router
from dashboard import router as dashboard_router
from home import router as home_router
from users import router as users_router
from profile import router as profile_router
from routes import router as routes_router

# ДОБАВИТЬ: роутер сброса пароля
from password_reset import router as password_reset_router

app = FastAPI()

# Подключение роутеров (порядок не критичен, главное — чтобы все были добавлены)
app.include_router(auth_router)
app.include_router(postback_router)
app.include_router(check_router)
app.include_router(deposit_check_router)
app.include_router(dashboard_router)
app.include_router(home_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(routes_router)

# ВАЖНО: подключаем роуты сброса пароля
app.include_router(password_reset_router)

# Статика/шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Таблицы БД
Base.metadata.create_all(bind=engine)
