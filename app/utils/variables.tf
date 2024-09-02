# variables.tfvars

variable "region_aws" {
 type        = string
 description = "AWS Region"
 default     = "us-east-1"
}

variable "aws_account_number" {
 type        = string
 description = "AWS Account Number"
 default     = ""
}

variable "cognito_pool_name" {
 type        = string
 description = "AWS Congito Pool ID"
 default     = "cfobayer"
}


variable "instance_type" {
 type        = string
 description = "AWS Instance Type"
 default     = "t2.micro"
}

variable "ami" {
 type        = string
 description = "Linux Image from AWS"
 default     = "ami-0e86e20dae9224db8"
}

variable "bucket_name" {
 type        = string
 description = "Bucket name for project data (model files, csv files, etc.)"
 default     = "cfobayer"
}

variable "accessKeyId" {
 type        = string
 description = "accessKeyId AWS"
 default     = ""
}

variable "secretAccessKey" {
 type        = string
 description = "secretAccessKey AWS"
 default     = ""
}

variable "ssh_key_pair_name" {
 type        = string
 description = "Your SSH key pair name got from EC2"
 default     = "ec2-user"
}

variable "github_repo" {
 type        = string
 description = "Repo with the Flask code. Change remote exec to use private repo"
 default     = "https://github.com/kandreyrosales/cfo_bayern_xaldigital.git"
}

variable "private_key_ec2_path" {
 type        = string
 description = "PEM file path in your computer"
 default     = "/Users/kevinrosalesferreira/Downloads/ec2-user.pem"
}

variable "lambda_layer_pandas" {
 type        = string
 description = "Layer for Lambdas Python"
 default     = "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-pandas:2"
}

variable "password_db" {
 type        = string
 description = "Password for Postgresql DB instance"
 default     = "XalDigital!#388"
}

variable "db_name" {
 type        = string
 description = "Name for Postgresql DB instance"
 default     = "cfo_db"
}

variable "username_db" {
 type        = string
 description = "Username for Postgresql DB instance"
 default     = "cfo_user"
}