from database import Base, engine
from models import User

# Удаляем и создаём заново таблицы
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("✅ База очищена и пересоздана.")
