import os
import psycopg2

def create_tables_rds():
    db_host = os.getenv("db_endpoint")
    db_name = "postgres"
    db_user = "cfo_user"
    db_password = os.getenv("password_db")

    tables_and_views_queries = [
        """CREATE TABLE IF NOT EXISTS cfdi_ingreso (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              version VARCHAR(50),
              estado VARCHAR(50),
              tipo_comprobante VARCHAR(50),
              rfc VARCHAR(255),
              nombre VARCHAR(255),
              fecha_emision DATE,
              folio_interno VARCHAR(255),
              uuid_fiscal VARCHAR(255),
              producto_servicio_conforme_sat VARCHAR(255) NULL,
              concepto_del_cfdi TEXT NULL,
              moneda VARCHAR(5),
              metodo_de_pago VARCHAR(255),
              subtotal NUMERIC,
              descuento NUMERIC,
              iva NUMERIC,
              ieps NUMERIC,
              isr_retenido NUMERIC,
              iva_retenido NUMERIC,
              total_cfdi NUMERIC,
              tipo_de_relacion TEXT NULL,
              cfdi_relacionado VARCHAR(255) NULL
            );
    """,
        """CREATE TABLE IF NOT EXISTS complemento (
            id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        estado_sat VARCHAR(255),
        version_pagos VARCHAR(255),
        uuid_complemento VARCHAR(255),
        fecha_timbrado VARCHAR(50) NULL,
        fecha_emision DATE,
        folio VARCHAR(255),
        serie VARCHAR(255) NULL,
        subtotal NUMERIC,
        moneda VARCHAR(255),
        total NUMERIC,
        lugar_expedicion VARCHAR(255),
        rfc_emisor VARCHAR(255),
        nombre_emisor VARCHAR(255),
        rfc_receptor VARCHAR(255),
        nombre_receptor VARCHAR(255),
        uso_cfdi VARCHAR(255),
        clave_prod_serv VARCHAR(255),
        descripcion VARCHAR(255),
        fecha_de_pago timestamp,
        forma_de_pago varchar(50),
        moneda_p VARCHAR(5),
        tipo_cambio_p VARCHAR(5),
        monto NUMERIC,
        numero_operacion VARCHAR(255) NULL,
        importe_pagado_mo VARCHAR(255) NULL,
        id_documento VARCHAR(255),
        serie_dr VARCHAR(255),
        folio_dr VARCHAR(255),
        moneda_dr VARCHAR(5),
        num_parcialidad VARCHAR(255) NULL,
        imp_saldo_ant NUMERIC,
        importe_pagado NUMERIC,
        imp_saldo_insoluto NUMERIC
        );""",

        """
        CREATE TABLE IF NOT EXISTS iva_cobrado_bcs (
            id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        doc_number VARCHAR(255),
        account VARCHAR(255),
        doc_type VARCHAR(255),
        clrng_date date,
        text VARCHAR(255) NULL,
        reference VARCHAR(255),
        billing_doc VARCHAR(255),
        trading_partner numeric,
        
        doc_number_2 VARCHAR(255),
        clearing_doc VARCHAR(255),
        tax_code VARCHAR(255),
        doc_date date,
        posting_date date,
        amount_in_local_curr numeric,
        amount_in_doc_curr numeric,
        doc_curr VARCHAR(255),
        eff_exchange_rate numeric,
        
        ano numeric,
        llave VARCHAR(255),
        base_16 numeric,
        cero_nacional numeric,
        cero_extranjero numeric,
        
        iva numeric,
        ieps numeric,
        iva_retenido numeric,
        total_factura numeric,
        diferencia numeric,
        
        ieps_base_iva numeric,
        
        nombre VARCHAR(255),
        pais VARCHAR(255),
        ieps_tasa_6 numeric,
        ieps_tasa_7 numeric,
        total_ieps numeric,
        diferencia_2 numeric
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS resumen_iva_traslado (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ano_doc VARCHAR(255),
            sum_of_amount_in_local_cur numeric,
            row_labels VARCHAR(255),
            sum_of_amount_in_local_cur_2 numeric
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS resumen_iva_retenido (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ano_doc VARCHAR(255),
            sum_of_amount_in_local_cur numeric,
            row_labels VARCHAR(255),
            sum_of_amount_in_local_cur_2 numeric
        );
        """,

        """
            CREATE OR REPLACE VIEW conciliaciones AS
            SELECT t1.folio_interno as factura_bayer,
               t1.nombre as cliente,
               t1.tipo_comprobante as transaccion,
               t1.rfc as rfc,
               t1.fecha_emision as fecha,
               t1.estado as estado,
               t1.uuid_fiscal as uuid,
               to_char(t1.subtotal, 'FM99G999G999') AS subtotal,
               to_char(t1.iva, 'FM99G999G999') AS iva,
               to_char(t1.ieps, 'FM99G999G999') as ieps,
               to_char(t1.total_cfdi, 'FM99G999G999') as total,

               0 as depositos,
               '' as nombre_del_banco,

               '' as document_number_sap,
               '' as clearing_document_sap,
               0 as subtotal_sap,
               0 as iva_sap,
               0 as ieps_sap,
               0 as total_aplicacion_sap,

               CASE WHEN t2.uuid_complemento IS NOT NULL
                   THEN t2.uuid_complemento
                   ELSE 'Sin Complemento'
                   END AS uuid_relacionado,

               to_char(round((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal))), 2), 'FM99G999G999') as subtotal_sat,
               round(((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal))))*(t1.iva/t1.subtotal), 2) as iva_cobrado_sat,
               round(((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal))))*(t1.ieps/t1.subtotal), 2) as ieps_cobrado_sat,
               t2.importe_pagado as total_aplicacion_sat,
               0 as validador_aplicacion_pagos,

               CASE WHEN (ROUND(t1.total_cfdi-t2.importe_pagado, 2)+t2.importe_pagado)-(t1.total_cfdi) = 0
                THEN 0
                    ELSE round((t1.subtotal)-((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal)))), 2)
                END AS validador_subtotal_validador_iva,

                CASE WHEN (ROUND(t1.total_cfdi-t2.importe_pagado, 2)+t2.importe_pagado)-(t1.total_cfdi) = 0
                THEN 0
                    ELSE round((t1.iva)-(((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal))))*(t1.iva/t1.subtotal)), 2)
                END AS validar_ivas_validador_iva,

                CASE WHEN (ROUND(t1.total_cfdi-t2.importe_pagado, 2)+t2.importe_pagado)-(t1.total_cfdi) = 0
                THEN 0
                    ELSE round((t1.ieps)-(((t2.importe_pagado)/(1+((t1.iva/t1.subtotal)+(t1.ieps/t1.subtotal))))*(t1.ieps/t1.subtotal)), 2)
                END AS validador_ieps_validador_iva,

               CASE WHEN ROUND(t1.total_cfdi-t2.importe_pagado, 2) > 0
                THEN (ROUND(t1.total_cfdi-t2.importe_pagado, 2)+t2.importe_pagado)-(t1.total_cfdi)
                    ELSE ROUND(t1.total_cfdi-t2.importe_pagado, 2)
                END AS total_variacion_validador_iva
            FROM cfdi_ingreso t1
            LEFT JOIN complemento t2 ON t1.uuid_fiscal = t2.id_documento;
        """
    ]

    # Connect to the PostgreSQL database
    try:
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=5432)
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()
    # Execute table and views creation with queries
    for query in tables_and_views_queries:
        try:
            cur.execute(query)
            print("Table created successfully")
        except Exception as e:
            print(f"Error creating table: {e}")
        finally:
            conn.commit()  # Commit changes after each table creation

    # Close the connection
    cur.close()
    conn.close()

if __name__ == '__main__':
    create_tables_rds()