# auth.py
from fastapi import APIRouter, Request, Form, Body
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from passlib.context import CryptContext
from typing import Optional
import secrets
import os

from sqlalchemy import exists

from database import SessionLocal
from models import User, PostbackLog  # PostbackLog нужен для attach_pending_postbacks ниже

router = APIRouter()
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"  # True в проде
SAMESITE_POLICY = "Lax"

def _ensure_click_id_in_cookie(request: Request) -> str:
    """Берём click_id из cookie, если нет — генерим новый"""
    cid = request.cookies.get("click_id")
    if not cid:
        cid = secrets.token_urlsafe(8)  # короткий безопасный id (URL-safe)
    return cid

def ensure_unique_click_id(db, cid: Optional[str]) -> str:
    """Возвращает свободный click_id (если занято — сгенерирует новый)."""
    if not cid:
        cid = secrets.token_urlsafe(8)
    while db.query(exists().where(User.click_id == cid)).scalar():
        cid = secrets.token_urlsafe(8)
    return cid

# --- подтягивание старых постбэков ---
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


@router.get("/auth")
async def auth_form(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


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
            if db.query(User).filter(User.login == login).first():
                return JSONResponse({"success": False, "message": "Этот логин уже занят."})
            if email and db.query(User).filter(User.email == email).first():
                return JSONResponse({"success": False, "message": "Этот email уже занят."})

            # берём СВОБОДНЫЙ click_id (чтобы не упасть по UNIQUE)
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

            # подтянем постбэки, если были
            attach_pending_postbacks(db, new_user)

            resp = JSONResponse({"success": True, "click_id": click_id_cookie})
            resp.set_cookie("user_id", str(new_user.id), httponly=True, max_age=max_age,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            if new_user.email:
                resp.set_cookie("user_email", new_user.email, max_age=max_age,
                                secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            # обновим куку на тот click_id, который точно свободен
            resp.set_cookie("click_id", click_id_cookie, max_age=60*60*24*30,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            return resp

        elif action == "login":
            user = db.query(User).filter(User.login == login).first()
            if not user or not verify_password(password, user.password):
                return JSONResponse({"success": False, "message": "Неверный логин или пароль."})

            click_id_cookie = raw_click_id

            # если у пользователя в БД пусто — выдадим ему свободный click_id
            if not user.click_id:
                safe_cid = ensure_unique_click_id(db, click_id_cookie)
                if safe_cid != click_id_cookie:
                    click_id_cookie = safe_cid  # заменим куку ниже
                user.click_id = safe_cid
                user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(user)

            # подтянем постбэки
            attach_pending_postbacks(db, user)

            resp = JSONResponse({"success": True, "click_id": user.click_id or click_id_cookie})
            resp.set_cookie("user_id", str(user.id), httponly=True, max_age=max_age,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            if user.email:
                resp.set_cookie("user_email", user.email, max_age=max_age,
                                secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            # поддержим корректный click_id в куке
            resp.set_cookie("click_id", user.click_id or click_id_cookie, max_age=60*60*24*30,
                            secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
            return resp

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
    token = token_form or (body or {}).get("token")
    new_password = new_password_form or (body or {}).get("new_password")

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
        user.reset_token = None
        user.updated_at = datetime.utcnow()
        db.commit()

        return JSONResponse({"success": True, "message": "Пароль успешно изменён."})
    finally:
        db.close()
