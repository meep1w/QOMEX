# routes.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.parse, secrets, os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

IS_SECURE_COOKIES = os.getenv("ENV", "dev") != "dev"
SAMESITE_POLICY = "Lax"

BASE_URL = os.getenv("BASE_URL", "https://qomex.top")

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
from fastapi import Request
from fastapi.responses import (
    PlainTextResponse,
    HTMLResponse,
    RedirectResponse,

)
from xml.etree.ElementTree import Element, SubElement, tostring

# ---------- robots.txt ----------
@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    body = f"""User-agent: *
Allow: /
Disallow: /profile
Disallow: /auth/reset
Sitemap: {BASE_URL}/sitemap.xml
""".strip()
    return PlainTextResponse(
        body,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )

from fastapi.responses import Response

@router.head("/robots.txt")
def robots_head():
    # HEAD для robots.txt: отдать только заголовки, без тела
    return Response(
        status_code=200,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


# ---------- sitemap.xml ----------
@router.get("/sitemap.xml")
def sitemap():
    urls = [
        "/", "/auth", "/signals",
        "/privacy.html", "/terms.html", "/cookie.html",
    ]
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path in urls:
        url = SubElement(urlset, "url")
        loc = SubElement(url, "loc")
        loc.text = f"{BASE_URL}{path}"

    xml = '<?xml version="1.0" encoding="UTF-8"?>' + tostring(urlset, encoding="unicode")
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Cache-Control": "no-store"},
    )

# HEAD для sitemap (чтобы не было 405 на HEAD)
@router.head("/sitemap.xml")
def sitemap_head():
    return Response(status_code=200, media_type="application/xml")

# ---------- Страница /signals и редирект со старого пути ----------
@router.get("/signals", response_class=HTMLResponse)
def signals_page(request: Request):
    return templates.TemplateResponse("signals.html", {"request": request})

@router.get("/go-to-signals")
def go_to_signals():
    return RedirectResponse("/signals", status_code=301)
