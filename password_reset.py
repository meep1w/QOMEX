import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
from database import SessionLocal
from models import User

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
log = logging.getLogger("password_reset")

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
RESET_TOKEN_MAX_AGE = int(os.getenv("RESET_TOKEN_MAX_AGE", "3600"))  # 1 час по умолчанию
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
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
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

    # 1) логируем ссылку (удобно в dev)
    log.warning("Password reset link for %s: %s", email, reset_url)

    # 2) пытаемся отправить письмо
    try:
        _send_email_smtp(email, subject, body)
        log.info("Password reset email sent to %s", email)
    except Exception as e:
        log.exception("SMTP send failed: %s", e)
        # В ответ пользователю всё равно вернём success, чтобы не палить существование email.


@router.post("/password-reset-request")
async def password_reset_request(payload: dict, background: BackgroundTasks):
    """
    Принимает JSON: {"email": "..."}
    Если пользователь существует — генерирует токен, сохраняет в БД и отправляет письмо.
    В ответе всегда success=True (не палим существование email).
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return JSONResponse({"success": False, "message": "Укажите email."})

    db = SessionLocal()
    try:
        user: Optional[User] = db.query(User).filter(User.email == email).first()
        if user:
            if not SALT:
                log.error("SECURITY_PASSWORD_SALT not set")
                # Всё равно отвечаем success, но логируем проблему
            else:
                # генерим токен с TTL (проверим TTL при смене пароля, если решишь валидировать через serializer)
                s = get_serializer()
                token = s.dumps(email, salt=SALT)

                # сохраняем токен в БД (под твой /password-reset из auth.py)
                user.reset_token = token
                user.updated_at = datetime.utcnow()
                db.commit()

                # письмо отправим в фоне
                background.add_task(send_password_reset_email, email, token)

        # Всегда успешный ответ
        return JSONResponse({"success": True, "message": "Если email существует, ссылка отправлена."})
    finally:
        db.close()


@router.get("/auth/reset")
async def reset_password_page(request: Request, token: str):
    """
    Страница смены пароля (форма). Шаблон должен POST-ить на /password-reset
    с полями: token, new_password (FormData), что совпадает с твоим auth.py.
    """
    # Можно тут валидировать токен заранее (красиво показать "ссылка устарела")
    # Если не хочешь преждевременных ошибок — пропусти проверку на этом этапе.
    if SECRET_KEY and SALT and token:
        s = get_serializer()
        try:
            # Просто проверим подпись и срок (кроме того, /password-reset дальше сверит по БД)
            s.loads(token, salt=SALT, max_age=RESET_TOKEN_MAX_AGE)
        except SignatureExpired:
            # Можно отрисовать отдельный шаблон с сообщением "Ссылка устарела"
            return templates.TemplateResponse(
                "reset_password_expired.html",
                {"request": request}
            )
        except BadSignature:
            return templates.TemplateResponse(
                "reset_password_invalid.html",
                {"request": request}
            )

    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})
