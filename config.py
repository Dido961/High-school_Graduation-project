# config.py
DB_USERNAME = 'root'
DB_PASSWORD = '1234'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'ecommerce_db'

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
