from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()  # ❗️Не нужен prefix

templates = Jinja2Templates(directory="templates")

@router.get("/cookie.html", response_class=HTMLResponse)
async def cookie_policy(request: Request):
    return templates.TemplateResponse("cookie.html", {"request": request})

@router.get("/terms.html", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@router.get("/privacy.html", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@router.post("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    response.delete_cookie("user_email")
    return response


# routes.py (или другой ваш роутер)
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import urllib.parse, secrets, os

router = APIRouter()

IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"
SAMESITE_POLICY = "Lax"

# ВСТАВЬ свою партнёрскую ссылку (ту, что нажимает пользователь)
# Важно: БЕЗ click_id — мы добавим его сами.
AFF_URL = "https://u3.shortink.io/smart/16ZjQA8RfjI79Z"

def ensure_click_id(request: Request) -> str:
    cid = request.cookies.get("click_id")
    if not cid:
        cid = secrets.token_urlsafe(8)
    return cid

@router.get("/go-broker")
def go_broker(request: Request):
    cid = ensure_click_id(request)
    # допишем click_id в партнёрскую ссылку
    url = AFF_URL + ("&" if "?" in AFF_URL else "?") + urllib.parse.urlencode({"click_id": cid})
    resp = RedirectResponse(url, status_code=302)
    # положим click_id в куку (если его не было)
    resp.set_cookie("click_id", cid, max_age=60*60*24*30,
                    secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
    return resp
