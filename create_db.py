# app/create_db.py
from sqlalchemy import create_engine
from app.models import Base
from config import SQLALCHEMY_DATABASE_URI

def create_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
    Base.metadata.create_all(engine)
    print("Базата данни е създадена успешно.")

if __name__ == "__main__":
    create_database()
