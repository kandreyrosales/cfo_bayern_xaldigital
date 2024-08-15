import math
import os
import json
import urllib.request, json as js
from collections import defaultdict

import numpy as np
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from io import BytesIO
import re
import pandas as pd
import logging
from app import db, app
from app.utils import aws
from app.models import Bank, Sat, BCSIEPS2440020, BCSIVACobrado2440015, BCSIVARetenido1250010, BHCIEPS2440020, \
    BHCIVATrasladado2440015, BHCIVARetenido1250010, BHCIVAOTROS, BCSFBL5N, BHCFBL5N, BankPbc, BankN8p, Sap, Dof

logger = logging.getLogger(__name__)


class UploadFilesController:
    COLUMN_NAMES_INGRESOS = [
        "version",
        "estado",
        "tipo_comprobante",
        "rfc",
        "nombre",
    ]

    BANK_LIST = [
        ("BBVA_64277", "BBVA 64277"),
        ("Citibanamex_5611843", "Citibanamex 5611843"),
        ("JP_Morgan_6461", "JP Morgan 6461"),
        ("BBVA_EUR_0196006752", "BBVA EUR 0196006752"),
        ("Deutsche_Bank_4500", "Deutsche Bank 4500"),
        ("JP_Morgan_6487", "JP Morgan 6487"),
        ("Citibanamex_5032927", "Citibanamex 5032927"),
        ("BBVA_012180001637146406", "BBVA 012180001637146406"),
        ("BBVA_6026", "BBVA 6026"),
        ("Santander_65-50049596-9", "Santander 65-50049596-9"),
        ("In_House_Bank", "In House Bank"),
        ("HSBC_0156000508", "HSBC 0156000508"),
        ("HSBC_4005129028", "HSBC 4005129028"),
        ("HSBC_4030167084", "HSBC 4030167084"),
        ("Citibanamex_002180026157967545", "Citibanamex 002180026157967545")
    ]

    EXPECTED_COLUMNS_FBL3N = ['Business Area', 'Document Type', 'Document Number', 'G/L Account', 'Fiscal Year',
                              'Year/month',
                              'Document Header Text', 'Assignment', 'Profit Center', 'Cost Center', 'Text', 'Reference',
                              'User name', 'Transaction Type', 'Clearing Document', 'Tax code', 'Account Type',
                              'Line item',
                              'Invoice reference', 'Billing Document', 'Trading Partner', 'Purchasing Document',
                              'Posting Date', 'Document currency', 'Amount in doc. curr.', 'Eff.exchange rate',
                              'Amount in local currency', 'Document Date', 'Clearing date', 'Withholding tax amnt',
                              'Withhldg tax base amount', 'Local Currency', 'Entry Date']

    BHC_EXPECTED_COLUMNS_FBL3N = [
        "División",
        "Clase de documento",
        "Nº documento",
        "Cuenta",
        "Ejercicio",
        "Ejercicio / mes",
        "Texto cab.documento",
        "Asignación",
        "Centro de beneficio",
        "Centro de coste",
        "Texto",
        "Referencia",
        "Nombre del usuario",
        "Código transacción",
        "Doc.compensación",
        "Indicador impuestos",
        "Clase de cuenta",
        "Posición",
        "Referencia a factura",
        "Doc.facturación",
        "Sociedad GL asociada",
        "Cuenta de mayor",
        "Documento compras",
        "Fe.contabilización",
        "Moneda del documento",
        "Importe en moneda doc.",
        "Tp.cambio efectivo",
        "Importe en moneda local",
        "Fecha de documento",
        "Fecha compensación",
        "Importe de retención",
        "ImpteExentRetImptos",
        "Importe base de retención",
        "Moneda local",
        "Fecha de entrada"
    ]

    BHC_EXPECTED_COLUMNS_FBL5N = [
        "Clave contabiliz.",
        "Nombre del usuario",
        "Nº documento",
        "Cuenta",
        "Referencia",
        "Bloqueo de pago",
        "Clase de documento",
        "Indicador CME",
        "Asignación",
        "Texto",
        "Doc.compensación",
        "Status de documento",
        "Posición",
        "Documento compras",
        "Posición",
        "Cta.subsidiaria",
        "Clase de cuenta",
        "Indicador impuestos",
        "Posición",
        "Referencia a factura",
        "Factura colectiva",
        "Documento de ventas",
        "Doc.facturación",
        "Sociedad GL asociada",
        "Status",
        "Cuenta de mayor",
        "ID texto",
        "Fe.contabilización",
        "Fecha de documento",
        "Vencimiento neto",
        "Fecha compensación",
        "Moneda del documento",
        "Importe en moneda doc.",
        "Tp.cambio efectivo",
        "Importe en moneda local",
        "Moneda local",
        "Importe de retención",
        "ImpteExentRetImptos",
        "Importe base de retención",
        "Fecha valor",
        "Fecha de entrada"
    ]

    BCS_EXPECTED_COLUMNS_FBL5N = [
        "Document Number",
        "Account",
        "Reference",
        "Document Type",
        "Doc.status",
        "Assignment",
        "Text",
        "Clearing Document",
        "Tax code",
        "Invoice reference",
        "Billing Document",
        "Trading Partner",
        "G/L Account",
        "Posting Date",
        "Document Date",
        "Clearing date",
        "Document currency",
        "Amount in doc. curr.",
        "Eff.exchange rate",
        "Amount in local currency",
        "Local Currency"
    ]

    BANK_PBC = [
        "Business Area",
        "Document Type",
        "Document Number",
        "Account",
        "Fiscal Year",
        "Document Header Text",
        "Assignment",
        "Profit Center",
        "Cost Center",
        "Text",
        "Reference",
        "User name",
        "Transaction Code",
        "Clearing Document",
        "Tax code",
        "Account Type",
        "Item",
        "Invoice reference",
        "Billing Document",
        "Trading partner",
        "G/L Account",
        "Purchasing Document",
        "Posting Date",
        "Document currency",
        "Amount in doc. curr.",
        "Eff.exchange rate",
        "Amount in local currency",
        "Document Date",
        "Clearing date",
        "Withholding tax amnt",
        "W/tax exempt amount",
        "Withhldg tax base amount",
        "Local Currency",
        "Entry Date"
    ]

    BANK_N8P = [
        "Business Area",
        "Document Type",
        "Document Number",
        "Account",
        "Fiscal Year",
        "Document Header Text",
        "Assignment",
        "Profit Center",
        "Cost Center",
        "Text",
        "Reference",
        "User Name",
        "Transaction Code",
        "Clearing Document",
        "Tax Code",
        "Account Type",
        "Item",
        "Invoice reference",
        "Billing Document",
        "Trading partner",
        "G/L Account",
        "Purchasing Document",
        "Posting Date",
        "Document currency",
        "Amount in doc. curr.",
        "Eff.exchange rate",
        "Amount in local currency",
        "Document Date",
        "Clearing date",
        "Withholding tax amnt",
        "W/tax exempt amount",
        "Withhldg tax base amount",
        "Local Currency",
        "Entry Date"
    ]

    @classmethod
    def process_file(cls, file, extension):
        pass

    @classmethod
    def load_file(cls, file, extension):
        try:
            data = None

            if extension == "xml":
                data = ET.parse(file)

            if extension == "xls" or extension == "xlsx":
                data = pd.read_excel(file)

            if extension == "pdf":
                data = file.read()
            return data
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            return None

    @classmethod
    def valid_file(cls, file, extension):
        data = cls.load_file(file, extension)

        if extension == "xls" or extension == "xlsx":
            columns = data.columns.tolist()
            columns_lowercase_strings = [s.lower() for s in columns]
            if columns_lowercase_strings == cls.COLUMN_NAMES_INGRESOS:
                return True, "", data
            else:
                return False, "Las columnas no corresponden con las esperadas", None

        if extension == 'xml':
            print(data)
            return True, "", data

        if extension == 'pdf':
            print(data)
            return True, "", data

    @classmethod
    def upload_sat_info(cls, files):
        with app.app_context():
            for file in files.getlist("sat"):
                try:
                    today = datetime.now()
                    object_name = f"{today.strftime('%d-%m-%Y')}/{file.filename}"
                    file_content = file.read()
                    cls.process_xml_file(file_content, "", object_name)
                except Exception as e:
                    logger.warning(str(e))

    @classmethod
    def upload_ban_info(cls, files, dof_value):
        try:
            today = datetime.now()
            url = os.getenv("api-getway-service",
                            "https://vt26v7zc2d.execute-api.us-east-1.amazonaws.com/prod/UploadFile")
            with app.app_context():
                object_name = f"{today.strftime('%d-%m-%Y')}/{files['banks'].filename}"

                bank = Bank.query.filter_by(file_name=object_name).first()
                file_content = files['banks'].read()
                files['banks'].seek(0)

                if not bank:
                    cls.upload_to_s3(files['banks'], aws.S3_BUCKET_NAME, object_name)

                    s3_url = (f"https://{aws.S3_BUCKET_NAME}.s3.amazonaws.com/{today.strftime('%d-%m-%Y')}/"
                              f"{files['banks'].filename}")

                    headers = {
                        'file-name': 'Cobradoras_Agosto',
                        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    }

                    response = requests.put(url, headers=headers, data=file_content)

                    json_response = json.loads(response.text)
                    logger.warning(json_response)
                    default_value = ""

                    '''
                    Bulk insert sqlalquemist
                    '''

                    for url in json_response.get('urls'):
                        file_name_with_extension = os.path.basename(url)
                        file_name = os.path.splitext(file_name_with_extension)[0]
                        with urllib.request.urlopen(url.replace(" ", "%20")) as url_json:
                            data = js.load(url_json)
                            for transaction in data[file_name]["Transactions"]:
                                for key, value in transaction.items():
                                    if isinstance(value, float) and math.isnan(value):  # Check if float and NaN
                                        transaction[key] = default_value
                                    elif isinstance(value, str) and value.lower() == 'nan':  # Check if string 'nan'
                                        transaction[key] = default_value
                                    elif value is np.nan:  # General check for np.nan
                                        transaction[key] = default_value

                                new_bank = Bank(
                                    bank_name=file_name,
                                    book_date=transaction.get('Book Date'),
                                    value_date=transaction.get('Value Date'),
                                    posting_amount=transaction.get('Posting Amount'),
                                    payment_method=transaction.get('Payment Method'),
                                    ref=transaction.get('Ref'),
                                    addref=transaction.get('Addref'),
                                    comment=transaction.get('Reason of transfer'),
                                    payer=transaction.get('Payer'),
                                    posting_text=transaction.get('Posting Text'),
                                    s3_url=s3_url,
                                    file_name=object_name
                                )
                                new_bank.save()

                else:
                    logger.warning(f"{object_name} the data bank already register")

                dof = Dof(exchange_rate=dof_value)
                dof.save()

        except Exception as e:
            logger.warning(str(e))

    @classmethod
    def upload_sap_info(cls, files):
        try:
            today = datetime.now()
            for file in files:
                with app.app_context():
                    object_name = f"{today.strftime('%d-%m-%Y')}/{files[file].filename}"
                    extension = files[file].filename.split(".")[-1].lower()
                    file_content = files[file].read()
                    files[file].seek(0)

                    cls.upload_to_s3(file_content, aws.S3_BUCKET_NAME, object_name)

                    s3_url = (f"https://{aws.S3_BUCKET_NAME}.s3.amazonaws.com/"
                              f"{today.strftime('%d-%m-%Y')}/{files[file].filename}")

                    if extension == "xlsx":
                        cls.process_xlsx_file(file_content, file, object_name)
        except Exception as e:
            logger.warning(str(e))

    @classmethod
    def process_xml_file(cls, file_content, s3_url, object_name):
        sat = Sat.query.filter_by(file_name=object_name).first()
        if not sat:
            root = ET.fromstring(file_content)
            vat_16 = 0
            ieps = 0
            vat_0 = 0
            subtotal_16 = 0
            tax_rate = ""

            descriptions = ' * '.join(
                map(lambda concepto: concepto.get('Descripcion', ''),
                    root.findall('.//cfdi:Concepto', {'cfdi': 'http://www.sat.gob.mx/cfd/3'})))

            receptor = root.find('cfdi:Receptor', {'cfdi': 'http://www.sat.gob.mx/cfd/3'})

            taxes = root.findall('.//cfdi:Traslado', {'cfdi': 'http://www.sat.gob.mx/cfd/3'})

            for tax in taxes:
                print("---- Tax Element ----")
                for child in tax:
                    print(f"Tag: {child.tag}, Attribute: {child.attrib}, Text: {child.text}")

                print("Attributes of Tax Element:", tax.attrib)
                print("-----------------------\n")

            '''
            
            list(map(lambda traslado: total_taxes[traslado.attrib['Impuesto']].update(
                { 'Base': total_taxes[traslado.attrib['Impuesto']]['Base'] + float(traslado.attrib.get('Base', '0')),
                  'Importe': total_taxes[traslado.attrib['Impuesto']]['Importe'] + float(traslado.attrib.get('Importe', '0')),
                  'TasaOCuota': round(total_taxes[traslado.attrib['Impuesto']]['TasaOCuota'] + float(traslado.attrib.get('TasaOCuota', '0')), 6),
                }), 

            # Convert defaultdict to a regular dictionary if needed
            total_taxes = dict(total_taxes)

            if total_taxes.get('002'):
                subtotal_16 = total_taxes.get('002').get('Base')
            if total_taxes.get('003'):
                vat_0 = total_taxes.get('003').get('Base')

            logger.warning(total_taxes)

            taxes = root.find('.//cfdi:Impuestos', {'cfdi': 'http://www.sat.gob.mx/cfd/3'})
            traslados = taxes.find('.//cfdi:Traslados', {'cfdi': 'http://www.sat.gob.mx/cfd/3'})

            taxes_elements = traslados.findall('.//cfdi:Traslado',
                                               {'cfdi': 'http://www.sat.gob.mx/cfd/3'})

            for tax in taxes_elements:
                if tax.get('Impuesto') == '002' and float(tax.get('Importe')) > 0.0:
                    vat_16 = tax.get('Importe')
                    tax_rate += "16%"
                if tax.get('Impuesto') == '003' and float(tax.get('Importe')) > 0.0:
                    ieps = tax.get('Importe')
                    tax_rate += " 0%"

            sat = Sat(
                cfdi_date=root.get('Fecha'),
                cfdi_use=receptor.get('UsoCFDI') if receptor is not None else "",
                rfc=receptor.get('Rfc') if receptor is not None else "",
                client_name=receptor.get('Nombre') if receptor is not None else "",
                receipt_number=root.get('Folio'),
                fiscal_uuid=root.find('.//tfd:TimbreFiscalDigital',
                                      {
                                          'cfdi': 'http://www.sat.gob.mx/cfd/4',
                                          'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
                                      }
                                      ).get('UUID'),
                product_or_service=descriptions,
                currency=root.get('Moneda'),
                total_amount=root.get('Total'),
                payment_method=root.get('MetodoPago'),
                s3_url=s3_url,
                state="uploaded",
                ieps=ieps,
                vat_16=vat_16,
                file_name=object_name,
                vat_0=vat_0,
                subtotal_16=subtotal_16 if float(vat_16) > 0.0 else 0,
                tax_rate=tax_rate
            )
            sat.save()
            '''
        else:
            logger.warning(f"{object_name} the data sat already register")

    @classmethod
    def process_xlsx_file(cls, file_content, file_key, object_name):
        try:
            file_bytes = BytesIO(file_content)
            xls = pd.ExcelFile(file_bytes)

            if file_key == "bcs_fbl3n":
                df_bcs_ieps_2440020 = pd.read_excel(xls, 'IEPS 2440020')
                df_bcs_iva_cobrado_2440015 = pd.read_excel(xls, 'IVA cobrado 2440015')
                df_bcs_iva_retenido_1250010 = pd.read_excel(xls, 'IVA Retenido 1250010')

                if cls.validate_columns(df_bcs_ieps_2440020, cls.EXPECTED_COLUMNS_FBL3N):
                    df_bcs_ieps_2440020 = cls.clean_data(df_bcs_ieps_2440020)
                    df_bcs_ieps_2440020 = df_bcs_ieps_2440020.drop(
                        df_bcs_ieps_2440020.index[-1])
                    cls.save_fbl3n_to_db(df_bcs_ieps_2440020, BCSIEPS2440020)

                if cls.validate_columns(df_bcs_iva_cobrado_2440015, cls.EXPECTED_COLUMNS_FBL3N):
                    df_bcs_iva_cobrado_2440015 = cls.clean_data(df_bcs_iva_cobrado_2440015)
                    df_bcs_iva_cobrado_2440015 = df_bcs_iva_cobrado_2440015.drop(
                        df_bcs_iva_cobrado_2440015.index[-1])
                    cls.save_fbl3n_to_db(df_bcs_iva_cobrado_2440015, BCSIVACobrado2440015)

                if cls.validate_columns(df_bcs_iva_retenido_1250010, cls.EXPECTED_COLUMNS_FBL3N):
                    df_bcs_iva_retenido_1250010 = cls.clean_data(df_bcs_iva_retenido_1250010)
                    df_bcs_iva_retenido_1250010 = df_bcs_iva_retenido_1250010.drop(
                        df_bcs_iva_retenido_1250010.index[-1])
                    cls.save_fbl3n_to_db(df_bcs_iva_retenido_1250010, BCSIVARetenido1250010)

            elif file_key == "bhc_fbl3n":
                df_bhs_ieps_2440020 = pd.read_excel(xls, 'IEPS 2440020')
                df_bhs_iva_trasladado_2440015 = pd.read_excel(xls, 'IVA Trasladado 2440015')
                df_bhs_iva_retenido_1250010 = pd.read_excel(xls, 'IVA Retenido 1250010')
                df_bhs_iva_otros = pd.read_excel(xls, 'IVA Otros ingresos')

                if cls.validate_columns(df_bhs_ieps_2440020, cls.BHC_EXPECTED_COLUMNS_FBL3N):
                    df_bhs_ieps_2440020 = cls.clean_data(df_bhs_ieps_2440020)
                    df_bhs_ieps_2440020 = df_bhs_ieps_2440020.drop(
                        df_bhs_ieps_2440020.index[-1])
                    cls.save_bhc_fbl3n_to_db(df_bhs_ieps_2440020, BHCIEPS2440020)

                if cls.validate_columns(df_bhs_iva_trasladado_2440015, cls.BHC_EXPECTED_COLUMNS_FBL3N):
                    df_bhs_iva_trasladado_2440015 = cls.clean_data(df_bhs_iva_trasladado_2440015)
                    df_bhs_iva_trasladado_2440015 = df_bhs_iva_trasladado_2440015.drop(
                        df_bhs_iva_trasladado_2440015.index[-1])
                    cls.save_bhc_fbl3n_to_db(df_bhs_iva_trasladado_2440015, BHCIVATrasladado2440015)

                if cls.validate_columns(df_bhs_iva_retenido_1250010, cls.BHC_EXPECTED_COLUMNS_FBL3N):
                    df_bhs_iva_retenido_1250010 = cls.clean_data(df_bhs_iva_retenido_1250010)
                    df_bhs_iva_retenido_1250010 = df_bhs_iva_retenido_1250010.drop(
                        df_bhs_iva_retenido_1250010.index[-1])
                    cls.save_bhc_fbl3n_to_db(df_bhs_iva_retenido_1250010, BHCIVARetenido1250010)

                if cls.validate_columns(df_bhs_iva_otros, cls.BHC_EXPECTED_COLUMNS_FBL3N):
                    df_bhs_iva_otros = cls.clean_data(df_bhs_iva_otros)
                    df_bhs_iva_otros = df_bhs_iva_otros.drop(
                        df_bhs_iva_otros.index[-1])
                    cls.save_bhc_fbl3n_to_db(df_bhs_iva_otros, BHCIVAOTROS)

            elif file_key == "bcs_fbl5n":
                df_bcs = pd.read_excel(xls, "Sheet1")
                if cls.validate_columns(df_bcs, cls.BCS_EXPECTED_COLUMNS_FBL5N):
                    df_bcs = cls.clean_data(df_bcs)
                    cls.save_bcs_fbl5n_to_db(df_bcs, BCSFBL5N)

            elif file_key == "bhc_fbl5n":
                df_bhc = pd.read_excel(xls, 'Sheet1')
                if cls.validate_columns(df_bhc, cls.BHC_EXPECTED_COLUMNS_FBL5N):
                    df_bhc = cls.clean_data(df_bhc)
                    df_bhc = df_bhc.drop(
                        df_bhc.index[-3:])
                    cls.save_bhc_fbl5n_to_db(df_bhc, BHCFBL5N)

            elif file_key == "banks":
                sheets_to_process = cls.get_sheets_banks(xls.sheet_names)
                for sheet in sheets_to_process:
                    model_name = sheet[-3:]
                    model = None
                    array_to_validate = []

                    if model_name == "PBC":
                        model = BankPbc
                        array_to_validate = cls.BANK_PBC

                    if model_name == "N8P":
                        model = BankN8p
                        array_to_validate = cls.BANK_N8P

                    if model is not None:
                        df_bank = pd.read_excel(xls, sheet)
                        if cls.validate_columns(df_bank, array_to_validate):
                            df_bank = cls.clean_data(df_bank)
                            cls.save_bank_pbc_n8p(df_bank, model)
        except Exception as e:
            logger.warning(f"the process failed in file {file_key} {str(e)}")

    @classmethod
    def get_sheets_banks(cls, sheets_list):
        pattern = re.compile(r'^[a-z]{2,3}-[a-z]{3} [A-Z0-9]{3}$')
        sheets = []
        for sheet in sheets_list:
            if pattern.match(sheet):
                sheets.append(sheet)

        return sheets

    @classmethod
    def validate_columns(cls, df, expected_columns):
        return all(column in df.columns for column in expected_columns)

    @classmethod
    def convert_to_datetime(cls, value):
        if pd.notnull(value):
            return pd.to_datetime(value)
        return None

    @classmethod
    def clean_data(cls, df):
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace("'", "", regex=False)
        return df

    @classmethod
    def save_fbl3n_to_db(cls, df, model):
        for _, row in df.iterrows():
            try:
                record = model(
                    business_area=str(row.get("Business Area")) if not pd.isna(row.get("Business Area")) else None,
                    document_type=row.get('Document Type'),
                    document_number=str(int(row.get('Document Number'))),
                    gl_account=str(int(row.get('G/L Account'))) if not pd.isna(row.get("G/L Account")) else None,
                    fiscal_year=str(int(row.get('Fiscal Year'))),
                    year_month=str(row.get('Year/month')),
                    document_header_text=str(row.get('Document Header Text')) if not pd.isna(
                        row.get('Document Header Text')) else None,
                    assignment=str(row.get('Assignment')) if not pd.isna(row.get('Assignment')) else None,
                    profit_center=row.get('Profit Center'),
                    cost_center=str(row.get('Cost Center')) if not pd.isna(row.get('Cost Center')) else None,
                    text=str(row.get('Text')) if not pd.isna(row.get('Text')) else None,
                    reference=str(row.get('Reference')) if not pd.isna(row.get('Reference')) else None,
                    user_name=row.get('User Name'),
                    transaction_type=str(row.get('Transaction Type')) if not pd.isna(
                        row.get('Transaction Type')) else None,
                    clearing_document=str(int(row.get('Clearing Document'))) if not pd.isna(
                        row.get('Clearing Document')) else None,
                    tax_code=row.get('Tax Code'),
                    account_type=row.get('Account Type'),
                    line_item=row.get('Line Item'),
                    invoice_reference=row.get('Invoice Reference'),
                    billing_document=str(row.get('Billing Document')) if not pd.isna(
                        row.get('Billing Document')) else None,
                    trading_partner=str(int(row.get('Trading Partner'))) if not pd.isna(
                        row.get('Trading Partner')) else None,
                    purchasing_document=str(row.get('Purchasing Document')) if not pd.isna(
                        row.get('Purchasing Document')) else None,
                    posting_date=cls.convert_to_datetime(row.get('Posting Date')),
                    document_currency=row.get('Document Currency'),
                    amount_in_doc_curr=row.get('Amount in doc. curr.'),
                    eff_exchange_rate=str(row.get('Eff.exchange rate').replace(",", ".")),
                    amount_in_local_currency=row.get('Amount in local currency'),
                    document_date=cls.convert_to_datetime(row.get('Document Date')),
                    clearing_date=cls.convert_to_datetime(row.get('Clearing Date')),
                    withholding_tax_amnt=float(row.get('Withholding tax amnt')),
                    withhldg_tax_base_amount=float(row.get('Withhldg tax base amount')),
                    local_currency=row.get('Local Currency'),
                    entry_date=cls.convert_to_datetime(row.get('Entry Date'))
                )
                db.session.add(record)
            except Exception as e:
                logger.warning(str(e))
        db.session.commit()

    @classmethod
    def save_bhc_fbl3n_to_db(cls, df, model):
        for _, row in df.iterrows():
            try:
                eff_exchange_rate = row.get('Tp.cambio efectivo')
                if pd.isna(eff_exchange_rate):
                    eff_exchange_rate = None
                elif isinstance(eff_exchange_rate, str):
                    eff_exchange_rate = eff_exchange_rate.replace(",", ".")
                    try:
                        eff_exchange_rate = float(eff_exchange_rate)
                    except ValueError:
                        eff_exchange_rate = None

                record = model(
                    business_area=str(row.get('División')) if not pd.isna(row.get("División")) else None,
                    document_type=str(row.get('Clase de documento')),
                    document_number=str(int(row.get('Nº documento'))),
                    gl_account=str(int(row.get('Cuenta'))),
                    fiscal_year=str(int(row.get('Ejercicio'))),
                    year_month=str(row.get('Ejercicio / mes')),
                    document_header_text=str(row.get('Texto cab.documento')) if not pd.isna(
                        row.get('Texto cab.documento')) else None,
                    assignment=str(row.get('Asignación')) if not pd.isna(row.get('Asignación')) else None,
                    profit_center=str(row.get('Centro de beneficio')) if not pd.isna(
                        row.get('Centro de beneficio')) else None,
                    cost_center=str(row.get('Centro de coste')) if not pd.isna(row.get('Centro de coste')) else None,
                    text=str(row.get('Texto')) if not pd.isna(row.get('Texto')) else None,
                    reference=str(row.get('Referencia')) if not pd.isna(row.get('Referencia')) else None,
                    user_name=str(row.get('Nombre del usuario', '')),
                    transaction_type=str(row.get('Código transacción')),
                    clearing_document=str(int(row.get('Doc.compensación'))) if not pd.isna(
                        row.get("Doc.compensación")) else None,
                    tax_code=str(row.get('Indicador impuestos')) if not pd.isna(
                        row.get('Indicador impuestos')) else None,
                    account_type=str(row.get('Clase de cuenta', '')),
                    line_item=int(row.get('Posición', 0) if not pd.isna(row.get('Posición')) else 0),
                    invoice_reference=str(int(row.get('Referencia a factura'))),
                    billing_document=str(row.get('Doc.facturación')) if not pd.isna(
                        row.get('Doc.facturación')) else None,
                    trading_partner=str(row.get('Sociedad GL asociada')) if not pd.isna(
                        row.get('Sociedad GL asociada')) else None,
                    purchasing_document=str(row.get('Documento compras')) if not pd.isna(
                        row.get('Documento compras')) else None,
                    posting_date=cls.convert_to_datetime(row.get('Fe.contabilización')),
                    document_currency=str(row.get('Moneda del documento', '')),
                    amount_in_doc_curr=row.get('Importe en moneda doc.'),
                    eff_exchange_rate=eff_exchange_rate,
                    amount_in_local_currency=row.get('Importe en moneda local'),
                    document_date=cls.convert_to_datetime(row.get('Fecha de documento')),
                    clearing_date=cls.convert_to_datetime(row.get('Fecha compensación')),
                    withholding_tax_amnt=float(row.get('Importe de retención')),
                    amount_exempt_withholding_taxes=float(row.get('ImpteExentRetImptos')),
                    general_ledger_account=str(row.get('Cuenta de mayo', '')),
                    withhldg_tax_base_amount=float(row.get('Importe base de retención')),
                    local_currency=str(row.get('Moneda local', '')),
                    entry_date=cls.convert_to_datetime(row.get('Fecha de entrada'))
                )
                db.session.add(record)

            except Exception as e:
                logger.warning(f"{str(e)}  {model}")
        db.session.commit()

    @classmethod
    def save_bcs_fbl5n_to_db(cls, df, model):
        for _, row in df.iterrows():
            try:
                record = model(
                    document_number=str(int(row.get("Document Number"))) if not pd.isna(
                        row.get("Document Number")) else None,
                    account=str(int(row.get("Account"))) if not pd.isna(row.get("Account")) else None,
                    reference=str(row.get("Reference")) if not pd.isna(row.get("Reference")) else None,
                    document_type=str(row.get("Document Type")) if not pd.isna(row.get("Document Type")) else None,
                    doc_status=str(row.get("Doc.status")) if not pd.isna(row.get("Doc.status")) else None,
                    assignment=str(row.get("Assignment")) if not pd.isna(row.get("Assignment")) else None,
                    text=str(row.get("Text")) if not pd.isna(row.get("Text")) else None,
                    clearing_document=str(int(row.get("Clearing Document"))) if not pd.isna(
                        row.get("Clearing Document")) else None,
                    tax_code=str(row.get("Tax code")) if not pd.isna(row.get("Tax code")) else None,
                    invoice_reference=str(row.get("Invoice reference")) if not pd.isna(
                        row.get("Invoice reference")) else None,
                    billing_document=str(int(row.get("Billing Document"))) if not pd.isna(
                        row.get("Billing Document")) else None,
                    trading_partner=str(row.get("Trading Partner")) if not pd.isna(
                        row.get("Trading Partner")) else None,
                    gl_account=str(int(row.get("G/L Account"))) if not pd.isna(row.get("G/L Account")) else None,
                    posting_date=cls.convert_to_datetime(row.get("Posting Date")),
                    document_date=cls.convert_to_datetime(row.get("Document Date")),
                    clearing_date=cls.convert_to_datetime(row.get("Clearing date")),
                    document_currency=row.get("Document currency"),
                    amount_in_doc_curr=row.get("Amount in doc. curr."),
                    eff_exchange_rate=float(str(row.get('Eff.exchange rate')).replace(",", ".")) if not pd.isna(
                        row.get('Eff.exchange rate')) else None,
                    amount_in_local_currency=row.get("Amount in local currency"),
                    local_currency=str(row.get("Local Currency"))
                )
                db.session.add(record)
            except Exception as e:
                logger.warning(str(e))
        db.session.commit()

    @classmethod
    def save_bhc_fbl5n_to_db(cls, df, model):
        for _, row in df.iterrows():
            try:
                record = model(
                    posting_key=int(row.get("Clave contabiliz.")),
                    user_name=str(row.get("Nombre del usuario")),
                    document_number=str(int(row.get("Nº documento"))),
                    account=str(int(row.get("Cuenta"))),
                    reference=str(row.get("Referencia")) if not pd.isna(row.get("Referencia")) else None,
                    payment_block=str(row.get("Bloqueo de pago")) if not pd.isna(row.get("Bloqueo de pago")) else None,
                    document_type=str(row.get("Clase de documento")),
                    cme_indicator=str(row.get("Indicador CME")) if not pd.isna(row.get("Indicador CME")) else None,
                    assignment=str(row.get("Asignación")),
                    text=str(row.get("Texto")) if not pd.isna(row.get("Texto")) else None,
                    clearing_document=str(int(row.get("Doc.compensación"))),
                    document_status=str(row.get("Status de documento")) if not pd.isna(
                        row.get("Status de documento")) else None,
                    position=str(int(row.get("Posición"))),
                    purchase_document=str(row.get("Documento compras")) if not pd.isna(
                        row.get("Documento compras")) else None,
                    subsidiary_account=str(row.get("Cta.subsidiaria")) if not pd.isna(
                        row.get("Cta.subsidiaria")) else None,
                    account_type=str(row.get("Clase de cuenta")),
                    tax_indicator=str(row.get("Indicador impuestos")) if not pd.isna(
                        row.get("Indicador impuestos")) else None,
                    invoice_reference=str(row.get("Referencia a factura")),
                    collective_invoice=row.get("Factura colectiva"),
                    sales_document=str(row.get("Documento de ventas")) if not pd.isna(
                        row.get("Documento de ventas")) else None,
                    billing_document=str(row.get("Doc.facturación")) if not pd.isna(
                        row.get("Doc.facturación")) else None,
                    associated_gl_company=str(row.get("Sociedad GL asociada")) if not pd.isna(
                        row.get("Sociedad GL asociada")) else None,
                    status=str(row.get("Status")) if not pd.isna(row.get("Status")) else None,
                    gl_account=str(int(row.get("Cuenta de mayor"))),
                    text_id=str(row.get("ID texto")) if not pd.isna(row.get("ID texto")) else None,
                    posting_date=cls.convert_to_datetime(row.get("Fe.contabilización")),
                    document_date=cls.convert_to_datetime(row.get("Fecha de documento")),
                    net_due_date=cls.convert_to_datetime(row.get("Vencimiento neto")),
                    clearing_date=cls.convert_to_datetime(row.get("Fecha compensación")),
                    document_currency=row.get("Moneda del documento"),
                    amount_in_doc_curr=row.get("Importe en moneda doc."),
                    eff_exchange_rate=float(str(row.get("Tp.cambio efectivo")).replace(",", ".")),
                    amount_in_local_currency=row.get("Importe en moneda local"),
                    local_currency=str(row.get("Moneda local")),
                    withholding_amount=row.get("Importe de retención"),
                    exempt_withholding_amount=row.get("ImpteExentRetImptos"),
                    withholding_base_amount=row.get("Importe base de retención"),
                    value_date=cls.convert_to_datetime(row.get("Fecha valor")),
                    entry_date=cls.convert_to_datetime(row.get("Fecha de entrada"))
                )
                db.session.add(record)
            except Exception as e:
                logger.warning(str(e))
        db.session.commit()

    @classmethod
    def save_bank_pbc_n8p(cls, df, model):
        for _, row in df.iterrows():
            try:
                if "Cleared/open" not in str(row.get("Business Area")):
                    # Convert Eff.exchange rate if it's a valid number
                    eff_exchange_rate = row.get("Eff.exchange rate")
                    if pd.isna(eff_exchange_rate):
                        eff_exchange_rate = None
                    elif isinstance(eff_exchange_rate, str):
                        eff_exchange_rate = eff_exchange_rate.replace(",", ".")
                        try:
                            eff_exchange_rate = float(eff_exchange_rate)
                        except ValueError:
                            eff_exchange_rate = None

                    record = model(
                        business_area=str(row.get("Business Area")) if not pd.isna(row.get("Business Area")) else None,
                        document_type=str(row.get("Document Type")) if not pd.isna(row.get("Document Type")) else None,
                        document_number=str(int(row.get("Document Number"))) if not pd.isna(
                            row.get("Document Number")) else None,
                        account=str(int(row.get("Account"))) if not pd.isna(row.get("Account")) else None,
                        fiscal_year=row.get("Fiscal Year") if not pd.isna(row.get("Fiscal Year")) else None,
                        document_header_text=str(row.get("Document Header Text")) if not pd.isna(
                            row.get("Document Header Text")) else None,
                        assignment=str(row.get("Assignment")) if not pd.isna(row.get("Assignment")) else None,
                        profit_center=str(row.get("Profit Center")) if not pd.isna(row.get("Profit Center")) else None,
                        cost_center=row.get("Cost Center") if not pd.isna(row.get("Cost Center")) else None,
                        text=str(row.get("Text")) if not pd.isna(row.get("Text")) else None,
                        amount_in_doc_curr=row.get("Amount in doc. curr.") if not pd.isna(
                            row.get("Amount in doc. curr.")) else None,
                        eff_exchange_rate=eff_exchange_rate,
                        amount_in_local_currency=row.get("Amount in local currency") if not pd.isna(
                            row.get("Amount in local currency")) else None,
                        document_date=cls.convert_to_datetime(row.get("Document Date")),
                        clearing_date=cls.convert_to_datetime(row.get("Clearing date")),
                        withholding_tax_amnt=row.get("Withholding tax amnt") if not pd.isna(
                            row.get("Withholding tax amnt")) else None,
                        wtax_exempt_amount=row.get("W/tax exempt amount") if not pd.isna(
                            row.get("W/tax exempt amount")) else None,
                        withhldg_tax_base_amount=row.get("Withhldg tax base amount") if not pd.isna(
                            row.get("Withhldg tax base amount")) else None,
                        local_currency=str(row.get("Local Currency")) if not pd.isna(
                            row.get("Local Currency")) else None,
                        entry_date=cls.convert_to_datetime(row.get("Entry Date")),
                        user_name=str(row.get("User Name")) or "",
                        transaction_code=str(row.get("Transaction Code")) if not pd.isna(
                            row.get("Transaction Code")) else None,
                        clearing_document=row.get("Clearing Document") if not pd.isna(
                            row.get("Clearing Document")) else None,
                        tax_code=str(row.get("Tax Code")) if not pd.isna(row.get("Tax Code")) else None,
                        account_type=str(row.get("Account Type")) if not pd.isna(row.get("Account Type")) else None,
                        item=str(int(row.get("Item"))) if not pd.isna(row.get("Item")) else None,
                        invoice_reference=str(int(row.get("Invoice reference"))) if not pd.isna(
                            row.get("Invoice reference")) else None,
                        billing_document=str(int(row.get("Billing Document"))) if not pd.isna(
                            row.get("Billing Document")) else None,
                        trading_partner=row.get("Trading Partner") if not pd.isna(row.get("Trading Partner")) else None,
                        gl_account=row.get("G/L Account") if not pd.isna(row.get("G/L Account")) else None,
                        purchasing_document=row.get("Purchasing Document") if not pd.isna(
                            row.get("Purchasing Document")) else None,
                        posting_date=cls.convert_to_datetime(row.get("Posting Date"))
                    )
                    db.session.add(record)
            except Exception as e:
                logger.warning(str(e))
        db.session.commit()

    @classmethod
    def upload_to_s3(cls, file, bucket_name, object_name):
        try:
            s3_client = aws.upload_to_s3()
            s3_client.upload_fileobj(file, bucket_name, object_name)
        except Exception as e:
            return str(e)
        return 'Upload successful'


'''
XML, PDF y XLS y XLSX


 stream = BytesIO(archivo.read())
    workbook = load_workbook(stream)
    cfdi_ingresos_sheet = workbook.worksheets[0]
    cfdi_complemento_sheet = workbook.worksheets[1]
    iva_cobrado_sheet = workbook.worksheets[2]
    analisis_iva_cobrado_sheet = workbook.worksheets[3]
    # Prepare bulk insert query template
    try:
        column_names_ingresos = [
            "version",
            "estado",
            "tipo_comprobante",
            "rfc",
            "nombre",
            "fecha_emision",
            "folio_interno",
            "uuid_fiscal",
            "producto_servicio_conforme_sat",
            "concepto_del_cfdi",
            "moneda",
            "metodo_de_pago",
            "subtotal",
            "descuento",
            "iva",
            "ieps",
            "isr_retenido",
            "iva_retenido",
            "total_cfdi",
            "tipo_de_relacion",
            "cfdi_relacionado",]
        column_names_str_ingresos = ", ".join(column_names_ingresos)
        column_names_complemento = [
            "estado_sat",
            "version_pagos",
            "uuid_complemento",
            "fecha_timbrado",
            "fecha_emision",
            "folio",
            "serie",
            "subtotal",
            "moneda",
            "total",
            "lugar_expedicion",
            "rfc_emisor",
            "nombre_emisor",
            "rfc_receptor",
            "nombre_receptor",
            "uso_cfdi",
            "clave_prod_serv",
            "descripcion",
            "fecha_de_pago",
            "forma_de_pago",
            "moneda_p",
            "tipo_cambio_p",
            "monto",
            "numero_operacion",
            "importe_pagado_mo",
            "id_documento",
            "serie_dr",
            "folio_dr",
            "moneda_dr",
            "num_parcialidad",
            "imp_saldo_ant",
            "importe_pagado",
            "imp_saldo_insoluto"
        ]
        column_names_str_complemento = ", ".join(column_names_complemento)

        column_names_iva_cobrado_table = [
            "doc_number",
            "account",
            "doc_type",
            "clrng_date",
            "text_iva_cobrado",
            "reference",
            "billing_doc",
            "trading_partner",
            "doc_number_2",
            "clearing_doc",
            "tax_code",
            "doc_date",
            "posting_date",
            "amount_in_local_curr",
            "amount_in_doc_curr",
            "doc_curr",
            "eff_exchange_rate",
            "ano",
            "llave",
            "base_16",
            "cero_nacional",
            "cero_extranjero",
            "iva",
            "ieps",
            "iva_retenido",
            "total_factura",
            "diferencia",
            "ieps_base_iva",
            "nombre",
            "pais",
            "ieps_tasa_6",
            "ieps_tasa_7",
            "total_ieps",
            "diferencia_2"
        ]
        column_names_str_iva_cobrado = ", ".join(column_names_iva_cobrado_table)

        column_names_analisis_iva_cobrado = [
            "doc_number",
            "account",
            "reference",
            "doc_type",
            "doc_number_2",
            "clrng_date",
            "assignment_text",
            "text_analisis_iva_cobrado",
            "clearing_doc",
            "billing_doc",
            "tx",
            "amount_in_local_curr",
            "local_curr",
            "doc_date",
            "posting_date",
            "amount_in_dc",
            "diff",
            "ano",
            "llave",
            "base_16",
            "cero_nacional",
            "cero_extranjero",
            "iva",
            "ieps",
            "iva_retenido",
            "total_factura",
            "diferencia",
            "empty_col_1",
            "ieps_base_iva",
            "nombre",
            "pais",
            "tasa_9",
            "tasa_7",
            "tasa_6",
            "total_ieps",
            "diferencia_2"
        ]
        column_names_str_analisis_iva_cobrado = ", ".join(column_names_analisis_iva_cobrado)

    except Exception as e:
        print(f"Error retrieving column names or constructing query: {e}")
        exit()

    # Prepare data for bulk insertion CFDI Ingreso sheet
    data_collection_ingreso = custom_values_for_insert(data_sheet=cfdi_ingresos_sheet, max_col=21)
    final_result_ingreso_data = ",".join(data_collection_ingreso)
    # Prepare data for bulk insertion CFDI Complemento sheet
    data_collection_complemento = custom_values_for_insert(data_sheet=cfdi_complemento_sheet, max_col=33)
    final_result_complemento_data = ",".join(data_collection_complemento)
    # Prepare data for bulk insertion IVA Cobrado BCS sheet
    data_collection_iva_cobrado_table = custom_values_for_insert(data_sheet=iva_cobrado_sheet, max_col=34)
    final_result_iva_cobrado_data = ",".join(data_collection_iva_cobrado_table)
    # Prepare data for bulk insertion Analisis IVA Cobrado BHC sheet
    data_collection_analisis_iva_cobrado_table = custom_values_for_insert(data_sheet=analisis_iva_cobrado_sheet, max_col=36)
    final_result_analisis_iva_cobrado_data = ",".join(data_collection_analisis_iva_cobrado_table)

    insert_query = f"""SET datestyle = dmy; 
        INSERT INTO cfdi_ingreso ({column_names_str_ingresos}) VALUES {final_result_ingreso_data};
        INSERT INTO complemento ({column_names_str_complemento}) VALUES {final_result_complemento_data};
        INSERT INTO iva_cobrado_bcs ({column_names_str_iva_cobrado}) VALUES {final_result_iva_cobrado_data};
        INSERT INTO analisis_iva_cobrado_bhc ({column_names_str_analisis_iva_cobrado}) VALUES {final_result_analisis_iva_cobrado_data};
    """
    conn, cur = connection_db()
    try:
        # Execute bulk insert using executemany
        execute_query(cur, conn, insert_query)
    except Exception as err:
        print(err)
        
'''
