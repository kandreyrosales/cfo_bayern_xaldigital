import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    db_host = os.getenv("db_endpoint")
    db_name = os.getenv("db_name")
    db_user = os.getenv("username_db")
    db_password = os.getenv("password_db")
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
