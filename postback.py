# postback.py
from fastapi import APIRouter, Request, HTTPException
from database import SessionLocal
from models import User
from datetime import datetime
import os, json, logging, re

router = APIRouter()
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET", "YOUR_SECRET")  # можно поменять/удалить проверку

# Лог в файл (если нет прав на /var/log — смените путь на /tmp/postback.log)
logging.basicConfig(
    filename="/tmp/postback.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)

DIGITS_RE = re.compile(r"^\d+$")

def normalize_event(raw: str) -> str:
    v = (raw or "").strip().lower()
    if v in ("registration", "register", "signup", "trader_has_registered"):
        return "registration"
    if v in ("deposit", "ftd", "first_deposit", "payment", "trader_has_made_a_deposit"):
        return "deposit"
    return v

def parse_amount(v: str) -> float:
    if not v:
        return 0.0
    try:
        return float(v.replace(",", "."))
    except:
        return 0.0

async def _collect_params(request: Request) -> dict:
    params = dict(request.query_params)
    # Дополнительно соберём тело POST (form/json)
    if request.method.upper() == "POST":
        ct = (request.headers.get("content-type") or "").lower()
        try:
            if "application/json" in ct:
                body = await request.json()
                if isinstance(body, dict):
                    params.update(body)
            else:
                form = await request.form()
                params.update(dict(form))
        except Exception:
            pass
    return params

async def _handle(params: dict):
    # Лог входящих сырых параметров
    logging.info("RAW_POSTBACK %s", json.dumps(params, ensure_ascii=False))

    # Проверка секрета (если секрет не используете — уберите этот блок)
    token = params.get("token")
    if token != POSTBACK_SECRET:
        logging.info("FORBIDDEN token=%s", token)
        raise HTTPException(status_code=403, detail="forbidden")

    # Нормализация
    event = normalize_event(params.get("event"))
    click_id = (params.get("click_id") or "").strip()
    trader_id = (params.get("trader_id") or "").strip()
    amount = parse_amount((params.get("amount") or "").strip())
    currency = (params.get("currency") or "").strip().upper()

    db = SessionLocal()
    try:
        user = None
        if click_id:
            user = db.query(User).filter(User.click_id == click_id).first()
        if user is None and trader_id and DIGITS_RE.match(trader_id):
            user = db.query(User).filter(User.trader_id == trader_id).first()

        if user is None:
            logging.info("NO_USER_MATCH click_id=%s trader_id=%s event=%s amount=%.2f %s",
                         click_id, trader_id, event, amount, currency)
            return {"status": "ok", "note": "user_not_found"}

        # ТОЛЬКО если trader_id пуст у нас — заполняем
        if (not getattr(user, "trader_id", None)) and trader_id and DIGITS_RE.match(trader_id):
            user.trader_id = trader_id

        # Сохраняем последнее событие и сумму (подгоните под свою модель)
        user.event = event
        if event == "deposit" and amount > 0:
            # последний депозит
            user.amount = amount
            # аккумулируем общую сумму депозитов, если поле есть
            if hasattr(user, "deposits_sum"):
                user.deposits_sum = (user.deposits_sum or 0) + amount

        if hasattr(user, "updated_at"):
            user.updated_at = datetime.utcnow()

        db.commit()
        logging.info("OK user_id=%s click_id=%s trader_id=%s event=%s amount=%.2f %s",
                     user.id, click_id, user.trader_id, event, amount, currency)
        return {"status": "ok"}
    except Exception:
        db.rollback()
        logging.exception("ERROR_PROCESSING_POSTBACK")
        raise HTTPException(status_code=500, detail="internal_error")
    finally:
        db.close()

@router.get("/postback")
async def postback_get(request: Request):
    params = await _collect_params(request)
    return await _handle(params)

@router.post("/postback")
async def postback_post(request: Request):
    params = await _collect_params(request)
    return await _handle(params)
