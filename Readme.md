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

Reiniciar el proyecto:
```
sudo systemctl restart flask_app
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

