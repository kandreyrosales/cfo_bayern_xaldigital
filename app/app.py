import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import boto3
import jwt
from datetime import datetime
from functools import wraps

app = Flask(__name__)

app.secret_key = 'xaldigital!'
AWS_REGION_PREDICTIA = os.getenv("region_aws")
bucket_name = os.getenv("bucket_name")
accessKeyId = os.getenv("accessKeyId")
secretAccessKey = os.getenv("secretAccessKey")
arn_forecast_lambda=os.getenv("lambda_forecast_arn")
arn_ids_lambda=os.getenv("lambda_get_ids_arn")
arn_insights_lambda=os.getenv("lambda_get_insights")
arn_metrics_lambda=os.getenv("lambda_get_metrics")
CLIENT_ID_COGNITO =os.getenv("client_id")
USER_POOL_ID_COGNITO =os.getenv("user_pool")

# boto3 clients
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
lambda_client = boto3.client('lambda', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)
s3_client = boto3.client('s3', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId, aws_secret_access_key=secretAccessKey)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
        Accesing with Cognito using username and password.
        After login is redirected to reset password and login again
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username and password:
            cognito_response = authenticate_user(username, password)
            if cognito_response.get("reason") is not None:
                return render_template('login/login.html', error=cognito_response.get("reason"))
            else:
                challenge_name = cognito_response.get('ChallengeName', None)
                if challenge_name == 'NEW_PASSWORD_REQUIRED':
                    # User needs to set a new password
                    session_from_cognito=cognito_response["Session"]
                    return render_template('login/set_password.html', session=session_from_cognito, username=username)
                else:
                    auth_result = cognito_response["AuthenticationResult"]
                    if auth_result:
                        session['access_token'] = auth_result.get('AccessToken')
                        session['id_token'] = auth_result.get('IdToken')
                        return redirect(url_for('index'))
                    else:
                        return render_template('login/login.html', error=cognito_response)
        else:
            # Invalid credentials, show error message
            return render_template('login/login.html', error="Nombre de usuario y Contraseña obligatorios")
    else:
        return render_template(
            'login/login.html',
            accessKeyId=accessKeyId,
            secretAccessKey=secretAccessKey
        )
    
@app.route('/set_new_password', methods=['POST'])
def set_new_password():
    username = request.form['username']
    new_password = request.form['new_password']
    session_data=request.form['session']
    try:
        response = cognito_client.respond_to_auth_challenge(
            ClientId=CLIENT_ID_COGNITO,  # Replace 'your-client-id' with your Cognito app client ID
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session=session_data,  # Include the session token from the previous response
            ChallengeResponses={
                'USERNAME': username,
                'NEW_PASSWORD': new_password
            }
        )
        return redirect(url_for('index'))
    except cognito_client.exceptions.NotAuthorizedException as e:
        # Handle authentication failure
        return render_template('login/login.html', error="Hubo un problema al asignar una nueva contraseña")
    except Exception as e:
        # Handle other errors
        return render_template('login/login.html', error="Hubo un problema al asignar una nueva contraseña")

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
    except Exception as e:
        # Handle other errors
        return {"reason": "Error general. Por favor contactar al administrador"}
    
@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('login'))
