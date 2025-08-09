from fastapi import APIRouter, Request, HTTPException
from database import SessionLocal
from models import User
from datetime import datetime
import os

router = APIRouter()

POSTBACK_SECRET = os.getenv("POSTBACK_SECRET", "YOUR_SECRET")  # положи такой же в .env

@router.get("/postback")
async def handle_postback(request: Request):
    params = dict(request.query_params)

    # Безопасность
    token = params.get("token")
    if token != POSTBACK_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")

    # Нормализация событий и параметров из разных источников
    raw_event = (params.get("event") or "").lower()
    if raw_event in ("register", "registration", "reg"):
        event = "register"
    elif raw_event in ("deposit", "first_deposit", "repeated_deposit"):
        event = "deposit"
    else:
        event = raw_event  # неизвестное — отдадим как есть

    click_id = params.get("click_id")
    trader_id = params.get("trader_id")

    # сумма может приходить как sumdep (PP) или amount (твоя логика)
    amount_str = params.get("sumdep") or params.get("amount")
    amount = None
    if amount_str:
        try:
            amount = float(amount_str)
        except ValueError:
            amount = None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.click_id == click_id).first()

        if event == "register":
            if user and trader_id:
                user.trader_id = trader_id
                user.updated_at = datetime.utcnow()
                db.commit()
                return {"status": "registered", "click_id": click_id, "trader_id": trader_id}
            else:
                return {"status": "no_user_or_trader_id", "click_id": click_id}

        elif event == "deposit":
            if user and amount is not None:
                # первый депозит
                if not getattr(user, "first_deposit", None):
                    user.first_deposit = amount
                else:
                    # не увеличиваем first_deposit, просто фиксируем как min при желании
                    user.first_deposit = min(user.first_deposit, amount)

                # суммарные депозиты
                user.total_deposit = (user.total_deposit or 0.0) + amount

                # флаг прохождения порога $50 для твоей deposit_check
                if amount >= 50:
                    # если у тебя есть поле, типа user.deposit_verified = True — обнови его
                    if hasattr(user, "deposit_verified") and not user.deposit_verified:
                        user.deposit_verified = True

                user.updated_at = datetime.utcnow()
                db.commit()
                return {
                    "status": "deposit_recorded",
                    "click_id": click_id,
                    "trader_id": trader_id,
                    "amount": amount,
                    "total_deposit": user.total_deposit
                }
            else:
                return {"status": "no_user_or_amount", "click_id": click_id}

        else:
            return {"status": "unknown_event", "event": raw_event}

    finally:
        db.close()
