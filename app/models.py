from app import db, app
from datetime import datetime


class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bank_name = db.Column(db.String(250), nullable=False)
    account_number = db.Column(db.String(250), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    book_date = db.Column(db.DateTime, nullable=False)
    value_date = db.Column(db.DateTime, nullable=False)
    posting_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(250), nullable=False)
    ref = db.Column(db.String(250), nullable=False)
    addref = db.Column(db.String(250), nullable=False)
    posting_text = db.Column(db.String(250), nullable=False)
    payer = db.Column(db.String(250), nullable=False)
    classification = db.Column(db.String(250), nullable=False)
    comment = db.Column(db.String(250), nullable=False)
    s3_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Banco {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Sat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cfdi_date = db.Column(db.DateTime, nullable=False)
    vat_withholding_4_me = db.Column(db.Float, nullable=False)
    receipt_number = db.Column(db.String(250), nullable=False)
    vat_withholding_2_3_me = db.Column(db.Float, nullable=False)
    fiscal_uuid = db.Column(db.String(250), nullable=False)
    total_me = db.Column(db.Float, nullable=False)
    product_or_service = db.Column(db.String(250), nullable=False)
    subtotal_16 = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(250), nullable=False)
    vat_16 = db.Column(db.Float, nullable=False)
    subtotal_me = db.Column(db.Float, nullable=False)
    vat_0 = db.Column(db.Float, nullable=False)
    discount_me = db.Column(db.Float, nullable=False)
    ieps = db.Column(db.Float, nullable=False)
    vat_16_me = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    ieps_me = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(250), nullable=False)
    income_tax_withholding_me = db.Column(db.Float, nullable=False)
    payment_supplement = db.Column(db.Float, nullable=False)
    s3_url = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Sat {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Sap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    client_number = db.Column(db.String(250), nullable=False)
    client_name = db.Column(db.String(250), nullable=False)
    rfc = db.Column(db.String(250), nullable=False)
    clearing_payment_policy = db.Column(db.String(250), nullable=False)
    provision_policy_document = db.Column(db.String(250), nullable=False)
    s3_url = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Sap {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Dof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exchange_rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Dof {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class BankStatement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bank_account_name = db.Column(db.String(250), nullable=False)
    bank_account_number = db.Column(db.String(250), nullable=False)
    bank_reference = db.Column(db.String(250), nullable=False)
    bank_payment_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<BankStatement {self.id}>'

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()
