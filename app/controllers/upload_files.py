from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import logging
import asyncio

from app import db, app
from app.utils import aws
from app.models import Banco

logger = logging.getLogger(__name__)


class UploadFilesController:
    COLUMN_NAMES_INGRESOS = [
        "version",
        "estado",
        "tipo_comprobante",
        "rfc",
        "nombre",
    ]

    #"Deutsche Bank 4500",
    #"JP Morgan 6487",
    #"Citibanamex 5032927",
    #"BBVA 012180001637146406",
    #"BBVA 6026",
    #"Santander 65-50049596-9",
    #"In House Bank",
    #"HSBC 0156000508",
    #"HSBC 4005129028",
    #"HSBC 4030167084",
    #"Citibanamex 002180026157967545"

    BANK_LIST = [
        ("BBVA_64277", "BBVA 64277"),
        ("Citibanamex_5611843", "Citibanamex 5611843"),
        ("JP_Morgan_6461", "JP Morgan 6461"),
        ("BBVA_EUR_0196006752", "BBVA EUR 0196006752")
    ]

    @classmethod
    def process_file(cls, file, extension):
        pass

    @classmethod
    def load_file(cls, file, extension):
        try:
            data = None
            print(file)
            print(extension)

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
    async def upload_ban_info(cls, files):
        try:
            today = datetime.now()
            tasks = []
            for file in files:
                object_name = f"{today.strftime('%d-%m-%Y')}/{files[file].filename}"
                tasks.append(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        cls.upload_to_s3,
                        files[file],
                        aws.S3_BUCKET_NAME,
                        object_name
                    )
                )

                # Await all upload tasks
                await asyncio.gather(*tasks)

                s3_url = f"https://{aws.S3_BUCKET_NAME}.s3.amazonaws.com/{today.strftime('%d-%m-%Y')}/{files[file].filename}"

                new_bank = Banco(
                    name=files[file].filename,
                    rfc=files[file].filename,
                    uuid='wewqe21121',
                    fiscal="fiscal",
                    s3_url=s3_url)

                new_bank.save()
        except Exception as e:
            logger.warning(str(e))

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
