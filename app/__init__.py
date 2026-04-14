# app/__init__.py
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import SQLALCHEMY_DATABASE_URI
from app.models import Base
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    app.secret_key = 'TainaMaina'

    # SQLAlchemy setup
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    app.session = DBSession()

    from app.routes import main
    app.register_blueprint(main)

    return app
