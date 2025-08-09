# check.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import SessionLocal
from models import User

router = APIRouter(prefix="/check")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _get_user_id_from_cookie(request: Request) -> Optional[int]:
    v = request.cookies.get("user_id")
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

@router.get("")
async def check_form(request: Request,
                     user_id: Optional[int] = None):
    # если user_id не передали — берём из cookie
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    return templates.TemplateResponse("register_check.html", {
        "request": request,
        "user_id": user_id,
        "result": None
    })

@router.post("")
async def check_trader_id(request: Request,
                          trader_id: str = Form(...),
                          user_id: Optional[int] = Form(None),
                          db: Session = Depends(get_db)):
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    if user_id is None:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Пользователь не авторизован. Пожалуйста, войдите.",
            "user_id": None
        })

    # ищем пользователя по этому trader_id
    existing_user = db.query(User).filter(User.trader_id == trader_id).first()
    if not existing_user:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Этот Trader ID не зарегистрирован. Пожалуйста, зарегистрируйтесь через нашу реферальную ссылку.",
            "user_id": user_id
        })

    # trader_id найден, но принадлежит не этому аккаунту
    if existing_user.id != user_id:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Этот Trader ID уже используется другим аккаунтом.",
            "user_id": user_id
        })

    # всё ок — редиректим к проверке депозита
    url = f"/deposit-check?trader_id={trader_id}"
    resp = RedirectResponse(url=url, status_code=302)
    resp.set_cookie(key="trader_id", value=trader_id)
    return resp
