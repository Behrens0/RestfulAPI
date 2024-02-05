API para manejar requests de Customers

Descripcion
LA API ofrece distintos servicios básicos, de forma segura, a clientes, tales como el registro de nuevas regiones y comunas, registro de nuevos usuarios, eliminacion de los mismos y extraccion de informacion de una base de datos con los customers registrados.


Instalación
Pasos para la instalación del proyecto de forma local:

-Clonar el repositorio de GitHub: git clone https://github.com/Behrens0/RestfulAPI.git

Crear un virtual environment: python -m venv env
Activar virtual environment:
Windows: venv\Scripts\activate
Unix o MacOS: source venv/bin/activate

Instalar dependencias: pip install -r requirements.txt

Instalar Postman software para hacer las requests necesarias: 

Windows: powershell.exe -NoProfile -InputFormat None -ExecutionPolicy AllSigned -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://dl-cli.pstmn.io/install/win64.ps1'))"

Mac: curl -o- "https://dl-cli.pstmn.io/install/osx_arm64.sh" | sh

Linux: curl -o- "https://dl-cli.pstmn.io/install/linux64.sh" | sh

Configurar las environment variables en un archivo ".env.secret":
HOST= 
PORT = 
COMBINED=${HOST}:${PORT}
DB_PASSWORD = 
DB_USER = 
API_KEY = 

Detalles de la configuración de las environment variables:
HOST: el host de la conexion a la base de datos
PORT: puerto donde esta conectada la base de datos
DB_PASSWORD: contraseña del usuario de la base de datos
DB_USER: nombre del usuario de la base de datos
API_KEY: key necesaria para hacer todas las requests de la aplicación

Instrucciones del proyecto:

Crear diseño de la base de datos(la query esta en el archivo "queryScript.txt")

Correr el servidor uvicorn para la aplicación FastAPI: uvicorn main:app --reload

Acceder a la url proporcionada por uvicorn y navegar hacia el endpoint /docs, donde se encontrarán los usos de la aplicación.

API Endpoints:

Para todos los endpoints se requeriria que en el header de la request se envie una API key "x-api-key".
Además de la API key, para los endpoints "/delete_data" y "/get_customer" se requerirá el token "user-token" en el header, de un usuario registrado que haya sido creado hace menos de 1 hora .

/region - POST
Crear una region en la base de datos proporcionando en el body: description(str)
/commune - POST
Crear una comuna en la base de datos proporcionando en el body: description(str), id_reg(int): representa el id de una region ya existente
/register - POST
Registra un nuevo usuario proporcionando, en el body de la request:  name(str)
    email(str): no puede existir en el sistema el mismo email.
    dni(str)
    last_name(str)
    address(str o NULL)
    status(StatusEnum("I", "A", "trash"))
    id_com(int)
    id_reg(int)
    id_reg, dni y id_com no pueden tener la misma combinacion de valores 2 veces 

/login - POST
Inicio de sesión de un usuario proporcionando en el body: email(str). A su vez se generan un token especifico del usuario que se guarda en la base de datos para manejar la autenticacion del mismo.
/delete_data - DELETE
Se elimina un usuario logicamente proprocionando un email en el body: email(str)
/get_customer - GET
Se obtiene un usuario proporcionando un email o dni en el body y una bandera para saber cual se eligio: email_true(bool), email(str), dni(str)


Requerimientos mínimos.

1.6 GHz or faster processor. 1.5 GB of RAM.

Mac OS X: OS X El Capitan (10.11+), including macOS Monterey.
Windows: Windows 7 and later are supported. Older operating systems are not supported (and do not work).
Linux: Ubuntu 14.04 and newer, Fedora 24 and newer, and Debian 8 and newer. 
