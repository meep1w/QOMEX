# users.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

router = APIRouter()

# Зависимость для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    users_data = [
        {
            "id": u.id,
            "login": u.login,
            "email": u.email,
            "trader_id": u.trader_id,
            "first_deposit": u.first_deposit,
            "total_deposit": u.total_deposit,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            "click_id": u.click_id
        }
        for u in users
    ]
    return JSONResponse({"users": users_data})

@router.post("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    return response
