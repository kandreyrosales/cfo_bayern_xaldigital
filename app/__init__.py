from flask import Flask
from config import Config
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'xaldigitalcfobayer!'
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024
app.config.from_object(Config)

db = SQLAlchemy(app)


def create_db():
    with app.app_context():
        db.create_all()


def destroy_db():
    with app.app_context():
        db.drop_all()


def create_conciliations_view():
    with app.app_context():
        view_query = text("""
           CREATE VIEW conciliations_view AS
           SELECT
               sat.cfdi_date,
               sat.receipt_number,
               sat.fiscal_uuid,
               sat.product_or_service,
               sat.currency,
               sat.subtotal_16,
               sat.vat_16,
               sat.vat_0,
               sat.ieps,
               sat.total_amount,
               sat.payment_method,
               sat.subtotal_me,
               sat.discount_me,
               sat.vat_16_me,
               sat.ieps_me,
               sat.vat_withholding_4_me,
               sat.vat_withholding_2_3_me,
               sat.total_me,
               bcs_fbl5n.clearing_document
               
           FROM
               sat
           JOIN
               bcs_fbl5n ON sat.receipt_number = bcs_fbl5n.reference;
           """)
        db.session.execute(view_query)
        db.session.commit()


def init_app():
    app.run(debug=True)


from app import models
