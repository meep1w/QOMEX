from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/deposit-check", response_class=HTMLResponse)
async def deposit_check(request: Request, trader_id: str):
    db = SessionLocal()
    user = db.query(User).filter(User.trader_id == trader_id).first()
    db.close()

    if user and user.first_deposit and user.first_deposit >= 50:
        return templates.TemplateResponse("deposit_check.html", {
            "request": request,
            "status": "success",
            "amount": user.first_deposit
        })
    else:
        return templates.TemplateResponse("deposit_check.html", {
            "request": request,
            "status": "fail"
        })
