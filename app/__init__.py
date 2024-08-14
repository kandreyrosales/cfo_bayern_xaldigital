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
        # First, create the format_price function
        create_function_query = text("""
            CREATE OR REPLACE FUNCTION format_price(price DOUBLE PRECISION)
            RETURNS TEXT AS $$
            BEGIN
              IF price = 0 THEN
                RETURN '$0';
              ELSE
                RETURN to_char(price, 'FM$999,999,999.00');
              END IF;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Execute the function creation query
        db.session.execute(create_function_query)

        # Then, create or replace the view
        create_view_query = text("""
                   CREATE OR REPLACE VIEW conciliations_view AS
                   SELECT
                        TO_CHAR(sat.cfdi_date, 'DD/MM/YYYY') AS formatted_date_cfdi_date,
                        sat.receipt_number,
                        sat.fiscal_uuid,
                        sat.product_or_service,
                        sat.currency,
                        format_price(sat.subtotal_16) AS formatted_subtotal_16,
                        format_price(sat.vat_16) AS formatted_vat_16,
                        format_price(sat.vat_0) AS formatted_vat_0,
                        format_price(sat.ieps) AS formatted_ieps,
                        format_price(sat.total_amount) AS formatted_total_amount,
                        sat.payment_method,
                       format_price(sat.subtotal_me) AS formatted_subtotal_me,
                       format_price(sat.discount_me) AS formatted_discount_me,
                       format_price(sat.vat_16_me) AS formatted_vat_16_me,
                       format_price(sat.ieps_me) AS formatted_ieps_me,
                       format_price(sat.vat_withholding_4_me) AS formatted_vat_withholding_4_me,
                       format_price(sat.vat_withholding_2_3_me) AS formatted_vat_withholding_2_3_me,
                       format_price(sat.total_me) AS formatted_total_me,
                       format_price((subtotal_me - discount_me + vat_16_me + ieps_me - income_tax_withholding_me 
                        - vat_withholding_4_me - vat_withholding_2_3_me)) AS total_me,
                         
                        format_price((subtotal_16 + vat_16 + vat_0 + ieps - vat_withholding_4_me - vat_withholding_2_3_me 
                         - income_tax_withholding_me)) AS total_amount,
                        bcs_fbl5n.clearing_document AS clearing_document,
                       CASE WHEN EXISTS(
                           SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                       ) THEN (
                           SELECT posting_amount from bank bk
                           WHERE bk.ref IN (
                               SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                           )
                       )
                       ELSE (
                           SELECT posting_amount from bank bk
                           WHERE bk.ref IN (
                               SELECT document_number from bhc_iva_traladado_2440015 where reference=sat.receipt_number
                           )
                       )
                       END AS deposits,

                       CASE WHEN EXISTS(
                           SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                       ) THEN (
                           SELECT bank_name from bank bk
                           WHERE bk.ref IN (
                               SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                           )
                       )
                       ELSE (
                           SELECT bank_name from bank bk WHERE bk.ref IN (
                               SELECT document_number from bhc_iva_traladado_2440015 where reference=sat.receipt_number
                           )
                       )
                       END AS bank_name,

                       CASE WHEN EXISTS(
                           SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                       ) THEN (
                           SELECT TO_CHAR(value_date, 'DD/MM/YYYY') from bank bk
                           WHERE  bk.ref IN (
                               SELECT document_number from bcs_iva_cobrado_2440015 where reference=sat.receipt_number
                           )
                       )
                       ELSE (
                           SELECT TO_CHAR(value_date, 'DD/MM/YYYY') from bank bk
                           WHERE bk.ref IN (
                               SELECT document_number from bhc_iva_traladado_2440015 where reference=sat.receipt_number
                           )
                       )
                       END AS deposit_date,

                       CASE WHEN EXISTS(
                            SELECT document_number from bcs_fbl5n where reference=sat.receipt_number
                       ) THEN (
                           SELECT document_number from bcs_fbl5n where reference=sat.receipt_number
                       )
                        ELSE (
                             SELECT clearing_document from bcs_fbl5n where invoice_reference=sat.receipt_number
                        )
                       END AS document_number
                   FROM sat 
                   JOIN bcs_fbl5n ON sat.receipt_number = bcs_fbl5n.reference;
               """)

        # Execute the view creation query
        db.session.execute(create_view_query)
        db.session.commit()


def init_app():
    app.run(debug=True)


from app import models
