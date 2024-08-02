import xml.etree.ElementTree as ET
import pandas as pd


class UploadFilesController:

    COLUMN_NAMES_INGRESOS = [
        "version",
        "estado",
        "tipo_comprobante",
        "rfc",
        "nombre",
    ]

    BANK_LIST = [
        "BBVA 64277",
        "Citibanamex 5611843",
        "JP Morgan 6461",
        "BBVA EUR 0196006752",
        "Deutsche Bank 4500",
        "JP Morgan 6487",
        "Citibanamex 5032927",
        "BBVA 012180001637146406",
        "BBVA 6026",
        "Santander 65-50049596-9",
        "In House Bank",
        "HSBC 0156000508",
        "HSBC 4005129028",
        "HSBC 4030167084",
        "Citibanamex 002180026157967545"
    ]

    @classmethod
    def process_file(cls, file, extension):
        pass

    @classmethod
    def load_file(cls, file, extension):
        data = None

        if extension == "xml":
            data = ET.parse(file)

        if extension == "xls" or extension == "xlsx":
            data = pd.read_excel(file)

        if extension == "pdf":
            data = file.read()
            print(data)

        return data

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
