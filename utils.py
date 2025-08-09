# utils.py
import secrets
import string
from datetime import datetime
from models import PostbackLog, User  # импортируем модель

def gen_click_id(n: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "_-"
    return ''.join(secrets.choice(alphabet) for _ in range(n))

def attach_pending_postbacks(db, user: User):
    """
    При связывании пользователя переносит все необработанные постбэки на него.
    """
    q = db.query(PostbackLog).filter(PostbackLog.processed == False)
    if user.click_id:
        q = q.filter(PostbackLog.click_id == user.click_id)
    elif user.trader_id:
        q = q.filter(PostbackLog.trader_id == user.trader_id)
    else:
        return

    logs = q.all()
    if not logs:
        return

    for pb in logs:
        if pb.event == "deposit" and (pb.amount or 0) > 0:
            if user.first_deposit is None:
                user.first_deposit = pb.amount
            user.total_deposit = (user.total_deposit or 0.0) + (pb.amount or 0.0)

        pb.user_id = user.id
        pb.processed = True
        pb.processed_at = datetime.utcnow()

    user.updated_at = datetime.utcnow()
    db.commit()
