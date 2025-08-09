from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/auth")

    db = SessionLocal()
    user = db.query(User).filter(User.id == int(user_id)).first()
    db.close()

    if not user:
        return RedirectResponse("/auth")

    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

