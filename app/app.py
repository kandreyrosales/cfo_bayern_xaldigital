import os
from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import jwt
from datetime import datetime
from functools import wraps

app = Flask(__name__)

app.secret_key = 'xaldigitalcfobayer!'
AWS_REGION_PREDICTIA = os.getenv("region_aws")
bucket_name = os.getenv("bucket_name")
accessKeyId = os.getenv("accessKeyId")
secretAccessKey = os.getenv("secretAccessKey")
CLIENT_ID_COGNITO =os.getenv("client_id")
USER_POOL_ID_COGNITO =os.getenv("user_pool")

# boto3 clients
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
lambda_client = boto3.client('lambda', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
s3_client = boto3.client('s3', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)

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
    user_information = cognito_client.get_user(AccessToken=session.get("access_token"))
    return render_template('index.html')
