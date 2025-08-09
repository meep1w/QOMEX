from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from typing import Optional
from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/check")
async def check_form(request: Request, user_id: Optional[int] = None):
    # Показываем форму с hidden user_id, если он есть
    return templates.TemplateResponse("register_check.html", {
        "request": request,
        "user_id": user_id,
        "result": None
    })

@router.post("/check")
async def check_trader_id(
    request: Request,
    trader_id: str = Form(...),
    user_id: Optional[int] = Form(None)
):
    db = SessionLocal()

    if user_id is None:
        db.close()
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Пользователь не авторизован. Пожалуйста, войдите.",
            "user_id": None
        })

    # Проверяем, зарегистрирован ли такой trader_id
    existing_user = db.query(User).filter(User.trader_id == trader_id).first()
    if not existing_user:
        db.close()
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Этот Trader ID не зарегистрирован. Пожалуйста, зарегистрируйтесь через нашу реферальную ссылку.",
            "user_id": user_id
        })

    # Если trader_id есть, но принадлежит другому пользователю — ошибка
    if existing_user.id != user_id:
        db.close()
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Этот Trader ID уже используется другим аккаунтом.",
            "user_id": user_id
        })

    # Всё ок — trader_id принадлежит текущему пользователю
    response = RedirectResponse(url=f"/deposit-check?trader_id={trader_id}", status_code=302)
    response.set_cookie(key="trader_id", value=trader_id)
    db.close()
    return response

