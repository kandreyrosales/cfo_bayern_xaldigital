import os
import boto3

bucket_name = os.getenv("bucket_name")
accessKeyId = os.getenv("accessKeyId")
secretAccessKey = os.getenv("secretAccessKey")

USER_POOL_ID_COGNITO = os.getenv("user_pool")
S3_BUCKET_NAME = os.getenv("bucket_name")
AWS_REGION_PREDICTIA = os.getenv("region_aws", 'us-east-1')


def get_cognito_client():
    # boto3 clients
    return boto3.client('cognito-idp', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId,
                        aws_secret_access_key=secretAccessKey)


def get_lambda_client():
    return boto3.client('lambda', region_name=AWS_REGION_PREDICTIA, aws_access_key_id=accessKeyId,
                        aws_secret_access_key=secretAccessKey)


def upload_to_s3():
    return boto3.client('s3',
                        region_name=AWS_REGION_PREDICTIA,
                        aws_access_key_id=accessKeyId,
                        aws_secret_access_key=secretAccessKey
                        )
