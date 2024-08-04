from app import db, app
from datetime import datetime


class Banco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rfc = db.Column(db.String(80), nullable=False)
    uuid = db.Column(db.String(120), nullable=False)
    fiscal = db.Column(db.String(120), nullable=False)
    s3_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Banco {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Sat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s3_url = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    state = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Sat {self.id}>'
