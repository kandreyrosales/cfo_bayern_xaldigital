import os
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
import jwt
from datetime import datetime
from functools import wraps
import psycopg2

from openpyxl.reader.excel import load_workbook

app = Flask(__name__)

app.secret_key = 'xaldigitalcfobayer!'
AWS_REGION_PREDICTIA = os.getenv("region_aws", 'us-east-1')
bucket_name = os.getenv("bucket_name")
accessKeyId = os.getenv("accessKeyId")
secretAccessKey = os.getenv("secretAccessKey")
CLIENT_ID_COGNITO =os.getenv("client_id")
USER_POOL_ID_COGNITO =os.getenv("user_pool")

# boto3 clients
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
lambda_client = boto3.client('lambda', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
s3_client = boto3.client('s3', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)

db_host = os.getenv("endpoint")
db_name = "postgres"
db_user = "cfo_user"
db_password = os.getenv("password_db")

def authenticate_user(username, password):
    try:
        response = cognito_client.admin_initiate_auth(
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            },
            ClientId=CLIENT_ID_COGNITO,
            UserPoolId=USER_POOL_ID_COGNITO,
            ClientMetadata={
                'username': username,
                'password': password,
            }
        )
        return response
    except cognito_client.exceptions.NotAuthorizedException as e:
        # Handle invalid credentials
        return {"reason": "Credenciales Inválidas"}
    except cognito_client.exceptions.ResourceNotFoundException as e:
        # Handle invalid credentials
        return {"reason": "Recurso No Encontrado"}
    except cognito_client.exceptions.UserNotFoundException as e:
        # Handle invalid credentials
        return {"reason": "Usuario No Encontrado"}
    except cognito_client.exceptions.UserNotConfirmedException as e:
        # Handle invalid credentials
        return {"reason": "Usuario No Confirmado"}
    except Exception as e:
        # Handle other errors
        return {"reason": "Error general. Por favor contactar al administrador"}


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Accessing with Cognito using username and password.
        After login is redirected to reset password and login again
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login/login.html',
                                   error="Nombre de usuario y Contraseña obligatorios")

        cognito_response = authenticate_user(username, password)

        reason = cognito_response.get("reason")
        if reason == "Usuario No Confirmado":
            return render_template('login/confirm_account_code.html', email=username)
        elif reason is not None:
            return render_template('login/login.html', error=reason)

        auth_result = cognito_response.get("AuthenticationResult")
        if not auth_result:
            return render_template('login/login.html', error=cognito_response)

        session['access_token'] = auth_result.get('AccessToken')
        session['id_token'] = auth_result.get('IdToken')
        return redirect(url_for('index'))
    else:
        return render_template(
            'login/login.html',
            accessKeyId=accessKeyId,
            secretAccessKey=secretAccessKey
        )

@app.route('/registro', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        corporate_title = request.form['corp_title']
        contact_number = request.form['contact_number']
        user_id = request.form['worker_custom_id']
        user_attributes = [
            {
                'Name': 'custom:corporate_title',
                'Value': corporate_title
            },
            {
                'Name': 'custom:contact_number',
                'Value': contact_number
            },
            {
                'Name': 'custom:user_id',
                'Value': user_id
            }
        ]
        try:
            response = cognito_client.sign_up(
                ClientId=CLIENT_ID_COGNITO,
                Username=username,
                Password=password,
                UserAttributes=user_attributes
            )
            return render_template('login/confirm_account_code.html', email=username)
        except cognito_client.exceptions.NotAuthorizedException as e:
            # Handle authentication failure
            return render_template(
                'login/signup.html',
                error="Usuario no Autorizado para ejecutar esta acción")
        except cognito_client.exceptions.UsernameExistsException:
            return render_template(
                'login/signup.html',
                error="Ya existe una cuenta asociada a este correo")
        except cognito_client.exceptions.InvalidPasswordException:
            return render_template(
                'login/signup.html',
                error="Crea una contraseña de al menos 8 dígitos, más segura, usando al menos una letra mayúscula, "
                      "un número y un carácter especial")
        except Exception as e:
            return render_template(
                'login/signup.html',
                error=f"Ha ocurrido el siguiente error: {e}")
    else:
        return render_template('login/signup.html')

@app.route('/confirmar_cuenta', methods=['GET', 'POST'])
def confirm_account_code():
    email = request.form['email_not_confirmed']
    email_code = request.form['custom_code']
    if request.method == "POST":
        try:
            cognito_client.confirm_sign_up(
                ClientId=CLIENT_ID_COGNITO,
                Username=email,
                ConfirmationCode=email_code
            )
            return render_template('login/login.html')
        except cognito_client.exceptions.ExpiredCodeException as e:
            return render_template(
                'login/confirm_account_code.html',
                error="El código enviado a su correo ha expirado", email=email)
        except cognito_client.exceptions.CodeMismatchException as e:
            return render_template(
                'login/confirm_account_code.html',
                error="El código no es válido", email=email)
        except cognito_client.exceptions.TooManyFailedAttemptsException as e:
            return render_template(
                'login/confirm_account_code.html',
                error="Máximo de intentos superados para validar la cuenta", email=email)
        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template(
                'login/confirm_account_code.html',
                error="Error: Usuario no Encontrado o Eliminado", email=email)
    else:
        return render_template('login/confirm_account_code.html', email=email)

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('login'))

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("access_token")
        if not token:
            return render_template('login/login.html')
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})  # Decode the token without verifying signature
            expiration_time = datetime.utcfromtimestamp(decoded_token['exp'])
            current_time = datetime.utcnow()
            if expiration_time > current_time:
                return f(*args, **kwargs)
            else:
                return render_template('login/login.html',
                                       error="Sesión Expirada. Ingrese sus datos de nuevo")
        except jwt.ExpiredSignatureError:
            return render_template('login/login.html',
                                   error="Sesión Expirada. Ingrese sus datos de nuevo")
    return decorated_function

@app.route('/olvido_contrasena', methods=['GET', 'POST'])
def forgot_password():
    if request.method == "POST":
        email = request.form['email_forgot_password']
        password = request.form['password']
        custom_code = request.form['custom_code']
        try:
            cognito_client.confirm_forgot_password(
                ClientId=CLIENT_ID_COGNITO,
                Username=email,
                ConfirmationCode=custom_code,
                Password=password,
            )
            return render_template('login/login.html')
        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template('login/reset_password.html',
                                   error="Usuario No Encontrado o Eliminado.", email=email)
        except cognito_client.exceptions.InvalidPasswordException as e:
            return render_template('login/reset_password.html',
                                   error="Usuario No Encontrado o Eliminado.", email=email)
        except cognito_client.exceptions.CodeMismatchException as e:
            return render_template('login/reset_password.html',
                                   error="Ha ocurrido un problema al enviar el código para asignar una nueva contraseña. "
                                         "Intenta de nuevo.",
                                   email=email)
        except Exception as e:
            return render_template('login/reset_password.html',
                                   error=f"Error: {e}", email=email)
    else:
        return render_template('login/reset_password.html')

@app.route('/enviar_link_contrasena', methods=['GET', 'POST'])
def send_reset_password_link():
    if request.method == "POST":
        email = request.form['email_forgot_password']
        try:
            cognito_client.forgot_password(
                ClientId=CLIENT_ID_COGNITO,
                Username=email
            )
            return render_template('login/reset_password.html')

        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template('login/send_reset_password_link.html',
                                   error="Usuario No Encontrado o Eliminado.", email=email)
        except cognito_client.exceptions.CodeDeliveryFailureException as e:
            return render_template('login/send_reset_password_link.html',
                                   error="Ha ocurrido un problema al enviar el código para asignar una nueva contraseña. "
                                         "Intenta de nuevo.",
                                   email=email)
        except Exception as e:
            return render_template('login/send_reset_password_link.html',
                                   error=f"Error: {e}", email=email)
    else:
        return render_template('login/send_reset_password_link.html')

@app.route('/')
@token_required
def index():
    # try:
    #     cognito_client.get_user(AccessToken=session.get("access_token"))
    # except cognito_client.exceptions.UserNotFoundException as e:
    #     return redirect(url_for('logout'))
    variation_labels = ["Cliente 1", "Cliente 2", "Cliente 3",
                        "Cliente 4", "Cliente 5", "Cliente 6",
                        "Cliente 7", "Cliente 8", "Cliente 9", "Cliente 10"]
    variation_data = [100, 80, 70, 100, 50, 60, 95, 100, 30, 10]

    transactions_labels = ["Totales", "Exitosas", "Revertidas", "Diferencias", "Pendientes"]
    transactions_data = [100, 50, 60, 30, 70]


    return render_template(
        'index.html',
        variation_data=variation_data,
        variation_labels=variation_labels,
        transactions_labels=transactions_labels,
        transactions_data=transactions_data
    )

@app.route('/invoke_lambda_rfc_data', methods=["GET"])
def invoke_lambda_rfc_data():
    try:
        # response = lambda_client.invoke(FunctionName=arn_ids_lambda, InvocationType='RequestResponse')
        # response_payload = response['Payload'].read()
        # result = json.loads(response_payload.decode('utf-8'))
        # if result.get("statusCode") == 200:
        #     body = json.loads(result["body"])
        #     return body["unique_ids"]
        return [
            "XAAA010101123456",
            "BAAA010101123456",
            "XIFF010101123456",
            "CABD010101123456",
        ]
    except Exception as e:
        return jsonify({'error': str(e)})

def get_conciliations_data():
    aws_postgres_result = [
        (1, 'John Doe', 30, 'john@example.com'),
        (2, 'Jane Smith', 25, 'jane@example.com'),
        (3, 'Alice Lee', 35, 'alice@example.com')
    ]
    result = jsonify(aws_postgres_result)
    return result.json

@app.route('/conciliaciones')
@token_required
def reconciliations_data_cfo():
    # try:
    #     cognito_client.get_user(AccessToken=session.get("access_token"))
    # except cognito_client.exceptions.UserNotFoundException as e:
    #     return redirect(url_for('logout'))
    conn, cur = connection_db()
    query_conciliations_view = """select * from conciliaciones;"""
    rows_data_view = get_query_rows(cur=cur, conn=conn, query=query_conciliations_view)

    return render_template(
        'reconciliations_data_cfo.html', initial_data_for_table=rows_data_view
    )

@app.route('/vista_subir_archivo')
def uploadfile():
    return render_template('uploadfile.html')
def custom_values_for_insert(data_sheet, max_col: int):
    # Prepare data for bulk insertion
    data_collection = []
    for row in data_sheet.iter_rows(min_row=2, max_col=max_col):  # Start from the second row (data)
        if row[0].value == "" or row[0].value is None:
            continue
        data_collection.append(f"""{tuple(str(cell.value).replace("'","") if cell.value is not None else '' for cell in row)}""")
    return data_collection

def connection_db():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host.split(":")[0],
            port=5432)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"Error connecting to database: {e}")
        exit()

def get_query_rows(cur, conn, query):
    try:
        cur.execute(query)
        rows = cur.fetchall()  # Fetch all rows
        # Print fetched rows (optional)
        return rows
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
    finally:
        # Close the connection
        if conn:
            cur.close()
            conn.close()
        print("PostgreSQL connection is closed")
def execute_query(cur, conn, query):
    # Execute bulk insert using executemany
    try:
        cur.execute(query)
        conn.commit()
        print(f"Data inserted successfully into table")
    except Exception as e:
        print(f"Error inserting data: {e}")
        conn.rollback()  # Rollback changes in case of errors

@app.route('/subir_archivo', methods=['POST'])
def subir_archivo():
    if 'archivo' not in request.files:
        return 'No se ha enviado ningún archivo'
    archivo = request.files['archivo']
    if archivo.filename == '':
        return 'No se ha seleccionado ningún archivo'
    # Verificar si el archivo tiene la extensión permitida
    if not archivo.filename.endswith('.xlsx'):
        return 'La extensión del archivo no está permitida. Se permiten solo archivos .xlsx'
    stream = BytesIO(archivo.read())
    workbook = load_workbook(stream)
    cfdi_ingresos_sheet = workbook.worksheets[0]
    cfdi_complemento_sheet = workbook.worksheets[1]
    # Prepare bulk insert query template
    try:
        column_names_ingresos = [
            "version",
            "estado",
            "tipo_comprobante",
            "nombre",
            "rfc",
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

    except Exception as e:
        print(f"Error retrieving column names or constructing query: {e}")
        exit()

    # Prepare data for bulk insertion CFDI Ingreso sheet
    data_collection_ingreso = custom_values_for_insert(data_sheet=cfdi_ingresos_sheet, max_col=21)
    final_result_ingreso_data = ",".join(data_collection_ingreso)
    # Prepare data for bulk insertion CFDI Complemento sheet
    data_collection_complemento = custom_values_for_insert(data_sheet=cfdi_complemento_sheet, max_col=33)
    final_result_complemento_data = ",".join(data_collection_complemento)

    insert_query = f"""SET datestyle = dmy; 
        INSERT INTO cfdi_ingreso ({column_names_str_ingresos}) VALUES {final_result_ingreso_data};
        INSERT INTO complemento ({column_names_str_complemento}) VALUES {final_result_complemento_data};
    """
    conn, cur = connection_db()

    # Execute bulk insert using executemany
    execute_query(cur, conn, insert_query)