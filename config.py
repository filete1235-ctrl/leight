import os
from datetime import timedelta

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "user": "root", 
    "password": "",
    "database": "control_acceso",
    "port": 3306
}

# Configuración de la aplicación
SECRET_KEY = 'clave_secreta_super_segura_mejorada_2024'
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

# Configuración de credenciales
DURACION_CREDENCIAL_HORAS = 8

# Configuración de seguridad
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 15  # minutos