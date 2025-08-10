# routes.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse, secrets, os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"
SAMESITE_POLICY = "Lax"

# смарт-рефка БЕЗ click_id — добавим сами
AFF_URL = "https://u3.shortink.io/smart/16ZjQA8RfjI79Z"

def ensure_click_id(request: Request) -> str:
    cid = request.cookies.get("click_id")
    return cid or secrets.token_urlsafe(8)

# ---------- Инфостраницы ----------

@router.get("/cookie.html", response_class=HTMLResponse)
async def cookie_policy(request: Request):
    return templates.TemplateResponse("cookie.html", {"request": request})

@router.get("/terms.html", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@router.get("/privacy.html", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


def _delete_auth_cookies(resp: RedirectResponse):
    # удаляем с теми же атрибутами и path="/"
    for name in ["user_id", "user_email", "click_id"]:
        resp.delete_cookie(name, secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY, path="/")

@router.post("/logout")
async def logout_post():
    resp = RedirectResponse("/", status_code=303)
    _delete_auth_cookies(resp)
    return resp

@router.get("/logout")
async def logout_get():
    resp = RedirectResponse("/", status_code=303)
    _delete_auth_cookies(resp)
    return resp


# ---------- Переход на брокера ----------

@router.get("/go-broker")
def go_broker(request: Request):
    cid = ensure_click_id(request)
    url = AFF_URL + ("&" if "?" in AFF_URL else "?") + urllib.parse.urlencode({"click_id": cid})
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie("click_id", cid, max_age=60*60*24*30,
                    secure=IS_SECURE_COOKIES, samesite=SAMESITE_POLICY)
    return resp


# --- SEO: robots.txt & sitemap.xml ---
from fastapi.responses import PlainTextResponse, Response
import os as _os

BASE_URL = _os.getenv("BASE_URL", "https://qomex.top")

@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return f"""User-agent: *
Allow: /
Disallow: /profile
Disallow: /auth/reset
Sitemap: {BASE_URL}/sitemap.xml
""".strip()

@router.get("/sitemap.xml")
def sitemap():
    urls = [
        "/",              # главная
        "/auth",
        "/go-to-signals",
        "/privacy.html",
        "/terms.html",
        "/cookie.html",
        # добавишь сюда свои новые SEO-страницы, например: "/signals"
    ]
    items = "\n".join(f"<url><loc>{BASE_URL}{p}</loc></url>" for p in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{items}"
        "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")
