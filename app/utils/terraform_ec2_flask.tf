provider "aws" {
  region = var.region_aws
}

resource "aws_cognito_user_pool" "cfo_bayer" {
  name = var.cognito_pool_name
  # Enable admin user password authentication
  username_attributes = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
  }

  schema {
    attribute_data_type = "String"
    name                = "corporate_title"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "contact_number"
    required            = false
    mutable             = true
  }

  schema {
    attribute_data_type = "String"
    name                = "user_id"
    required            = false
    mutable             = true
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }
}

resource "aws_cognito_user_pool_client" "cfo_bayer_cognito_client" {
  name = "cfo_bayer_app_client"
  user_pool_id = aws_cognito_user_pool.cfo_bayer.id
  # Configure other settings as needed
  explicit_auth_flows = ["ADMIN_NO_SRP_AUTH", "USER_PASSWORD_AUTH"]
}

# # Create ZIP archive of Lambda function code
# data "archive_file" "lambda_zip" {
#   type        = "zip"
#   source_dir  = "../lambdas-cfo_bayer/"  # Path to the directory containing Lambda function code
#   output_path = "${path.module}/lambda_function.zip"
# }


# # Define Lambda function lambda-ids
# resource "aws_lambda_function" "lambdaids" { 
#   function_name    = "lambda-ids"
#   role             = aws_iam_role.lambda_role.arn
#   handler          = "lambda-ids.lambda_handler"
#   runtime          = "python3.12"
#   filename         = data.archive_file.lambda_zip.output_path
#   source_code_hash = data.archive_file.lambda_zip.output_base64sha256
#   layers           = [var.lambda_layer_pandas]  # ARN of your Lambda layer

#   environment {
#     variables = {
#       BUCKET_NAME = var.bucket_name
#     }
#   }
# }

# # Define Lambda function lambda-forecast
# resource "aws_lambda_function" "lambdaforecast" { 
#   function_name    = "lambda-forecast"
#   role             = aws_iam_role.lambda_role.arn
#   handler          = "lambda-forecast.lambda_handler"
#   runtime          = "python3.12"
#   filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
#   source_code_hash = data.archive_file.lambda_zip.output_base64sha256
#   layers           = [var.lambda_layer_pandas]  # ARN of your Lambda layer

#   environment {
#     variables = {
#       BUCKET_NAME = var.bucket_name
#     }
#   }
# }

# # Define Lambda function lambda-insights
# resource "aws_lambda_function" "lambdainsights" { 
#   function_name    = "lambda-insights"
#   role             = aws_iam_role.lambda_role.arn
#   handler          = "lambda-insights.lambda_handler"
#   runtime          = "python3.12"
#   filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
#   source_code_hash = data.archive_file.lambda_zip.output_base64sha256
#   layers           = [var.lambda_layer_pandas]  # ARN of your Lambda layer

#   environment {
#     variables = {
#       BUCKET_NAME = var.bucket_name
#     }
#   }
# }

# # Define Lambda function lambda-metrics
# resource "aws_lambda_function" "lambdametrics" { 
#   function_name    = "lambda-metrics"
#   role             = aws_iam_role.lambda_role.arn
#   handler          = "lambda-metrics.lambda_handler"
#   runtime          = "python3.12"
#   filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
#   source_code_hash = data.archive_file.lambda_zip.output_base64sha256
#   layers           = [var.lambda_layer_pandas]  # ARN of your Lambda layer

#   environment {
#     variables = {
#       BUCKET_NAME = var.bucket_name
#     }
#   }
# }

# # Define Lambda function lambda-metrics
# resource "aws_lambda_function" "lambdasendemail" { 
#   function_name    = "lambda-email"
#   role             = aws_iam_role.lambda_role.arn
#   handler          = "lambda-sendemail.lambda_handler"
#   runtime          = "python3.12"
#   filename         = data.archive_file.lambda_zip.output_path  # Path to the ZIP archive of Lambda function code
#   source_code_hash = data.archive_file.lambda_zip.output_base64sha256

#   environment {
#     variables = {
#       pool_id = aws_cognito_user_pool.cfo_bayer.id
#     }
#   }
# }

# Define IAM role for Lambda function
resource "aws_iam_role" "lambda_role_cfo" {
  name = "lambda-role-cfo"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "cognito_list_users_policy" {
  name        = "cognito-list-users-policy"
  description = "Allows Lambda execution role to list users in Cognito User Pool"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "cognito-idp:ListUsers"
        Resource = "arn:aws:cognito-idp:${var.region_aws}:${var.aws_account_number}:userpool/${aws_cognito_user_pool.cfo_bayer.id}"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cognito_list_users_policy_attachment" {
  role       = aws_iam_role.lambda_role_cfo.name
  policy_arn = aws_iam_policy.cognito_list_users_policy.arn
}


# Attach IAM policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_attachment" {
  role       = aws_iam_role.lambda_role_cfo.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"  # Attach a read-only S3 access policy
}

resource "aws_security_group" "rds_sg" {
  name_prefix = "rds_sg"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"   // Allow all protocols
    cidr_blocks     = ["0.0.0.0/0"]  // Allow traffic to any IPv4 address
  }
}

resource "aws_db_instance" "posgtres_rds" {
  engine                 = "postgres"
  db_name                = var.db_name
  identifier             = "cfo"
  instance_class         = "db.t3.micro"
  engine_version         = "12"
  allocated_storage      = 20
  publicly_accessible    = true
  username               = var.username_db
  password               = var.password_db
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot    = true

  tags = {
    Name = "cfo-db"
  }
}

output "endpoint" {
  value = aws_db_instance.posgtres_rds.endpoint
}

resource "aws_instance" "flask_ec2" {
  ami                    = var.ami
  instance_type          = var.instance_type
  key_name               = var.ssh_key_pair_name
  associate_public_ip_address = true


  provisioner "remote-exec" {
    inline = [
      # Install required packages
      "sudo apt-get update -y",
      "sudo apt-get install -y python3 git",
      "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py",
      "sudo python3 get-pip.py",
      "sudo apt-get install -y python3-venv",  # Install python3-venv package for virtual environments
      "sudo apt install -y libpq-dev python3-dev",

      "echo \"export AWS_ACCESS_KEY_ID=${var.accessKeyId}\" >> ~/.bashrc",
      "echo \"export AWS_SECRET_ACCESS_KEY=${var.secretAccessKey}\" >> ~/.bashrc",
      "echo \"export AWS_REGION=${var.region_aws}\" >> ~/.bashrc",
      "echo \"export client_id=${aws_cognito_user_pool_client.cfo_bayer_cognito_client.id}\" >> ~/.bashrc",
      "echo \"export user_pool=${aws_cognito_user_pool.cfo_bayer.id}\" >> ~/.bashrc",
      "echo \"export db_endpoint=${aws_db_instance.posgtres_rds.endpoint}\" >> ~/.bashrc",
      "echo \"export password_db=${var.password_db}\" >> ~/.bashrc",

      # Clone Flask application from GitHub
      "git clone ${var.github_repo} /home/ubuntu/flask_app",

      # Create and activate virtual environment
      "cd /home/ubuntu/flask_app",
      "python3 -m venv venv",
      "source venv/bin/activate",
      "cd app/",

      # Install dependencies
      "pip install -r requirements.txt",

      "sudo ufw allow 5000",

      # Create a systemd service for Gunicorn
      "cat <<EOF | sudo tee /etc/systemd/system/flask_app.service",
      "[Unit]",
      "Description=Gunicorn instance to serve Flask application",
      "After=network.target",

      "[Service]",
      "User=ubuntu",
      "Group=ubuntu",
      "WorkingDirectory=/home/ubuntu/flask_app/app",
      "Environment=\"PATH=/home/ubuntu/flask_app/venv/bin\"",
      "ExecStart=/home/ubuntu/.local/bin/gunicorn -w 1 -b 0.0.0.0:5000 -e bucket_name=${var.bucket_name} -e region_aws=${var.region_aws} -e accessKeyId=${var.accessKeyId} -e secretAccessKey=${var.secretAccessKey} -e client_id=${aws_cognito_user_pool_client.cfo_bayer_cognito_client.id} -e user_pool=${aws_cognito_user_pool.cfo_bayer.id} -e db_endpoint=${aws_db_instance.posgtres_rds.endpoint} -e db_name=${var.db_name} -e username_db=${var.username_db} -e password_db=${var.password_db} run:app",
      "Restart=always",

      "[Install]",
      "WantedBy=multi-user.target",
      "EOF",

      # Start and enable the Gunicorn service
      "sudo systemctl daemon-reload",
      "sudo systemctl start flask_app",
      "sudo systemctl enable flask_app",
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"  # SSH username for Amazon Linux, CentOS, or Red Hat AMIs
      private_key = file(var.private_key_ec2_path)  # Replace with the path to your SSH private key file
      host        = self.public_ip
    }
  }

  tags = {
    Name = "cfo-bayer-Flask-Ubuntu"
  }

  vpc_security_group_ids = [aws_security_group.flask_sg_cfo_bayer.id]

}

resource "aws_security_group" "flask_sg_cfo_bayer" {
  name        = "flask_sg_cfo_bayer"
  description = "Security group for Flask EC2 instance"

  // Ingress rule to allow HTTP traffic from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  // Allow traffic from any IPv4 address
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"   // Allow all protocols
    cidr_blocks     = ["0.0.0.0/0"]  // Allow traffic to any IPv4 address
  }
}

output "public_ip" {
  value = aws_instance.flask_ec2.public_ip
}

# output "lambda_get_ids_arn" {
#   value = aws_lambda_function.lambdaids.arn
# }
#
# output "lambda_forecast_arn" {
#   value = aws_lambda_function.lambdaforecast.arn
# }
#
# output "lambda_insights_arn" {
#   value = aws_lambda_function.lambdainsights.arn
# }
#
# output "lambda_emails_arn" {
#   value = aws_lambda_function.lambdasendemail.arn
# }
#
# output "lambda_metrics_arn" {
#   value = aws_lambda_function.lambdametrics.arn
# }

# output "USER_POOL_ID_COGNITO" {
#   value = aws_cognito_user_pool.cfo_bayer.id
# }

# output "CLIENT_ID_COGNITO" {
#   value = aws_cognito_user_pool_client.cfo_bayer_cognito_client.id
# }