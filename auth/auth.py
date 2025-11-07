from flask import session
from functools import wraps
from models.database import tiene_permiso, obtener_usuario_actual
import time

# Diccionario para control de intentos de login
login_attempts = {}

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            from flask import redirect, url_for, flash
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def permiso_requerido(permiso):
    """Decorador para requerir un permiso específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                from flask import redirect, url_for, flash
                flash('Debe iniciar sesión para acceder a esta página', 'warning')
                return redirect(url_for('login'))
            
            if not tiene_permiso(session['usuario_id'], permiso):
                from flask import redirect, url_for, flash
                flash('No tiene permisos para acceder a esta funcionalidad', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def limpiar_intentos_login():
    """Limpiar intentos de login antiguos"""
    global login_attempts
    current_time = time.time()
    login_attempts = {ip: data for ip, data in login_attempts.items() 
                     if current_time - data['timestamp'] < 900}  # 15 minutos

def registrar_intento_login(ip):
    """Registrar un intento de login fallido"""
    global login_attempts
    limpiar_intentos_login()
    
    if ip not in login_attempts:
        login_attempts[ip] = {'count': 0, 'timestamp': time.time()}
    
    login_attempts[ip]['count'] += 1
    login_attempts[ip]['timestamp'] = time.time()

def esta_bloqueado(ip):
    """Verificar si una IP está bloqueada por muchos intentos fallidos"""
    limpiar_intentos_login()
    if ip in login_attempts and login_attempts[ip]['count'] >= 5:
        return True
    return False

def resetear_intentos_login(ip):
    """Resetear intentos de login para una IP"""
    global login_attempts
    if ip in login_attempts:
        del login_attempts[ip]