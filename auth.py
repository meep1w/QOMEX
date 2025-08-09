from fastapi import APIRouter, Request, Form, Body
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from passlib.context import CryptContext
from typing import Optional
import secrets
import os

from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# В проде задай BASE_URL и используй HTTPS
IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"  # True в проде
SAMESITE_POLICY = "Lax"  # можно "Strict", если не планируется кросс-сайт


@router.get("/auth")
async def auth_form(request: Request):
    """Страница регистрации/входа"""
    return templates.TemplateResponse("auth.html", {"request": request})


@router.post("/auth")
async def handle_auth(
    request: Request,
    login: str = Form(...),
    email: Optional[str] = Form(None),     # при login не требуем email
    password: str = Form(...),
    action: str = Form(...),               # "register" | "login"
    remember: Optional[str] = Form(None),  # "true" | None
):
    """Обработчик регистрации и входа"""
    db = SessionLocal()
    try:
        remember_bool = (remember == "true")
        max_age = 60 * 60 * 24 * 30 if remember_bool else None  # 30 дней

        if action == "register":
            # проверки уникальности
            if db.query(User).filter(User.login == login).first():
                return JSONResponse({"success": False, "message": "Этот логин уже занят."})
            if email and db.query(User).filter(User.email == email).first():
                return JSONResponse({"success": False, "message": "Этот email уже занят."})

            # создаём пользователя
            hashed_pw = hash_password(password)
            unique_click_id = secrets.token_urlsafe(8)

            new_user = User(
                login=login,
                email=email,
                password=hashed_pw,
                click_id=unique_click_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # куки
            response = JSONResponse({"success": True, "click_id": unique_click_id})
            response.set_cookie(
                key="user_id",
                value=str(new_user.id),
                httponly=True,
                max_age=max_age,
                secure=IS_SECURE_COOKIES,
                samesite=SAMESITE_POLICY,
            )
            if new_user.email:
                response.set_cookie(
                    key="user_email",
                    value=new_user.email,
                    max_age=max_age,
                    secure=IS_SECURE_COOKIES,
                    samesite=SAMESITE_POLICY,
                )
            return response

        elif action == "login":
            user = db.query(User).filter(User.login == login).first()
            if user and verify_password(password, user.password):
                response = JSONResponse({"success": True, "click_id": user.click_id})
                response.set_cookie(
                    key="user_id",
                    value=str(user.id),
                    httponly=True,
                    max_age=max_age,
                    secure=IS_SECURE_COOKIES,
                    samesite=SAMESITE_POLICY,
                )
                if user.email:
                    response.set_cookie(
                        key="user_email",
                        value=user.email,
                        max_age=max_age,
                        secure=IS_SECURE_COOKIES,
                        samesite=SAMESITE_POLICY,
                    )
                return response

            return JSONResponse({"success": False, "message": "Неверный логин или пароль."})

        else:
            return JSONResponse({"success": False, "message": "Неверное действие."})

    finally:
        db.close()


@router.post("/password-reset")
async def password_reset(
    token_form: Optional[str] = Form(None),
    new_password_form: Optional[str] = Form(None),
    body: Optional[dict] = Body(None),
):
    """
    Принимает либо FormData (token, new_password), либо JSON {"token": ..., "new_password": ...}
    """
    # Достаём данные из формы или JSON
    token = token_form
    new_password = new_password_form
    if body:
        token = token or body.get("token")
        new_password = new_password or body.get("new_password")

    if not token or not new_password:
        return JSONResponse({"success": False, "message": "Некорректные данные."})

    if len(new_password) < 6:
        return JSONResponse({"success": False, "message": "Пароль слишком короткий (мин. 6 символов)."})

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            return JSONResponse({"success": False, "message": "Неверный или устаревший токен."})

        user.password = hash_password(new_password)
        user.reset_token = None  # сброс токена
        user.updated_at = datetime.utcnow()
        db.commit()

        return JSONResponse({"success": True, "message": "Пароль успешно изменён."})
    finally:
        db.close()
