from fastapi import APIRouter, Request
from database import SessionLocal
from models import User
from datetime import datetime

router = APIRouter()

@router.get("/postback")
async def handle_postback(request: Request):
    params = dict(request.query_params)
    event = params.get("event")
    click_id = params.get("click_id")
    trader_id = params.get("trader_id")
    amount = params.get("amount")

    db = SessionLocal()
    user = db.query(User).filter(User.click_id == click_id).first()

    if event == "registration":
        if user and trader_id:
            user.trader_id = trader_id
            user.updated_at = datetime.utcnow()
            db.commit()
            db.close()
            return {"status": "registered"}
        else:
            db.close()
            return {"error": "User with this click_id not found. Please register on site first."}

    elif event == "first_deposit":
        if user and amount:
            try:
                deposit_amount = float(amount)
            except ValueError:
                db.close()
                return {"error": "Invalid amount format"}

            if not user.first_deposit:
                user.first_deposit = deposit_amount
            else:
                user.first_deposit = min(user.first_deposit, deposit_amount)  # optional logic
            user.total_deposit = (user.total_deposit or 0) + deposit_amount
            user.updated_at = datetime.utcnow()
            db.commit()
            db.close()
            return {"status": "deposit recorded", "amount": deposit_amount}
        else:
            db.close()
            return {"error": "User with this click_id not found or missing amount"}

    else:
        db.close()
        return {"error": "Invalid or missing event parameter"}
