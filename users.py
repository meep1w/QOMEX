# users.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database import SessionLocal
from models import User

router = APIRouter()

@router.get("/users")
async def get_all_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    users_data = []
    for u in users:
        users_data.append({
            "id": u.id,
            "login": u.login,
            "email": u.email,
            "trader_id": u.trader_id,
            "first_deposit": u.first_deposit,
            "total_deposit": u.total_deposit,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            "click_id": u.click_id
        })
    return JSONResponse({"users": users_data})


from fastapi.responses import JSONResponse


class RedirectResponse:
    pass


@router.post("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    return response
