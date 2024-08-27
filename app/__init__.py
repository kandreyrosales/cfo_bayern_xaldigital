from flask import Flask
from .config import Config
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "xaldigitalcfobayer!"
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024
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
        create_function_query = text(
            """
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
        """
        )

        # Execute the function creation query
        db.session.execute(create_function_query)

        # Then, create or replace the view
        create_view_query = text(
            """
            CREATE OR REPLACE VIEW conciliations_view AS
                SELECT 
                    (
                        SELECT bcs_fbl5n.account 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    ) AS account,
                    sat.client_name,
                    sat.rfc,
                    TO_CHAR(sat.cfdi_date, 'DD/MM/YYYY') AS formatted_date_cfdi_date,
                    sat.cfdi_date,
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
                    (
                        SELECT bcs_fbl5n.clearing_document 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    ) AS clearing_payment_policy,
                    (
                        SELECT bcs_fbl5n.document_number 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    ) AS provision_policy_document,
                    (
                        SELECT bcs_fbl5n.eff_exchange_rate 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    ) AS t_c_dof,
                    format_price(sat.subtotal_16) AS formatted_subtotal_16,
                    format_price(sat.vat_16) AS formatted_vat_16,
                    format_price(sat.vat_0) AS formatted_vat_0,
                    format_price(sat.ieps) AS formatted_ieps,
                    format_price(sat.total_amount) AS formatted_total_amount,
                    format_price(sat.income_tax_withholding_me) AS formatted_income_tax_withholding_me,
                    sat.subtotal_16,
                    sat.vat_16,
                    sat.vat_0,
                    sat.ieps,
                    sat.total_amount AS total_amount,
                    sat.income_tax_withholding_me,
                    sat.tax_rate,
                    sat.payment_method,
                    (
                        SELECT bcs_fbl5n.invoice_reference 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    ) AS invoice_reference,
                    format_price(sat.total_amount - (
                        SELECT bcs_fbl5n.amount_in_local_currency 
                        FROM bcs_fbl5n 
                        WHERE bcs_fbl5n.reference = sat.receipt_number
                        LIMIT 1
                    )) AS diff_sat_sap,
                    COALESCE(
                        (
                            SELECT bcs_ieps_2440020.amount_in_doc_curr
                            FROM bcs_ieps_2440020
                            WHERE bcs_ieps_2440020.clearing_document = (
                                SELECT bcs_fbl5n.clearing_document 
                                FROM bcs_fbl5n 
                                WHERE bcs_fbl5n.reference = sat.receipt_number
                                LIMIT 1
                            )
                            LIMIT 1
                        ), 
                        0
                    ) AS amount_in_doc_curr_ieps,
                    COALESCE(
                        (
                            SELECT bhc_iva_traladado_2440015.amount_in_doc_curr
                            FROM bhc_iva_traladado_2440015
                            WHERE bhc_iva_traladado_2440015.clearing_document = (
                                SELECT bcs_fbl5n.clearing_document 
                                FROM bcs_fbl5n 
                                WHERE bcs_fbl5n.reference = sat.receipt_number
                                LIMIT 1
                            )
                            LIMIT 1
                        ), 
                        0
                    ) AS amount_in_doc_curr_iva_traladado
                FROM 
                    sat
                WHERE 
                    sat.payment_method = 'PUE' OR sat.payment_method = 'PPD';
               """
        )

        # Execute the view creation query
        db.session.execute(create_view_query)
        db.session.commit()


def init_app():
    app.run(debug=True)


from app import models
