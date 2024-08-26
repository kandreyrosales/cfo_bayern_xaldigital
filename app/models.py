from app import db, app
from sqlalchemy import text
from datetime import datetime
from sqlalchemy import func


class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bank_name = db.Column(db.String(250), nullable=False)
    account_number = db.Column(db.String(250), nullable=True)
    number = db.Column(db.Integer, nullable=True)
    book_date = db.Column(db.DateTime, nullable=True)
    value_date = db.Column(db.DateTime, nullable=True)
    posting_amount = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    payment_method = db.Column(db.String(250), nullable=True)
    ref = db.Column(db.String(250), nullable=True)
    addref = db.Column(db.String(250), nullable=True)
    posting_text = db.Column(db.String(250), nullable=True)
    payer = db.Column(db.String(250), nullable=True)
    classification = db.Column(db.String(250), nullable=True)
    comment = db.Column(db.String(250), nullable=True)
    s3_url = db.Column(db.String(250), nullable=True)
    file_name = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Banco {self.id}>"

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Sat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cfdi_date = db.Column(db.DateTime, nullable=False)
    cfdi_use = db.Column(db.String(250), nullable=False)
    rfc = db.Column(db.String(250), nullable=False)
    client_name = db.Column(db.String(250), nullable=False)
    vat_withholding_4_me = db.Column(db.Float, nullable=False, default=0)
    receipt_number = db.Column(db.String(250), nullable=False)
    vat_withholding_2_3_me = db.Column(db.Float, nullable=False, default=0)
    fiscal_uuid = db.Column(db.String(250), nullable=False)
    total_me = db.Column(db.Float, nullable=False, default=0)
    product_or_service = db.Column(db.String(250), nullable=False)
    subtotal_16 = db.Column(db.Float, nullable=False, default=0)
    currency = db.Column(db.String(250), nullable=False)
    vat_16 = db.Column(db.Float, nullable=False, default=0)
    subtotal_me = db.Column(db.Float, nullable=False, default=0)
    vat_0 = db.Column(db.Float, nullable=False, default=0)
    discount_me = db.Column(db.Float, nullable=False, default=0)
    ieps = db.Column(db.Float, nullable=False, default=0)
    vat_16_me = db.Column(db.Float, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    ieps_me = db.Column(db.Float, nullable=False, default=0)
    payment_method = db.Column(db.String(250), nullable=False)
    income_tax_withholding_me = db.Column(db.Float, nullable=False, default=0)
    payment_supplement = db.Column(db.Float, nullable=False, default=0)
    s3_url = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(100), nullable=False, default="uploaded")
    file_name = db.Column(db.String(250), nullable=False)
    tax_rate = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Sat {self.id}>"

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
        return f"<Sap {self.id}>"

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class Dof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exchange_rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Dof {self.id}>"

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
        return f"<BankStatement {self.id}>"

    def save(self):
        with app.app_context():
            db.session.add(self)
            db.session.commit()


class FBL3N(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    business_area = db.Column(db.String(250), nullable=True)
    document_type = db.Column(db.String(250), nullable=True)
    document_number = db.Column(db.String(250))
    gl_account = db.Column(db.String(250), nullable=True)
    fiscal_year = db.Column(db.String(10), nullable=True)
    year_month = db.Column(db.String(10), nullable=True)
    document_header_text = db.Column(db.String(255), nullable=True)
    assignment = db.Column(db.String(250), nullable=True)
    profit_center = db.Column(db.String(250), nullable=True)
    cost_center = db.Column(db.String(250), nullable=True)
    text = db.Column(db.String(255), nullable=True)
    reference = db.Column(db.String(250), nullable=True)
    user_name = db.Column(db.String(250), nullable=True)
    transaction_type = db.Column(db.String(250), nullable=True)
    clearing_document = db.Column(db.String(250), nullable=True)
    tax_code = db.Column(db.String(10), nullable=True)
    account_type = db.Column(db.String(10), nullable=True)
    line_item = db.Column(db.BigInteger, nullable=True)
    invoice_reference = db.Column(db.String(250), nullable=True)
    billing_document = db.Column(db.String(250), nullable=True)
    trading_partner = db.Column(db.String(250), nullable=True)
    purchasing_document = db.Column(db.String(250), nullable=True)
    posting_date = db.Column(db.DateTime, nullable=True)
    document_currency = db.Column(db.String(10), nullable=True)
    amount_in_doc_curr = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    eff_exchange_rate = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    amount_in_local_currency = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    document_date = db.Column(db.DateTime, nullable=True)
    clearing_date = db.Column(db.DateTime, nullable=True)
    withholding_tax_amnt = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    withhldg_tax_base_amount = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    local_currency = db.Column(db.String(10), nullable=True)
    entry_date = db.Column(db.DateTime, nullable=True)


class BCSIEPS2440020(FBL3N):
    __tablename__ = "bcs_ieps_2440020"


class BCSIVACobrado2440015(FBL3N):
    __tablename__ = "bcs_iva_cobrado_2440015"


class BCSIVARetenido1250010(FBL3N):
    __tablename__ = "bcs_iva_retenido_1250010"


class BHCIEPS2440020(FBL3N):
    amount_exempt_withholding_taxes = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    general_ledger_account = db.Column(db.String(250), nullable=True)
    __tablename__ = "bhc_ieps_2440020"


class BHCIVATrasladado2440015(FBL3N):
    amount_exempt_withholding_taxes = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    general_ledger_account = db.Column(db.String(250), nullable=True)
    __tablename__ = "bhc_iva_traladado_2440015"


class BHCIVARetenido1250010(FBL3N):
    amount_exempt_withholding_taxes = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    general_ledger_account = db.Column(db.String(250), nullable=True)
    __tablename__ = "bhc_iva_retenido_1250010"


class BHCIVAOTROS(FBL3N):
    amount_exempt_withholding_taxes = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    general_ledger_account = db.Column(db.String(250), nullable=True)
    __tablename__ = "bhc_iva_iva_otros"


class BCSFBL5N(db.Model):
    __tablename__ = "bcs_fbl5n"

    id = db.Column(db.Integer, primary_key=True)
    document_number = db.Column(db.String(250), nullable=True)
    account = db.Column(db.String(250), nullable=True)
    reference = db.Column(db.String(250), nullable=True)
    document_type = db.Column(db.String(250), nullable=True)
    doc_status = db.Column(db.String(250), nullable=True)
    assignment = db.Column(db.String(250), nullable=True)
    text = db.Column(db.String(255), nullable=True)  # Text
    clearing_document = db.Column(db.String(250), nullable=True)
    tax_code = db.Column(db.String(250), nullable=True)  # Tax code
    invoice_reference = db.Column(db.String(250), nullable=True)
    billing_document = db.Column(db.String(250), nullable=True)
    trading_partner = db.Column(db.String(250), nullable=True)
    gl_account = db.Column(db.String(250), nullable=True)
    posting_date = db.Column(db.DateTime, nullable=True)
    document_date = db.Column(db.DateTime, nullable=True)
    clearing_date = db.Column(db.DateTime, nullable=True)
    document_currency = db.Column(db.String(250), nullable=True)
    amount_in_doc_curr = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    eff_exchange_rate = db.Column(db.Numeric(precision=20, scale=5), nullable=True)
    amount_in_local_currency = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    local_currency = db.Column(db.String(250), nullable=True)


class BHCFBL5N(db.Model):
    __tablename__ = "bhc_fbl5n"
    id = db.Column(db.Integer, primary_key=True)
    posting_key = db.Column(db.String(250), nullable=True)
    user_name = db.Column(db.String(250), nullable=True)
    document_number = db.Column(db.String(250), nullable=True)
    account = db.Column(db.String(250), nullable=True)
    reference = db.Column(db.String(250), nullable=True)
    payment_block = db.Column(db.String(250), nullable=True)
    document_type = db.Column(db.String(250), nullable=True)
    cme_indicator = db.Column(db.String(250), nullable=True)
    assignment = db.Column(db.String(250), nullable=True)
    text = db.Column(db.String(255), nullable=True)
    clearing_document = db.Column(db.String(250), nullable=True)
    document_status = db.Column(db.String(250), nullable=True)
    position = db.Column(db.String(250), nullable=True)
    purchase_document = db.Column(db.String(250), nullable=True)
    subsidiary_account = db.Column(db.String(250), nullable=True)
    account_type = db.Column(db.String(250), nullable=True)
    tax_indicator = db.Column(db.String(250), nullable=True)
    invoice_reference = db.Column(db.String(250), nullable=True)
    collective_invoice = db.Column(db.String(250), nullable=True)
    sales_document = db.Column(db.String(250), nullable=True)
    billing_document = db.Column(db.String(250), nullable=True)
    associated_gl_company = db.Column(db.String(250), nullable=True)
    status = db.Column(db.String(250), nullable=True)
    gl_account = db.Column(db.String(250), nullable=True)
    text_id = db.Column(db.String(250), nullable=True)
    posting_date = db.Column(db.DateTime, nullable=True)
    document_date = db.Column(db.DateTime, nullable=True)
    net_due_date = db.Column(db.DateTime, nullable=True)
    clearing_date = db.Column(db.DateTime, nullable=True)
    document_currency = db.Column(db.String(250), nullable=True)
    amount_in_doc_curr = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    eff_exchange_rate = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    amount_in_local_currency = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    local_currency = db.Column(db.String(250), nullable=True)
    withholding_amount = db.Column(db.Numeric(precision=20, scale=2), nullable=True)
    exempt_withholding_amount = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    withholding_base_amount = db.Column(
        db.Numeric(precision=20, scale=2), nullable=True
    )
    value_date = db.Column(db.DateTime, nullable=True)
    entry_date = db.Column(db.DateTime, nullable=True)


class BankPbc(db.Model):
    __tablename__ = "bank_pbc"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_area = db.Column(db.String, nullable=True)
    document_type = db.Column(db.String, nullable=True)
    document_number = db.Column(db.String, nullable=True)
    account = db.Column(db.String, nullable=True)
    fiscal_year = db.Column(db.Integer, nullable=True)
    document_header_text = db.Column(db.String, nullable=True)
    assignment = db.Column(db.String, nullable=True)
    profit_center = db.Column(db.String, nullable=True)
    cost_center = db.Column(db.String, nullable=True)
    text = db.Column(db.String, nullable=True)
    amount_in_doc_curr = db.Column(db.Float, nullable=True)
    eff_exchange_rate = db.Column(db.Float, nullable=True)
    amount_in_local_currency = db.Column(db.Float, nullable=True)
    document_date = db.Column(db.Date, nullable=True)
    clearing_date = db.Column(db.Date, nullable=True)
    withholding_tax_amnt = db.Column(db.Float, nullable=True)
    wtax_exempt_amount = db.Column(db.Float, nullable=True)
    withhldg_tax_base_amount = db.Column(db.Float, nullable=True)
    local_currency = db.Column(db.String, nullable=True)
    entry_date = db.Column(db.Date, nullable=True)
    user_name = db.Column(db.String, nullable=True)  # Added field
    transaction_code = db.Column(db.String, nullable=True)  # Added field
    clearing_document = db.Column(db.String, nullable=True)  # Added field
    tax_code = db.Column(db.String, nullable=True)  # Added field
    account_type = db.Column(db.String, nullable=True)  # Added field
    item = db.Column(db.String, nullable=True)  # Added field
    invoice_reference = db.Column(db.String, nullable=True)  # Added field
    billing_document = db.Column(db.String, nullable=True)  # Added field
    trading_partner = db.Column(db.String, nullable=True)  # Added field
    gl_account = db.Column(db.String, nullable=True)  # Added field
    purchasing_document = db.Column(db.String, nullable=True)  # Added field
    posting_date = db.Column(db.Date, nullable=True)


class BankN8p(db.Model):
    __tablename__ = "bank_n8p"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_area = db.Column(db.Float, nullable=True, default=0)
    document_type = db.Column(db.String, nullable=True)
    document_number = db.Column(db.String, nullable=True)
    account = db.Column(db.String, nullable=True)
    fiscal_year = db.Column(db.Integer, nullable=True)
    document_header_text = db.Column(db.String, nullable=True)
    assignment = db.Column(db.String, nullable=True)
    profit_center = db.Column(db.String, nullable=True)
    cost_center = db.Column(db.String, nullable=True)
    text = db.Column(db.String, nullable=True)
    amount_in_doc_curr = db.Column(db.Float, nullable=True)
    eff_exchange_rate = db.Column(db.Float, nullable=True)
    amount_in_local_currency = db.Column(db.Float, nullable=True)
    document_date = db.Column(db.Date, nullable=True)
    clearing_date = db.Column(db.Date, nullable=True)
    withholding_tax_amnt = db.Column(db.Float, nullable=True)
    wtax_exempt_amount = db.Column(db.Float, nullable=True)
    withhldg_tax_base_amount = db.Column(db.Float, nullable=True)
    local_currency = db.Column(db.String, nullable=True)
    entry_date = db.Column(db.Date, nullable=True)
    user_name = db.Column(db.String, nullable=True)  # Added field
    transaction_code = db.Column(db.String, nullable=True)  # Added field
    clearing_document = db.Column(db.String, nullable=True)  # Added field
    tax_code = db.Column(db.String, nullable=True)  # Added field
    account_type = db.Column(db.String, nullable=True)  # Added field
    item = db.Column(db.String, nullable=True)  # Added field
    invoice_reference = db.Column(db.String, nullable=True)  # Added field
    billing_document = db.Column(db.String, nullable=True)  # Added field
    trading_partner = db.Column(db.String, nullable=True)  # Added field
    gl_account = db.Column(db.String, nullable=True)  # Added field
    purchasing_document = db.Column(db.String, nullable=True)  # Added field
    posting_date = db.Column(db.Date, nullable=True)


def get_conciliations_view_data(
    calendar_filter_start_date=None,
    calendar_filter_end_date=None,
    rfc_selector=None,
    customer_name_selector=None,
    calendar_filter_value_date_start_date=None,
):
    with app.app_context():
        query = "SELECT * FROM conciliations_view WHERE 1=1"
        query_sum = (
            "SELECT "
            "format_price(SUM(subtotal_16)) AS subtotal_iva_16, "
            "format_price(SUM(vat_16)) AS iva_16, "
            "format_price(SUM(vat_0)) AS iva_0, "
            "format_price(SUM(ieps)) AS ieps, "
            "format_price(SUM(total_amount)) AS total_sat "
            "FROM conciliations_view WHERE 1=1"
        )
        query_rfc = "SELECT clearing_payment_policy, SUM(total_amount) from public.conciliations_view WHERE 1=1"
        params = {}

        if calendar_filter_start_date and calendar_filter_end_date:
            sub_query = " AND cfdi_date BETWEEN :calendar_filter_start_date AND :calendar_filter_end_date"
            query += sub_query
            query_sum += sub_query
            query_rfc += sub_query
            params["calendar_filter_start_date"] = calendar_filter_start_date
            params["calendar_filter_end_date"] = calendar_filter_end_date

        if rfc_selector:
            sub_query = " AND rfc = :rfc_selector"
            query += sub_query
            query_sum += sub_query
            query_rfc += sub_query
            params["rfc_selector"] = rfc_selector
        if customer_name_selector:
            sub_query = " AND client_name = :customer_name_selector"
            query += sub_query
            query_sum += sub_query
            query_rfc += sub_query
            params["customer_name_selector"] = customer_name_selector
        if calendar_filter_value_date_start_date:
            sub_query = " AND value_date >= :calendar_filter_value_date_start_date"
            query += sub_query
            query_sum += sub_query
            query_rfc += sub_query
            params["calendar_filter_value_date_start_date"] = (
                calendar_filter_value_date_start_date
            )

        query += " ORDER BY clearing_payment_policy"

        query_rfc += " GROUP BY clearing_payment_policy"

        result = db.session.execute(text(query), params)
        result_sum = db.session.execute(text(query_sum), params)
        result_sum_rfc = db.session.execute(text(query_rfc), params)
        return result, result_sum, result_sum_rfc


def get_rfc_from_conciliations_view():
    with app.app_context():
        query = text("SELECT DISTINCT rfc FROM conciliations_view;")
        result = db.session.execute(query)
        return result


def get_clients_from_conciliations_view():
    with app.app_context():
        query = text("SELECT DISTINCT client_name FROM conciliations_view;")
        result = db.session.execute(query)
        return result


def get_transactions(date):
    results = (
        db.session.query(
            Bank.bank_name,
            Bank.comment,
            Bank.value_date,
            func.sum(Bank.posting_amount).label("total_posting_amount"),
            Bank.ref,
        )
        .filter(Bank.value_date >= date)
        .group_by(
            Bank.bank_name, Bank.value_date, Bank.comment, Bank.posting_amount, Bank.ref
        )
        .all()
    )

    return results
