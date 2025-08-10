# models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # хранить хэш
    click_id = Column(String(255), unique=True, nullable=False, index=True)
    trader_id = Column(String(255), unique=True, nullable=True)
    first_deposit = Column(Float, nullable=True)
    total_deposit = Column(Float, nullable=False, default=0.0)
    deposit_verified = Column(Boolean, default=False)
    reset_token = Column(String(255), nullable=True)  # <-- добавлено
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (f"<User(id={self.id}, login='{self.login}', click_id='{self.click_id}', "
                f"trader_id='{self.trader_id}', total_deposit={self.total_deposit})>")


class PostbackLog(Base):
    __tablename__ = "postbacks_log"

    id = Column(Integer, primary_key=True)
    event = Column(String(50))
    click_id = Column(String(255), index=True)
    trader_id = Column(String(255), index=True)
    amount = Column(Float)
    currency = Column(String(10))
    raw = Column(Text)  # сырые параметры постбэка (JSON строкой)
    processed = Column(Boolean, default=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (f"<PostbackLog(id={self.id}, event='{self.event}', click_id='{self.click_id}', "
                f"trader_id='{self.trader_id}', amount={self.amount}, processed={self.processed})>")
