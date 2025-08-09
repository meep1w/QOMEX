# check.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import SessionLocal
from models import User
from utils import gen_click_id

router = APIRouter(prefix="/check")
templates = Jinja2Templates(directory="templates")

PO_BASE = "https://u3.shortink.io/register?utm_campaign=824666&utm_source=affiliate&utm_medium=sr&a=16ZjQA8RfjI79Z&ac=qomex&code=EIX228"
OUT_PARAM_NAME = "click_id"  # если у PP другое имя для {click_id} в ссылке — поменяй тут

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
    except:
        return None

def _ref_link_from_request(request: Request) -> tuple[str, str]:
    click_id = request.cookies.get("click_id") or gen_click_id()
    ref_link = f"{PO_BASE}&{OUT_PARAM_NAME}={click_id}"
    return click_id, ref_link

@router.get("")
async def check_form(request: Request, db: Session = Depends(get_db), user_id: Optional[int] = None):
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    click_id, ref_link = _ref_link_from_request(request)

    if user_id:
        me = db.get(User, user_id)  # SQLAlchemy 2.x
        if me and not me.click_id:
            me.click_id = click_id
            db.commit()

    resp = templates.TemplateResponse("register_check.html", {
        "request": request,
        "user_id": user_id,
        "result": None,
        "ref_link": ref_link,
    })
    resp.set_cookie(key="click_id", value=click_id, max_age=60*60*24*30)
    return resp

@router.post("")
async def check_trader_id(
    request: Request,
    trader_id: str = Form(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    click_id, ref_link = _ref_link_from_request(request)

    # 1) Должен быть авторизован
    if user_id is None:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Пользователь не авторизован. Пожалуйста, войдите.",
            "user_id": None,
            "ref_link": ref_link,
        })

    me = db.get(User, user_id)
    if not me:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "result": "❌ Аккаунт не найден.",
            "user_id": user_id,
            "ref_link": ref_link,
        })

    # 2) Проверяем, что постбэк УЖЕ записал trader_id юзеру
    if not me.trader_id:
        # постбэк еще не пришёл или не сматчился по click_id
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "user_id": user_id,
            "ref_link": ref_link,
            "result": "⌛ Мы ещё не получили ваш Trader ID от брокера. "
                      "Убедитесь, что регистрировались по нашей ссылке и попробуйте чуть позже.",
        })

    # 3) Строгое сравнение: введённый trader_id должен совпасть с тем, что пришёл постбэком
    if trader_id.strip() != (me.trader_id or "").strip():
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "user_id": user_id,
            "ref_link": ref_link,
            "result": "❌ Введённый Trader ID не совпадает с данными от брокера.",
        })

    # 4) Совпало — пускаем дальше на проверку депозита
    resp = RedirectResponse(url=f"/deposit-check?trader_id={trader_id}", status_code=302)
    resp.set_cookie(key="trader_id", value=trader_id, max_age=60*60*24*30)
    return resp
