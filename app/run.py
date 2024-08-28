import os
import io
from collections import defaultdict
from typing import Dict

import jwt
import boto3
import psycopg2
import pandas as pd
from functools import wraps, reduce
from datetime import datetime
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor

from app import init_app, create_db, app, create_conciliations_view, destroy_db
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    make_response,
)
from app.controllers.conciliation import ConciliationController
from app.controllers.upload_files import UploadFilesController
from app.models import (
    get_conciliations_view_data,
    get_count_incomes,
    get_count_transactions,
    get_eips_iva_conciliations_view_data,
    get_rfc_from_conciliations_view,
    get_clients_from_conciliations_view,
    Bank,
    get_transactions,
)

AWS_REGION_PREDICTIA = os.getenv("region_aws", "us-east-1")
bucket_name = os.getenv("bucket_name")
accessKeyId = os.getenv("accessKeyId")
secretAccessKey = os.getenv("secretAccessKey")
CLIENT_ID_COGNITO = os.getenv("client_id")
USER_POOL_ID_COGNITO = os.getenv("user_pool")
S3_BUCKET_NAME = os.getenv("s3_bucket_name", "test")

# boto3 clients
cognito_client = boto3.client(
    "cognito-idp",
    region_name=AWS_REGION_PREDICTIA,
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
)
lambda_client = boto3.client(
    "lambda",
    region_name=AWS_REGION_PREDICTIA,
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
)
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION_PREDICTIA,
    aws_access_key_id=accessKeyId,
    aws_secret_access_key=secretAccessKey,
)

db_host = os.getenv("db_endpoint", "localhost")
db_name = "postgres"
db_user = "postgres"
db_password = os.getenv("password_db", "root")


def authenticate_user(username, password):
    try:
        response = cognito_client.admin_initiate_auth(
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
            ClientId=CLIENT_ID_COGNITO,
            UserPoolId=USER_POOL_ID_COGNITO,
            ClientMetadata={
                "username": username,
                "password": password,
            },
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


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Accessing with Cognito using username and password.
    After login is redirected to reset password and login again
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return jsonify(error="Nombre de usuario y Contraseña obligatorios"), 400

        cognito_response = authenticate_user(username, password)

        reason = cognito_response.get("reason")
        if reason == "Usuario No Confirmado":
            return jsonify(error=username), 400
        elif reason is not None:
            return jsonify(error=reason), 400

        auth_result = cognito_response.get("AuthenticationResult")
        if not auth_result:
            return jsonify(error=cognito_response), 400

        session["access_token"] = auth_result.get("AccessToken")
        session["id_token"] = auth_result.get("IdToken")
        return redirect(url_for("index"))
    else:
        return render_template(
            "login/login.html", accessKeyId=accessKeyId, secretAccessKey=secretAccessKey
        )


@app.route("/registro", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        corporate_title = request.form["corp_title"]
        contact_number = request.form["contact_number"]
        user_id = request.form["worker_custom_id"]
        user_attributes = [
            {"Name": "custom:corporate_title", "Value": corporate_title},
            {"Name": "custom:contact_number", "Value": contact_number},
            {"Name": "custom:user_id", "Value": user_id},
        ]
        try:
            response = cognito_client.sign_up(
                ClientId=CLIENT_ID_COGNITO,
                Username=username,
                Password=password,
                UserAttributes=user_attributes,
            )
            return render_template("login/confirm_account_code.html", email=username)
        except cognito_client.exceptions.NotAuthorizedException as e:
            # Handle authentication failure
            return jsonify(error="Usuario no Autorizado para ejecutar esta acción"), 400
        except cognito_client.exceptions.UsernameExistsException:
            return jsonify(error="Ya existe una cuenta asociada a este correo"), 400
        except cognito_client.exceptions.InvalidPasswordException:
            return (
                jsonify(
                    error="Crea una contraseña de al menos "
                    "8 dígitos, más segura, usando al menos una letra mayúscula, "
                    "un número y un carácter especial"
                ),
                400,
            )
        except Exception as e:
            return jsonify(error=f"Ha ocurrido el siguiente error: {e}"), 400

    else:
        return render_template("login/signup.html")


@app.route("/confirmar_cuenta", methods=["GET", "POST"])
def confirm_account_code():
    email = request.form["email_not_confirmed"]
    email_code = request.form["custom_code"]
    if request.method == "POST":
        try:
            cognito_client.confirm_sign_up(
                ClientId=CLIENT_ID_COGNITO, Username=email, ConfirmationCode=email_code
            )
            return render_template("login/login.html")
        except cognito_client.exceptions.ExpiredCodeException as e:
            return render_template(
                "login/confirm_account_code.html",
                error="El código enviado a su correo ha expirado",
                email=email,
            )
        except cognito_client.exceptions.CodeMismatchException as e:
            return render_template(
                "login/confirm_account_code.html",
                error="El código no es válido",
                email=email,
            )
        except cognito_client.exceptions.TooManyFailedAttemptsException as e:
            return render_template(
                "login/confirm_account_code.html",
                error="Máximo de intentos superados para validar la cuenta",
                email=email,
            )
        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template(
                "login/confirm_account_code.html",
                error="Error: Usuario no Encontrado o Eliminado",
                email=email,
            )
    else:
        return render_template("login/confirm_account_code.html", email=email)


@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for("login"))


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("access_token")
        if not token:
            return render_template("login/login.html")
        try:
            decoded_token = jwt.decode(
                token, options={"verify_signature": False}
            )  # Decode the token without verifying signature
            expiration_time = datetime.utcfromtimestamp(decoded_token["exp"])
            current_time = datetime.utcnow()
            if expiration_time > current_time:
                return f(*args, **kwargs)
            else:
                return render_template(
                    "login/login.html",
                    error="Sesión Expirada. Ingrese sus datos de nuevo",
                )
        except jwt.ExpiredSignatureError:
            return render_template(
                "login/login.html", error="Sesión Expirada. Ingrese sus datos de nuevo"
            )

    return decorated_function


@app.route("/olvido_contrasena", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email_forgot_password"]
        password = request.form["password"]
        custom_code = request.form["custom_code"]
        try:
            cognito_client.confirm_forgot_password(
                ClientId=CLIENT_ID_COGNITO,
                Username=email,
                ConfirmationCode=custom_code,
                Password=password,
            )
            return render_template("login/login.html")
        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template(
                "login/reset_password.html",
                error="Usuario No Encontrado o Eliminado.",
                email=email,
            )
        except cognito_client.exceptions.InvalidPasswordException as e:
            return render_template(
                "login/reset_password.html",
                error="Usuario No Encontrado o Eliminado.",
                email=email,
            )
        except cognito_client.exceptions.CodeMismatchException as e:
            return render_template(
                "login/reset_password.html",
                error="Ha ocurrido un problema al enviar el código para asignar una nueva contraseña. "
                "Intenta de nuevo.",
                email=email,
            )
        except Exception as e:
            return render_template(
                "login/reset_password.html", error=f"Error: {e}", email=email
            )
    else:
        return render_template("login/reset_password.html")


@app.route("/enviar_link_contrasena", methods=["GET", "POST"])
def send_reset_password_link():
    if request.method == "POST":
        email = request.form["email_forgot_password"]
        try:
            cognito_client.forgot_password(ClientId=CLIENT_ID_COGNITO, Username=email)
            return render_template("login/reset_password.html")

        except cognito_client.exceptions.UserNotFoundException as e:
            return render_template(
                "login/send_reset_password_link.html",
                error="Usuario No Encontrado o Eliminado.",
                email=email,
            )
        except cognito_client.exceptions.CodeDeliveryFailureException as e:
            return render_template(
                "login/send_reset_password_link.html",
                error="Ha ocurrido un problema al enviar el código para asignar una nueva contraseña. "
                "Intenta de nuevo.",
                email=email,
            )
        except Exception as e:
            return render_template(
                "login/send_reset_password_link.html", error=f"Error: {e}", email=email
            )
    else:
        return render_template("login/send_reset_password_link.html")


@app.route("/", methods=["GET"])
# @token_required
def index():
    result_rfc = get_rfc_from_conciliations_view()
    column_names_rfc = result_rfc.keys()
    rfc_list = [dict(zip(column_names_rfc, row)) for row in result_rfc]

    result_clients = get_clients_from_conciliations_view()
    column_names_clients = result_clients.keys()
    client_list = [dict(zip(column_names_clients, row)) for row in result_clients]

    return render_template(
        "index.html",
        search=True,
        rfc_list=rfc_list,
        client_list=client_list,
        url="/get_dashboard_data",
        target="#result-dashboard",
    )


@app.route("/get_dashboard_data", methods=["GET"])
# @token_required
def dashboard_data():
    calendar_filter_start_date = request.args.get("calendar_filter_start_date", None)
    calendar_filter_end_date = request.args.get("calendar_filter_end_date", None)
    rfc_selector = request.args.get("rfc_selector", None)
    customer_name_selector = request.args.get("customer_name_selector", None)

    if calendar_filter_start_date != "" and calendar_filter_end_date != "":
        calendar_filter_start_date = format_date(calendar_filter_start_date)
        calendar_filter_end_date = format_date(calendar_filter_end_date, True)
    else:
        calendar_filter_start_date = None
        calendar_filter_end_date = None

    bank_records = get_count_transactions(
        calendar_filter_start_date, calendar_filter_end_date
    )

    bank_records_dicts = list(
        map(
            lambda x: {
                "bank_name": x[0],
                "total_posting_amount": x[1],
                "total_transactions": x[2],
            },
            bank_records,
        )
    )

    total_amount_transactions = sum(
        map(lambda x: x["total_posting_amount"], bank_records_dicts)
    )

    total_transactions_sum = sum(
        map(lambda x: x["total_transactions"], bank_records_dicts)
    )

    income_records = get_count_incomes(
        calendar_filter_start_date, calendar_filter_end_date
    )

    income_records_dicts = list(
        map(
            lambda x: {
                "client": x[0],
                "sum_total_amount": x[1],
                "sum_total_vat_16": x[2],
                "sum_total_ieps": x[3],
            },
            income_records,
        )
    )

    total_incomes_sum = sum(map(lambda x: x["sum_total_amount"], income_records_dicts))
    total_iva_sum = sum(map(lambda x: x["sum_total_vat_16"], income_records_dicts))
    total_ieps_sum = sum(map(lambda x: x["sum_total_ieps"], income_records_dicts))

    income_expenses = {
        "total_income": total_incomes_sum,
        "total_expenses": total_amount_transactions,
    }

    tax_info = {
        "vat_16": total_iva_sum,
        "ieps": total_ieps_sum,
        "amount_in_doc_curr_ieps": 0,
        "amount_in_doc_curr_iva_traladado": 0,
    }

    return (
        jsonify(
            [
                {"result_transactions": bank_records_dicts},
                {"total_amount_transactions": total_amount_transactions},
                {"total_transactions_sum": total_transactions_sum},
                {"tax_info": tax_info},
                {"total_income": []},
                {"income_expenses": income_expenses},
                {"income_records_dicts": income_records_dicts},
            ]
        ),
        200,
    )

    """
    data_trasactions = ConciliationController.group_transactions(
        bank_transactions_filtered
    )

    total_posting_amount_sum = sum(
        [float(item["total_posting_amount"]) for item in data_trasactions]
    )

    total_transactions_sum = sum(
        [item["total_transactions"] for item in data_trasactions]
    )

    
    """

    return jsonify([]), 200


@app.route("/conciliaciones")
# @token_required
def reconciliations_data_cfo():
    # try:
    #     cognito_client.get_user(AccessToken=session.get("access_token"))
    # except cognito_client.exceptions.UserNotFoundException as e:
    #     return redirect(url_for('logout'))

    result_rfc = get_rfc_from_conciliations_view()
    column_names_rfc = result_rfc.keys()
    rfc_list = [dict(zip(column_names_rfc, row)) for row in result_rfc]

    result_clients = get_clients_from_conciliations_view()
    column_names_clients = result_clients.keys()
    client_list = [dict(zip(column_names_clients, row)) for row in result_clients]

    return render_template(
        "reconciliations_data_cfo.html",
        search=True,
        url="/get_filtered_data_conciliations",
        target="#result-conciliations",
        rfc_list=rfc_list,
        client_list=client_list,
    )


def generate_filter_sql(start_date, end_date, rfc, customer):
    """
    Smart query for Where statement using variables from the page
    """
    where_query = """WHERE """
    query_date_range = f"""fecha BETWEEN '{start_date}' and '{end_date}' """
    query_rfc = f""" rfc='{rfc}' """
    query_customer = f""" cliente='{customer}' """

    field_flag = False
    if start_date and end_date:
        field_flag = True
        where_query += f"{query_date_range}"
    if rfc and rfc != "all":
        if field_flag:
            where_query += f" AND {query_rfc}"
        else:
            where_query += f"{query_rfc}"
        field_flag = True
    if customer and customer != "all":
        if field_flag:
            where_query += f" AND {query_customer}"
        else:
            where_query += f"{query_customer}"
            field_flag = True
    if field_flag:
        return where_query, True
    return where_query, False


@app.route("/get_filtered_data_conciliations", methods=["GET"])
def get_filtered_data_conciliations():
    if request.method == "GET":
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        calendar_filter_start_date = request.args.get(
            "calendar_filter_start_date", None
        )
        calendar_filter_end_date = request.args.get("calendar_filter_end_date", None)
        rfc_selector = request.args.get("rfc_selector", None)
        customer_name_selector = request.args.get("customer_name_selector", None)
        calendar_filter_value_date_start_date = request.args.get(
            "calendar_filter_value_date_start_date", None
        )

        # Format the dates to 'Y-m-d' before passing them to the query
        calendar_filter_start_date = format_date(calendar_filter_start_date)
        calendar_filter_end_date = format_date(calendar_filter_end_date, True)
        calendar_filter_value_date_start_date = format_date(
            calendar_filter_value_date_start_date
        )

        if calendar_filter_end_date:
            filter_date = calendar_filter_end_date
        else:
            filter_date = datetime.now()

        result, totals, sum_by_rfc = get_conciliations_view_data(
            calendar_filter_start_date=calendar_filter_start_date,
            calendar_filter_end_date=calendar_filter_end_date,
            rfc_selector=rfc_selector,
            customer_name_selector=customer_name_selector,
            calendar_filter_value_date_start_date=calendar_filter_value_date_start_date,
        )

        bank_records = get_transactions(filter_date)

        column_names = result.keys()
        data = [dict(zip(column_names, row)) for row in result]

        rcf_column_names = sum_by_rfc.keys()
        sum_rfc_data = [dict(zip(rcf_column_names, row)) for row in sum_by_rfc]

        bank_transactions_filtered = filter_bank_transactions(
            sum_rfc_data, bank_records
        )

        full_data = list(
            map(lambda x: update_bank_info(x, bank_transactions_filtered), data)
        )

        column_names_totals = totals.keys()
        data_totals = [dict(zip(column_names_totals, row)) for row in totals]

        start = (page - 1) * page_size
        end = start + page_size
        paginated_data = full_data[start:end]

        response = {
            "data": paginated_data,
            "total_data": data_totals,
            "total": len(data),
            "page": page,
            "page_size": page_size,
            "total_pages": (len(data) + page_size - 1) // page_size,
        }
        return jsonify(response), 200


@app.route("/download_data_conciliations", methods=["GET"])
def download_data_conciliations():
    if request.method == "GET":
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))

        calendar_filter_start_date = request.args.get(
            "calendar_filter_start_date", None
        )
        calendar_filter_end_date = request.args.get("calendar_filter_end_date", None)
        rfc_selector = request.args.get("rfc_selector", None)
        customer_name_selector = request.args.get("customer_name_selector", None)
        calendar_filter_value_date_start_date = request.args.get(
            "calendar_filter_value_date_start_date", None
        )

        # Format the dates to 'Y-m-d' before passing them to the query
        calendar_filter_start_date = format_date(calendar_filter_start_date)
        calendar_filter_end_date = format_date(calendar_filter_end_date)
        calendar_filter_value_date_start_date = format_date(
            calendar_filter_value_date_start_date
        )

        if calendar_filter_start_date:
            filter_date = calendar_filter_start_date
        else:
            filter_date = datetime.now()

        result, totals, sum_by_rfc = get_conciliations_view_data(
            calendar_filter_start_date=calendar_filter_start_date,
            calendar_filter_end_date=calendar_filter_end_date,
            rfc_selector=rfc_selector,
            customer_name_selector=customer_name_selector,
            calendar_filter_value_date_start_date=calendar_filter_value_date_start_date,
        )

        bank_records = get_transactions(filter_date)

        column_names = result.keys()
        data = [dict(zip(column_names, row)) for row in result]

        rcf_column_names = sum_by_rfc.keys()
        sum_rfc_data = [dict(zip(rcf_column_names, row)) for row in sum_by_rfc]

        bank_transactions_filtered = filter_bank_transactions(
            sum_rfc_data, bank_records
        )

        full_data = list(
            map(lambda x: update_bank_info(x, bank_transactions_filtered), data)
        )

        column_names_totals = totals.keys()
        data_totals = [dict(zip(column_names_totals, row)) for row in totals]

        # Convert data to DataFrame
        df = pd.DataFrame(full_data)
        df_totals = pd.DataFrame(data_totals)

        # Combine data and totals into one DataFrame if necessary
        if not df_totals.empty:
            df = pd.concat([df, df_totals], ignore_index=True)

        # Create a bytes buffer for the Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Conciliations")

        # Rewind the buffer
        output.seek(0)

        # Create a response
        response = make_response(output.read())
        response.headers["Content-Disposition"] = (
            "attachment; filename=conciliations_data.xlsx"
        )
        response.headers["Content-type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return response, 200


def filter_bank_transactions(rfcs, transactions):
    match_transactions = []
    for item in rfcs:
        result = list(
            filter(
                lambda transaction: int(transaction[3]) == int(item["sum"]),
                transactions,
            )
        )
        if len(result) > 0:
            bank = result[0]
            item["bank_name"] = bank[0]
            item["comment"] = bank[1]
            item["value_date"] = bank[2]
            item["posting_amount"] = bank[3]
            item["ref"] = bank[4]
            match_transactions.append(item)

    return match_transactions


def update_bank_info(item, bank_info_list) -> Dict:
    for bank_info in bank_info_list:
        if item["clearing_payment_policy"] == bank_info["clearing_payment_policy"]:
            item["bank_name"] = bank_info["bank_name"]
            item["bank_ref"] = bank_info["ref"]
            item["value_date"] = bank_info["value_date"].strftime("%d/%m/%Y")
            item["posting_amount_number"] = bank_info["posting_amount"]
            item["posting_amount"] = f"${bank_info['posting_amount']:,.2f}"
            item["comment"] = bank_info["comment"]
            break
    return item


def format_date(date_str, end_date: bool = False):
    """Helper function to convert a date string to 'Y-m-d' format."""
    if date_str:
        try:
            if end_date:
                return datetime.strptime(date_str, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=00
                )
            return datetime.strptime(date_str, "%Y-%m-%d")

        except ValueError:
            try:
                # If the above fails, assume the date is already in 'Y-m-d' format
                return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Date {date_str} does not match expected formats '%d/%m/%Y' or '%Y-%m-%d'"
                )
    return None


def custom_values_for_insert(data_sheet, max_col: int):
    # Prepare data for bulk insertion
    data_collection = []
    for row in data_sheet.iter_rows(
        min_row=2, max_col=max_col
    ):  # Start from the second row (data)
        if row[0].value == "" or row[0].value is None:
            continue
        data_collection.append(
            f"""{tuple(str(cell.value).replace("'", "") if cell.value is not None else '' for cell in row)}"""
        )
    return data_collection


def connection_db():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host.split(":")[0],
            port=5432,
        )
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


@app.route("/vista_subir_archivo/")
def uploadfile(extension):
    return render_template("uploadfile.html", extension=extension)


@app.route("/subir_info", methods=["GET", "POST"])
def upload_banks_info():
    if request.method == "GET":
        return render_template(
            "uploader_info_files.html", title="Importador de archivos"
        )

    if request.method == "POST":
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(
                UploadFilesController.upload_ban_info,
                request.files,
                request.form["dof"],
            )
        return (
            jsonify(
                message="Ha comenzado el proceso de carga de la información bancaria. "
                "Por favor, espere unos minutos. El tiempo de "
                "carga depende del tamaño de los archivos."
            ),
            200,
        )


@app.route("/subir_info_sat_sap", methods=["POST"])
def upload_sat_sap():
    if request.method == "POST":
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(UploadFilesController.upload_sap_info, request.files)
        return (
            jsonify(
                message="Se está cargando información de SAP. "
                "Por favor, espere unos minutos. El tiempo de "
                "carga depende del tamaño de los archivos."
            ),
            200,
        )


@app.route("/subir_info_sat", methods=["POST"])
def upload_sat():
    if request.method == "POST":
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(UploadFilesController.upload_sat_info, request.files)
        return (
            jsonify(
                message="Se está cargando información de SAT. "
                "Por favor, espere unos minutos. El tiempo de "
                "carga depende del tamaño de los archivos."
            ),
            200,
        )


@app.route("/subir_archivo/<extension>", methods=["GET", "POST"])
def subir_archivo(extension):
    if request.method == "GET":
        return render_template("uploadfile.html", extension=extension)

    if "archivo" not in request.files:
        error = "No se ha enviado ningún archivo"
        return render_template("uploadfile.html", error=error, extension=extension)

    archivo = request.files["archivo"]

    if archivo.filename == "":
        error = "No se ha seleccionado ningún archivo"
        return render_template("uploadfile.html", error=error, extension=extension)

    # Verificar si el archivo tiene la extensión permitida
    if not archivo.filename.endswith(extension):
        error = f"La extensión del archivo no está permitida. Se permiten solo archivos {extension}"
        return render_template("uploadfile.html", error=error, extension=extension)

    is_valid, error, data = UploadFilesController.valid_file(archivo, extension)

    if not is_valid:
        error = error
        return render_template("uploadfile.html", error=error, extension=extension)

    s3_client.upload_fileobj(archivo, S3_BUCKET_NAME, archivo.filename)

    return render_template(
        "uploadfile.html",
        error=None,
        extension=extension,
        success="El archivo se ha cargado y se esta procesando en estos momentos",
    )


if __name__ == "__main__":
    init_app()
    # destroy_db()
    # create_db()
    # create_conciliations_view()
