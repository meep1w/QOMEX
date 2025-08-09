# check.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
import os

from database import SessionLocal
from models import User, PostbackLog
from utils import gen_click_id, attach_pending_postbacks

router = APIRouter(prefix="/check")
templates = Jinja2Templates(directory="templates")

PO_BASE = "https://u3.shortink.io/smart/16ZjQA8RfjI79Z"
OUT_PARAM_NAME = "click_id"

IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"
SAMESITE_POLICY = "Lax"

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

def _add_params(url: str, params: dict) -> str:
    u = urlsplit(url)
    q = dict(parse_qsl(u.query))
    q.update(params)
    return urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), u.fragment))

def _ref_link_from_request(request: Request) -> tuple[str, str]:
    click_id = request.cookies.get("click_id") or gen_click_id()
    ref_link = _add_params(PO_BASE, {OUT_PARAM_NAME: click_id})
    return click_id, ref_link

@router.get("")
async def check_form(request: Request, db: Session = Depends(get_db), user_id: Optional[int] = None):
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    click_id, ref_link = _ref_link_from_request(request)

    if user_id:
        me = db.get(User, user_id)
        if me:
            changed = False
            if not me.click_id:
                me.click_id = click_id
                changed = True
            if changed:
                db.commit(); db.refresh(me)
            # подтянуть «висящие» события по click_id/trader_id
            attach_pending_postbacks(db, me)

    resp = templates.TemplateResponse("register_check.html", {
        "request": request,
        "user_id": user_id,
        "result": None,
        "ref_link": ref_link,
    })
    resp.set_cookie("click_id", click_id, max_age=60*60*24*30,
                    secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
    return resp

@router.post("")
async def check_trader_id(
    request: Request,
    trader_id: str = Form(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    trader_id = (trader_id or "").strip()
    if user_id is None:
        user_id = _get_user_id_from_cookie(request)

    click_id, ref_link = _ref_link_from_request(request)

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

    # синхронизируем click_id (если надо)
    if not me.click_id and click_id:
        me.click_id = click_id
        db.commit(); db.refresh(me)

    # 1) перед проверкой подтянем все «висящие» логи
    attach_pending_postbacks(db, me)

    # 2) если всё ещё нет trader_id — попробуем найти его ЛОКАЛЬНО в логах по введённому trader_id
    if not me.trader_id and trader_id:
        pb = (db.query(PostbackLog)
                .filter(PostbackLog.trader_id == trader_id)
                .order_by(PostbackLog.id.desc())
                .first())
        if pb:
            # прикрепим трейдер к пользователю и применим все его события
            me.trader_id = trader_id
            db.commit(); db.refresh(me)
            attach_pending_postbacks(db, me)

    # 3) после всех попыток — если trader_id так и нет, показываем ожидание
    if not me.trader_id:
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "user_id": user_id,
            "ref_link": ref_link,
            "result": "⌛ Мы ещё не получили ваш Trader ID от брокера. "
                      "Убедитесь, что регистрировались по нашей ссылке и попробуйте позже.",
        })

    # 4) строгая сверка введённого id с тем, что в БД (на случай опечаток)
    if trader_id and trader_id != (me.trader_id or ""):
        return templates.TemplateResponse("register_check.html", {
            "request": request,
            "user_id": user_id,
            "ref_link": ref_link,
            "result": "❌ Введённый Trader ID не совпадает с данными от брокера.",
        })

    # 5) всё ок — идём на проверку депозита
    resp = RedirectResponse(url=f"/deposit-check?trader_id={me.trader_id}", status_code=302)
    resp.set_cookie("trader_id", me.trader_id, max_age=60*60*24*30,
                    secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
    return resp
