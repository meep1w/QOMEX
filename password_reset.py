import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
from database import SessionLocal
from models import User

# Загружаем .env (в main.py ты уже делаешь load_dotenv с явным путём — тут не мешает)
load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
log = logging.getLogger("password_reset")

# --- SMTP (оставлено на будущее, отправка ниже отключена) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

# --- Базовые настройки ---
BASE_URL = os.getenv("BASE_URL") or "https://qomex.top"  # НЕ localhost по умолчанию
RESET_TOKEN_MAX_AGE = int(os.getenv("RESET_TOKEN_MAX_AGE", "3600"))  # сек
SECRET_KEY = os.getenv("SECRET_KEY")
SALT = os.getenv("SECURITY_PASSWORD_SALT")

def get_serializer():
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY not set")
    return URLSafeTimedSerializer(SECRET_KEY)

def _send_email_smtp(to_email: str, subject: str, html_body: str):
    if not (SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD and SMTP_FROM):
        raise RuntimeError("SMTP env vars are not set (SERVER/USERNAME/PASSWORD/FROM)")

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    if SMTP_USE_SSL:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())

def send_password_reset_email(email: str, token: str):
    reset_url = f"{BASE_URL}/auth/reset?token={token}"
    subject = "Сброс пароля на QOMEX"
    body = f"""
        <p>Здравствуйте!</p>
        <p>Для сброса пароля перейдите по ссылке:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>Ссылка действительна {RESET_TOKEN_MAX_AGE // 60} минут(ы).</p>
    """
    # лог для отладки
    log.warning("Password reset link for %s: %s", email, reset_url)

    # ОТПРАВКА ВЫКЛЮЧЕНА (порты блокируются). Включишь позже — просто раскомментируй.
    try:
        # _send_email_smtp(email, subject, body)
        # log.info("Password reset email sent to %s", email)
        pass
    except Exception as e:
        log.exception("SMTP send failed: %s", e)
        # Ответ пользователю всё равно будет success.

@router.post("/password-reset-request")
async def password_reset_request(payload: dict, background: BackgroundTasks):
    """
    Принимает JSON: {"email": "..."}
    Если пользователь существует — генерирует токен, сохраняет в БД и (опционально) отправляет письмо.
    Сейчас возвращаем reset_url напрямую, чтобы обойтись без писем.
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return JSONResponse({"success": False, "message": "Укажите email."}, status_code=400)

    db = SessionLocal()
    try:
        reset_url_out = None

        user: Optional[User] = db.query(User).filter(User.email == email).first()
        if user and SALT:
            s = get_serializer()
            token = s.dumps(email, salt=SALT)

            user.reset_token = token
            user.updated_at = datetime.utcnow()
            db.commit()

            # Отправку письма можно включить позже:
            # background.add_task(send_password_reset_email, email, token)

            reset_url_out = f"{BASE_URL}/auth/reset?token={token}"
            log.warning("Password reset link for %s: %s", email, reset_url_out)

        # Всегда success (не палим наличие email), но если юзер найден — вернём reset_url
        resp = {"success": True, "message": "Если email существует, ссылка отправлена."}
        if reset_url_out:
            resp["reset_url"] = reset_url_out
        return JSONResponse(resp)
    finally:
        db.close()

@router.get("/auth/reset")
async def reset_password_page(request: Request, token: str):
    """
    Отрисовываем форму смены пароля. Если токен невалиден/просрочен — покажем предупреждение в этом же шаблоне.
    """
    invalid = False
    reason = None

    if SECRET_KEY and SALT and token:
        s = get_serializer()
        try:
            s.loads(token, salt=SALT, max_age=RESET_TOKEN_MAX_AGE)
        except SignatureExpired:
            invalid = True
            reason = "expired"
        except BadSignature:
            invalid = True
            reason = "invalid"

    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "token": token, "invalid": invalid, "reason": reason}
    )
