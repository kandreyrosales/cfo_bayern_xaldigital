# Xaldigital CFO app

* **Lenguaje Backend:** Python 3.11
* **Framework Backend:** Flask
* **Plantillas:** Jinja2
* **Frontend:** CSS, Bootstrap5 y Javascript
* **Base de datos:** Postgresql
* **Lógica de la aplicación:** Endpoints de Flask API
* **Authentication:** AWS Cognito con cliente de AWS
* **IoC:** Terraform

Los endpoints el registro e ingreso a la aplicación son:
* **Registro:**: http://54.234.200.171:5000/registro
* **Login:** http://54.234.200.171:5000/login

Los modelos de la aplicación se encuentran en el siguiente [enlace](app/models.py) a través de la creación de tablas usando SQL y SQLAlchemy.

# Terradform

# Explicación del Archivo Terraform para Despliegue de Recursos en AWS

los archivos de Terraform se encuentran en la carpeta [enlace](app/utils) y se dividen en los siguientes archivos:

* **variables.tf:**: [enlace](app/utils/variables.tf) Define las variables que se utilizarán en el archivo de configuración de Terraform.
* **terraform_ec2_flask.tf:**: [enlace](app/utils/terraform_ec2_flask.tf) Define los recursos necesarios para la creación de una instancia EC2 en AWS.

Este archivo de Terraform define una infraestructura en AWS para un entorno que incluye un grupo de usuarios de Cognito, instancias de EC2 con una aplicación Flask, una base de datos RDS PostgreSQL, funciones Lambda, y sus configuraciones de seguridad.

## Proveedor de AWS

```hcl
provider "aws" {
  region = var.region_aws
}
```
## Grupo de Usuarios de Cognito

```hcl
resource "aws_cognito_user_pool" "cfo_bayer" {
  name = var.cognito_pool_name
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
  admin_create_user_config {
    allow_admin_create_user_only = false
  }
}
```
Crea un grupo de usuarios Cognito con atributos de nombre de usuario como correo electrónico, y políticas de contraseña estrictas. Se permiten atributos como el correo electrónico y el título corporativo.

## Cliente de la Aplicación Cognito

```hcl
resource "aws_cognito_user_pool_client" "cfo_bayer_cognito_client" {
  name = "cfo_bayer_app_client"
  user_pool_id = aws_cognito_user_pool.cfo_bayer.id
  explicit_auth_flows = ["ADMIN_NO_SRP_AUTH", "USER_PASSWORD_AUTH"]
}
```
Define un cliente de aplicación en Cognito para permitir autenticación de usuarios con flujos explícitos.

## Base de Datos RDS PostgreSQL

```hcl
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
```
Crea una instancia de base de datos PostgreSQL RDS con 20 GB de almacenamiento, accesible públicamente, y aplica configuraciones de usuario y seguridad.

## EC2 Flask
    
```hcl
resource "aws_instance" "flask_ec2" {
  ami                    = var.ami
  instance_type          = var.instance_type
  key_name               = var.ssh_key_pair_name
  associate_public_ip_address = true

  provisioner "remote-exec" {
    inline = [
      "export DEBIAN_FRONTEND=noninteractive",
      "sudo apt-get update -y",
      "sudo apt-get install -y python3 python3-pip python3-venv git libpq-dev python3-dev",
      "git clone ${var.github_repo} /home/ubuntu/flask_app",
      "python3 -m venv /home/ubuntu/flask_app/venv",
      "/home/ubuntu/flask_app/venv/bin/pip install --upgrade pip",
      "/home/ubuntu/flask_app/venv/bin/pip install -r /home/ubuntu/flask_app/app/requirements.txt",
      "/home/ubuntu/flask_app/venv/bin/pip install --upgrade gevent",
      "sudo ufw allow 5000",
      "sudo systemctl daemon-reload",
      "sudo systemctl start flask_app",
      "sudo systemctl enable flask_app"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.private_key_ec2_path)
      host        = self.public_ip
    }
  }
  tags = {
    Name = "cfo-bayer-Flask-Ubuntu"
  }
  vpc_security_group_ids = [aws_security_group.flask_sg_cfo_bayer.id]
}
```
Configura una instancia EC2 con Ubuntu, instala las dependencias necesarias y despliega la aplicación Flask utilizando Gunicorn.


## Grupos de Seguridad

```hcl
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
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }
}
```

## Flask EC2 Security Group

```hcl
resource "aws_security_group" "flask_sg_cfo_bayer" {
  name        = "flask_sg_cfo_bayer"
  description = "Security group for Flask EC2 instance"
  ingress {
    from_port   = 80
    to_port     = 80
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
    protocol        = "-1"
    cidr_blocks     = ["0.0.0.0/0"]
  }
}
```
Define un grupo de seguridad para la instancia Flask, permitiendo tráfico HTTP y en el puerto 5000 (Gunicorn).


## Outputs

```hcl
output "public_ip" {
  value = aws_instance.flask_ec2.public_ip
}

output "USER_POOL_ID_COGNITO" {
  value = aws_cognito_user_pool.cfo_bayer.id
}

output "CLIENT_ID_COGNITO" {
  value = aws_cognito_user_pool_client.cfo_bayer_cognito_client.id
}

output "endpoint" {
  value = aws_db_instance.posgtres_rds.endpoint
}
```
Estos outputs devuelven valores clave como el IP público de la instancia Flask, el ID del grupo de usuarios de Cognito, el ID del cliente de Cognito, y el endpoint de la base de datos RDS.

# Despliegue de Infraestructura con Terraform

Este proyecto utiliza Terraform para desplegar una infraestructura en AWS, incluyendo Cognito, EC2 para Flask, una base de datos RDS PostgreSQL, funciones Lambda y configuraciones de seguridad.

## Requisitos Previos

Asegúrate de tener los siguientes componentes instalados en tu entorno local:

- [Terraform](https://www.terraform.io/downloads.html) (versión 1.0.0 o superior)
- Una cuenta de [AWS](https://aws.amazon.com/)
- Credenciales de AWS configuradas en tu máquina local (puedes usar [AWS CLI](https://aws.amazon.com/cli/))
- Un par de claves SSH para acceder a las instancias EC2
- [Git](https://git-scm.com/) para clonar el repositorio de tu aplicación Flask

## Variables de Entorno Necesarias

Antes de ejecutar el proyecto, debes definir las siguientes variables de entorno o configurarlas en el archivo `variables.tf`:

- `region_aws`: La región de AWS donde deseas desplegar los recursos.
- `aws_account_number`: Número de cuenta de AWS.
- `cognito_pool_name`: Nombre del grupo de usuarios de Cognito.
- `db_name`: Nombre de la base de datos.
- `username_db`: Nombre de usuario de la base de datos.
- `password_db`: Contraseña de la base de datos.
- `ami`: ID de la AMI (Amazon Machine Image) para la instancia EC2.
- `instance_type`: Tipo de instancia EC2 (por ejemplo, `t3.micro`).
- `ssh_key_pair_name`: Nombre del par de claves SSH para la instancia EC2.
- `private_key_ec2_path`: Ruta al archivo de clave privada SSH para conectarte a la instancia EC2.
- `github_repo`: URL del repositorio GitHub de la aplicación Flask.

## Instalación y Despliegue

### 1. Clonar el Proyecto

Clona el repositorio donde se encuentra tu código de Terraform:

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <DIRECTORIO_DEL_REPOSITORIO>
```

###  2. Inicializar Terraform
Inicializa Terraform en el directorio del proyecto para descargar los proveedores y módulos requeridos:
```bash
terraform init
```

### 3. Previsualizar los Cambios
Ejecuta el siguiente comando para ver qué recursos se crearán sin aplicarlos:
```bash
terraform plan
```

### 4. Aplicar el Plan
Si el plan se ve correcto, aplica los cambios para crear los recursos en AWS:
```bash
terraform apply
```

### 5. Outputs
Una vez que el despliegue haya terminado, Terraform mostrará varios outputs importantes, como:

La IP pública de la instancia EC2
El ID del pool de usuarios Cognito
El ID del cliente de Cognito
El endpoint de la base de datos RDS

### Destrucción de Recursos
Cuando ya no necesites la infraestructura, puedes destruir todos los recursos creados con el siguiente comando:
```bash
terraform destroy
```

# Importador de Archivos Bancarios

Este módulo permite la carga de archivos XLSX con información bancaria para su procesamiento y posterior envío a un servicio API Gateway para su almacenamiento en la base de datos.

## Funcionalidad

### Carga de Archivo: 
El usuario puede cargar un archivo XLSX utilizando el botón "Choose File". El archivo cargado se procesa y la información relevante se envía a un servicio API Gateway para su manejo y almacenamiento en la base de datos.

### Información Almacenada: 
La información extraída del archivo "Cobradoras Agosto 2022.xlsx" se guarda en las siguientes columnas de la base de datos:

Book Date: Fecha en la que se registró la transacción.
Value Date: Fecha en la que el valor fue efectivo.
Posting Amount: Monto de la transacción.
Payment Method: Método de pago utilizado.
Ref: Referencia de la transacción.
Addref: Referencia adicional.
Reason of transfer: Motivo de la transferencia.
Payer: Persona o entidad que realizó el pago.
Receiver: Persona o entidad que recibió el pago.
Consulta del Valor del Dólar: El módulo incluye un enlace para consultar el valor del dólar en tiempo real.

## Uso
Seleccione el archivo XLSX: Haga clic en "Choose File" y seleccione el archivo "Cobradoras Agosto 2022.xlsx" desde su dispositivo.
Suba el archivo: Haga clic en "Subir Archivos" para cargar y procesar el archivo.
Verificación: Asegúrese de que la información se haya procesado correctamente y enviado al servicio API Gateway.
Consideraciones
Formato del Archivo: Asegúrese de que el archivo esté en formato XLSX y contenga la estructura de datos esperada para una correcta importación.
Tamaño del Archivo: El archivo no debe exceder los 40 MB de tamaño.

# Importador de Archivos SAT

Este componente permite a los usuarios cargar archivos de impuestos SAT en formato XML. Los usuarios pueden seleccionar y cargar hasta 10 archivos a la vez para procesar la información contenida en ellos.

## Funcionalidad

### Selección de Archivos:

Los usuarios pueden seleccionar múltiples archivos en formato XML utilizando el botón "Choose Files".
El límite máximo de archivos que se pueden cargar en una sola operación es de 10.
Subir Archivos:

Una vez seleccionados los archivos, los usuarios deben hacer clic en el botón "Subir Archivos" para comenzar el proceso de carga.
Los archivos cargados serán procesados según el flujo establecido para la importación y manejo de datos SAT.
Consideraciones
Asegúrate de que los archivos XML seleccionados cumplan con las especificaciones del SAT para evitar errores durante la importación.
El componente está diseñado para manejar eficientemente hasta 10 archivos por carga. Si tienes más archivos, considera dividirlos en lotes antes de la carga.

# Importador de Archivos SAP

Este componente permite a los usuarios cargar archivos relacionados con diversas funciones de SAP. Todos los archivos que se pueden cargar deben estar en formato .xlsx. La interfaz está dividida en varias secciones para la carga de diferentes tipos de archivos SAP, cada una correspondiente a una función o reporte específico.

## Funcionalidad

### Selección de Archivos:

Los usuarios pueden seleccionar un archivo en formato .xlsx en cada una de las secciones correspondientes.
Las secciones disponibles para la carga de archivos son:
* ** Auxiliares Cuentas de Bancos
* ** BCS FBL5N
* ** BHC FBL5N
* ** BCS Auxiliares IVA, IEPS y Retención IVA
* ** BHC Auxiliares IVA, IEPS y Retención IVA

## Subir Archivos:

Después de seleccionar el archivo deseado, los usuarios deben hacer clic en el botón "Subir Archivos" en la sección correspondiente para iniciar la carga.
Cada sección tiene su propio botón de carga, lo que permite subir archivos de manera independiente para cada tipo de reporte o auxiliar.
Consideraciones
Asegúrate de que los archivos .xlsx seleccionados cumplan con las especificaciones requeridas para cada tipo de auxiliar o reporte SAP.
El componente está diseñado para manejar un archivo por sección en cada carga. Si tienes múltiples archivos para una misma sección, deberás realizar varias cargas.

