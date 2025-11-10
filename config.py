import os
from datetime import timedelta
from urllib.parse import urlparse


from typing import Optional

# Helper: parsea una URL MySQL (mysql://user:pass@host:port/db)
def parse_mysql_url(url: Optional[str]):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        # parsed.path puede comenzar con '/'
        database = parsed.path.lstrip('/') if parsed.path else None
        return {
            'user': parsed.username,
            'password': parsed.password,
            'host': parsed.hostname,
            'port': int(parsed.port) if parsed.port else 3306,
            'database': database
        }
    except Exception:
        return None

# Construcción de la configuración de la base de datos a partir de variables de entorno
# Prioridad: MYSQL_PUBLIC_URL (pública, buena para conexiones externas), luego MYSQL_URL (interna), luego DATABASE_URL
mysql_url = os.environ.get('MYSQL_PUBLIC_URL') or os.environ.get('MYSQL_URL') or os.environ.get('DATABASE_URL')
parsed = parse_mysql_url(mysql_url)

# Valores por defecto
DB_CONFIG = {
    # Por defecto usamos el host interno de Railway y el puerto MySQL estándar 3306.
    # Nota: en desarrollo local puedes sobrescribir estas variables con .env o vars del sistema.
    'host': 'mysql.railway.internal',
    'user': 'root',
    'password': 'dBFXlwdFLkBzuXdLochakelKQVcZhcbD',  # Password por defecto para Railway
    'database': 'railway',  # Base de datos por defecto en Railway
    'port': 3306
}

if parsed:
    # Sobre-escribe con los valores parseados
    DB_CONFIG.update({
        'host': parsed.get('host') or DB_CONFIG['host'],
        'user': parsed.get('user') or DB_CONFIG['user'],
        'password': parsed.get('password') or DB_CONFIG['password'],
        'database': parsed.get('database') or DB_CONFIG['database'],
        'port': parsed.get('port') or DB_CONFIG['port']
    })
else:
    # Intenta leer variables individuales si no hay URL
    DB_CONFIG.update({
        'host': os.environ.get('MYSQLHOST') or os.environ.get('MYSQL_HOST') or DB_CONFIG['host'],
        'user': os.environ.get('MYSQLUSER') or os.environ.get('MYSQL_USER') or DB_CONFIG['user'],
        'password': os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD') or DB_CONFIG['password'],
        'database': os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or DB_CONFIG['database'],
        'port': int(os.environ.get('MYSQLPORT') or os.environ.get('MYSQL_PORT') or DB_CONFIG['port'])
    })

# Configuración de la aplicación
# SECRET_KEY: se recomienda establecer en la variable de entorno SECRET_KEY en producción.
# Si config.py define SECRET_KEY, se usará; de lo contrario `app.py` usará la variable de entorno.
DEBUG = True

# Configuración de sesiones y cookies
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Configuración de horarios
HORARIOS_ACCESO = {
    'hora_inicio': '08:00',
    'hora_fin': '18:00'
}

# Zona horaria de la aplicación (usar formato IANA). Por defecto: hora de Colombia (COT)
APP_TIMEZONE = os.environ.get('APP_TIMEZONE', 'America/Bogota')

# Configuración de credenciales
DURACION_CREDENCIAL_HORAS = 8

# Configuración de seguridad
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 15  # minutos
