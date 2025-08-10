# auth.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from passlib.context import CryptContext
from typing import Optional
import secrets
import os

from sqlalchemy import exists
from database import SessionLocal
from models import User, PostbackLog  # для attach_pending_postbacks

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# === Пароли ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# === Куки ===
IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"  # True в проде
SAMESITE_POLICY = "Lax"

# === Вспомогательные ===
def _ensure_click_id_in_cookie(request: Request) -> str:
    """Берём click_id из cookie, если нет — генерим новый"""
    cid = request.cookies.get("click_id")
    if not cid:
        cid = secrets.token_urlsafe(8)
    return cid

def ensure_unique_click_id(db, cid: Optional[str]) -> str:
    """Возвращает свободный click_id (если занято — сгенерирует новый)."""
    if not cid:
        cid = secrets.token_urlsafe(8)
    while db.query(exists().where(User.click_id == cid)).scalar():
        cid = secrets.token_urlsafe(8)
    return cid

def attach_pending_postbacks(db, user: User):
    q = db.query(PostbackLog).filter(PostbackLog.processed == False)
    if user.click_id:
        q = q.filter(PostbackLog.click_id == user.click_id)
    elif user.trader_id:
        q = q.filter(PostbackLog.trader_id == user.trader_id)
    else:
        return

    logs = q.all()
    if not logs:
        return

    for pb in logs:
        if pb.event == "deposit" and (pb.amount or 0) > 0:
            if user.first_deposit is None:
                user.first_deposit = pb.amount
            user.total_deposit = (user.total_deposit or 0.0) + (pb.amount or 0.0)

        if pb.trader_id and not user.trader_id:
            user.trader_id = pb.trader_id

        pb.user_id = user.id
        pb.processed = True
        pb.processed_at = datetime.utcnow()

    user.updated_at = datetime.utcnow()
    db.commit()

# === Рендер формы ===
@router.get("/auth")
async def auth_form(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

# === Регистрация/логин ===
@router.post("/auth")
async def handle_auth(
    request: Request,
    login: str = Form(...),
    email: Optional[str] = Form(None),
    password: str = Form(...),
    action: str = Form(...),               # "register" | "login"
    remember: Optional[str] = Form(None),  # "true" | None
):
    db = SessionLocal()
    try:
        remember_bool = (remember == "true")
        max_age = 60 * 60 * 24 * 30 if remember_bool else None

        raw_click_id = _ensure_click_id_in_cookie(request)

        if action == "register":
            # базовая валидация
            if not email:
                return JSONResponse({"success": False, "message": "Укажите email."}, status_code=400)

            if db.query(User).filter(User.login == login).first():
                return JSONResponse({"success": False, "message": "Этот логин уже занят."}, status_code=409)
            if db.query(User).filter(User.email == email).first():
                return JSONResponse({"success": False, "message": "Этот email уже занят."}, status_code=409)

            click_id_cookie = ensure_unique_click_id(db, raw_click_id)
            hashed_pw = hash_password(password)

            new_user = User(
                login=login,
                email=email,
                password=hashed_pw,
                click_id=click_id_cookie,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            attach_pending_postbacks(db, new_user)

            resp = JSONResponse({"success": True, "click_id": click_id_cookie})
            resp.set_cookie("user_id", str(new_user.id), httponly=True, max_age=max_age,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            if new_user.email:
                resp.set_cookie("user_email", new_user.email, max_age=max_age,
                                secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            resp.set_cookie("click_id", click_id_cookie, max_age=60*60*24*30,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            return resp

        elif action == "login":
            user = db.query(User).filter(User.login == login).first()
            if not user or not verify_password(password, user.password):
                return JSONResponse({"success": False, "message": "Неверный логин или пароль."}, status_code=401)

            click_id_cookie = raw_click_id

            if not user.click_id:
                safe_cid = ensure_unique_click_id(db, click_id_cookie)
                if safe_cid != click_id_cookie:
                    click_id_cookie = safe_cid
                user.click_id = safe_cid
                user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(user)

            attach_pending_postbacks(db, user)

            resp = JSONResponse({"success": True, "click_id": user.click_id or click_id_cookie})
            resp.set_cookie("user_id", str(user.id), httponly=True, max_age=max_age,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            if user.email:
                resp.set_cookie("user_email", user.email, max_age=max_age,
                                secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            resp.set_cookie("click_id", user.click_id or click_id_cookie, max_age=60*60*24*30,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")
            return resp

        else:
            return JSONResponse({"success": False, "message": "Неверное действие."}, status_code=400)

    finally:
        db.close()

# === Сброс пароля (применение нового) ===
@router.post("/password-reset")
async def password_reset(
    request: Request,
    token_form: Optional[str] = Form(None),
    new_password_form: Optional[str] = Form(None),
):
    # 1) сначала пробуем form
    token = token_form
    new_password = new_password_form

    # 2) если form пуст — читаем JSON вручную
    if not token or not new_password:
        try:
            data = await request.json()
        except Exception:
            data = {}
        token = token or data.get("token")
        new_password = new_password or data.get("new_password")

    # 3) валидация
    if not token or not new_password:
        return JSONResponse({"success": False, "message": "Некорректные данные."}, status_code=400)
    if len(new_password) < 6:
        return JSONResponse({"success": False, "message": "Пароль слишком короткий (мин. 6 символов)."}, status_code=400)

    # 4) ищем по токену и обновляем пароль
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            return JSONResponse({"success": False, "message": "Неверный или устаревший токен."}, status_code=400)

        user.password = hash_password(new_password)
        user.reset_token = None
        user.updated_at = datetime.utcnow()
        db.commit()

        return JSONResponse({"success": True, "message": "Пароль успешно изменён."})
    finally:
        db.close()
