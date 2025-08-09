# deposit_check.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MIN_DEPOSIT = 50.0

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cookie(request: Request, key: str) -> Optional[str]:
    return request.cookies.get(key)

@router.get("/deposit-check")
async def deposit_check(
    request: Request,
    trader_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # если trader_id не передали в query — попробуем взять из cookie
    if not trader_id:
        trader_id = get_cookie(request, "trader_id")

    ctx = {
        "request": request,
        "status": "fail",
        "amount": 0.0,
        "first_deposit": 0.0,
        "total_deposit": 0.0,
        "min_deposit": MIN_DEPOSIT,
        "trader_id": trader_id,
    }

    if not trader_id:
        # просто отрисуем страницу с формой ввода trader_id
        return templates.TemplateResponse("deposit_check.html", ctx)

    user = db.query(User).filter(User.trader_id == trader_id).first()
    if not user:
        return templates.TemplateResponse("deposit_check.html", ctx)

    first = float(user.first_deposit or 0.0)
    total = float(user.total_deposit or 0.0)

    # критерий прохождения: либо первый депозит ≥ 50, либо суммарно ≥ 50
    passed = (first >= MIN_DEPOSIT) or (total >= MIN_DEPOSIT)

    ctx.update({
        "status": "success" if passed else "fail",
        "amount": first if first >= MIN_DEPOSIT else total,
        "first_deposit": first,
        "total_deposit": total,
    })

    return templates.TemplateResponse("deposit_check.html", ctx)
