from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
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
    deposit_verified = Column(Boolean, default=False)  # флаг прохождения проверки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (f"<User(id={self.id}, login='{self.login}', click_id='{self.click_id}', "
                f"trader_id='{self.trader_id}', total_deposit={self.total_deposit})>")
