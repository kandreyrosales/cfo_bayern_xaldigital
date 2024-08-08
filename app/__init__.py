from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024
app.config.from_object(Config)

db = SQLAlchemy(app)

with app.app_context():
    db.drop_all()
    db.create_all()

from app import models
