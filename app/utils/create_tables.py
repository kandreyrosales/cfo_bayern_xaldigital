import os
import psycopg2

def create_tables_rds():
    db_host = os.getenv("endpoint")
    db_name = os.getenv("db_name", "postgres")
    db_user = os.getenv("username_db","cfo_user")
    db_password = os.getenv("password_db")

    tables = [
        """CREATE TABLE IF NOT EXISTS cfdi_ingreso (
              id SERIAL PRIMARY KEY,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              version VARCHAR(50),
              estado VARCHAR(50),
              tipo_comprobante VARCHAR(50),
              nombre VARCHAR(255),
              rfc VARCHAR(255),
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
        """CREATE TABLE IF NOT EXISTS tabla_resultante (
                      id SERIAL PRIMARY KEY,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      factura_bayer VARCHAR(255),
                      cliente VARCHAR(255),
                      transaccion VARCHAR(10),
                      fecha DATE,

                      uuid_xml_facturacion VARCHAR(255),
                      subtotal_xml_facturacion NUMERIC,
                      iva_xml_facturacion NUMERIC,
                      ieps_xml_facturacion NUMERIC,
                      total_xml_facturacion NUMERIC,

                      depositos_bancos NUMERIC,

                      subtotal_sap NUMERIC,
                      iva_sap NUMERIC,
                      total_aplicacion_sap NUMERIC,

                      uuid_relacionado_sat VARCHAR(255),
                      subtotal_sat NUMERIC,
                      iva_cobrado_sat NUMERIC,
                      ieps_cobrado_sat NUMERIC,
                      total_aplicacion_sat NUMERIC,

                      validador_aplicacion_pagos NUMERIC,

                      validador_subtotal_validador_iva NUMERIC,
                      validar_ivas_validador_iva NUMERIC,
                      validador_ieps_validador_iva NUMERIC,
                      total_variacion_validador_iva NUMERIC
                    );""",
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
        );"""]

    # Connect to the PostgreSQL database
    try:
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=5432)
        cur = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()
    # Execute table creation queries
    for query in tables:
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