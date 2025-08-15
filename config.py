# config.py
import os

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "4753"
DB_NAME = "attendance_db"
SECRET_KEY = "change_this_secret_key"


# Flask secret key (change in production)
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_key")
