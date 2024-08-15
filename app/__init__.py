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
                        bcs_fbl5n.account,
                        sat.client_name,
                        sat.rfc,
                        TO_CHAR(sat.cfdi_date, 'DD/MM/YYYY') AS formatted_date_cfdi_date,
                        sat.receipt_number,
                        sat.fiscal_uuid,
                        sat.product_or_service,
                        sat.currency,
                        format_price(sat.subtotal_me) AS formatted_subtotal_me,
                        format_price(sat.discount_me) AS formatted_discount_me,
                        format_price(sat.vat_16_me) AS formatted_vat_16_me,
                        format_price(sat.ieps_me) AS formatted_ieps_me,
                        format_price(sat.vat_withholding_4_me) AS formatted_vat_withholding_4_me,
                        format_price(sat.vat_withholding_2_3_me) AS formatted_vat_withholding_2_3_me,
                        format_price(sat.total_me) AS formatted_total_me,
                        bcs_fbl5n.clearing_document AS clearing_payment_policy,
                        bcs_fbl5n.document_number AS provision_policy_document,
                        bcs_fbl5n.eff_exchange_rate AS t_c_dof,
                        format_price(sat.subtotal_16) AS formatted_subtotal_16,
                        format_price(sat.vat_16) AS formatted_vat_16,
                        format_price(sat.vat_0) AS formatted_vat_0,
                        format_price(sat.ieps) AS formatted_ieps,
                        format_price(sat.subtotal_16 + sat.vat_16 + sat.vat_0 + sat.ieps) AS formatted_total_amount,
                        format_price(sat.income_tax_withholding_me) AS formatted_income_tax_withholding_me,
                        sat.tax_rate,
                        sat.payment_method,
                        format_price(total_amount-bcs_fbl5n.amount_in_local_currency) AS diff_sat_sap
                   FROM sat 
                   JOIN bcs_fbl5n ON sat.receipt_number = bcs_fbl5n.reference
                   
               """)

        # Execute the view creation query
        db.session.execute(create_view_query)
        db.session.commit()

        '''
        bank.bank_name,
                        bank.ref,
                        TO_CHAR(bank.value_date, 'DD/MM/YYYY') AS formatted_date_value_date,
                        bank.comment
        JOIN bank ON sat.receipt_number = bank.ref;
        '''


def init_app():
    app.run(debug=True)


from app import models
