# postback.py
from fastapi import APIRouter, Request, HTTPException
from database import SessionLocal
from models import User, PostbackLog
from datetime import datetime
import os, json, logging, re

router = APIRouter()
POSTBACK_SECRET = os.getenv("POSTBACK_SECRET", "YOUR_SECRET")

logging.basicConfig(filename="/tmp/postback.log", level=logging.INFO,
                    format="%(asctime)s %(message)s")

DIGITS_RE = re.compile(r"^\d+$")

def normalize_event(v: str) -> str:
    v = (v or "").strip().lower()
    if v in ("registration", "register", "signup", "trader_has_registered"):
        return "registration"
    if v in ("deposit", "ftd", "first_deposit", "payment", "trader_has_made_a_deposit"):
        return "deposit"
    return v or "unknown_event"

def parse_amount(v: str) -> float:
    try:
        return float((v or "").replace(",", ".")) if v else 0.0
    except:
        return 0.0

async def _collect_params(request: Request) -> dict:
    params = dict(request.query_params)
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
        except:
            pass
    return params

def _find_user(db, click_id: str, trader_id: str):
    user = None
    if click_id:
        user = db.query(User).filter(User.click_id == click_id).first()
    if user is None and trader_id and DIGITS_RE.match(trader_id):
        user = db.query(User).filter(User.trader_id == trader_id).first()
    return user

def _log_postback(db, params: dict, event: str, click_id: str, trader_id: str,
                  amount: float, currency: str, user_id: int | None, processed: bool):
    plog = PostbackLog(
        event=event,
        click_id=click_id or None,
        trader_id=trader_id or None,
        amount=amount or 0.0,
        currency=(currency or None),
        raw=json.dumps(params, ensure_ascii=False),
        processed=processed,
        user_id=user_id,
        processed_at=datetime.utcnow() if processed else None,
    )
    db.add(plog)

async def _handle(params: dict):
    logging.info("RAW_POSTBACK %s", json.dumps(params, ensure_ascii=False))

    token = params.get("token")
    if token != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")

    event = normalize_event(params.get("event"))
    click_id = (params.get("click_id") or "").strip()
    trader_id = (params.get("trader_id") or "").strip()
    amount = parse_amount(params.get("amount") or "")
    currency = (params.get("currency") or "").strip().upper()

    db = SessionLocal()
    try:
        user = _find_user(db, click_id, trader_id)

        if user is None:
            # Пользователя нет — просто логируем (ожидаем, что появится позже)
            _log_postback(db, params, event, click_id, trader_id, amount, currency, None, False)
            db.commit()
            return {"status": "no_user_yet", "click_id": click_id or None}

        # Пользователь найден — обновляем его профиль по событию
        user.updated_at = datetime.utcnow()
        if (not user.trader_id) and trader_id and DIGITS_RE.match(trader_id):
            user.trader_id = trader_id  # НЕ трогаем, если уже установлен

        if event == "deposit" and amount > 0:
            # first_deposit заполняем, если ещё не было
            if user.first_deposit is None:
                user.first_deposit = amount
            user.total_deposit = (user.total_deposit or 0.0) + amount

        # лог помечаем обработанным
        _log_postback(db, params, event, click_id, trader_id, amount, currency, user.id, True)
        db.commit()
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
