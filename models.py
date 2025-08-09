from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    click_id = Column(String, unique=True, nullable=False, index=True)
    trader_id = Column(String, unique=True, nullable=True)
    first_deposit = Column(Float, nullable=True)
    total_deposit = Column(Float, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, login='{self.login}', click_id='{self.click_id}', trader_id='{self.trader_id}')>"
