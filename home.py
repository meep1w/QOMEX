from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/go-to-signals")
async def go_to_signals(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/auth")

    db = SessionLocal()
    user = db.query(User).filter(User.id == int(user_id)).first()
    db.close()

    if not user:
        return RedirectResponse("/auth")

    if not user.trader_id:
        return RedirectResponse(f"/check?user_id={user.id}")

    if not user.first_deposit or user.first_deposit < 50:
        return RedirectResponse(f"/deposit-check?trader_id={user.trader_id}")

    return RedirectResponse("/dashboard")
