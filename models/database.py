import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime

class Database:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "control_acceso",
            "port": 3306
        }
    
    def conectar(self):
        """Establecer conexión con la base de datos"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None
    
    @staticmethod
    def hash_contrasena(contrasena):
        """Hashear contraseña usando SHA-256"""
        return hashlib.sha256(contrasena.encode()).hexdigest()
    
    @staticmethod
    def verificar_contrasena(contrasena, hash_almacenado):
        """Verificar contraseña hasheada"""
        return Database.hash_contrasena(contrasena) == hash_almacenado

def obtener_permisos_usuario(usuario_id):
    """Obtener todos los permisos de un usuario basado en su rol"""
    db = Database()
    conn = db.conectar()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.nombre, p.modulo 
            FROM usuarios u
            JOIN roles r ON u.rol_id = r.id
            JOIN rol_permisos rp ON r.id = rp.rol_id
            JOIN permisos p ON rp.permiso_id = p.id
            WHERE u.id = %s AND u.estado = 'activo'
        """, (usuario_id,))
        
        permisos = cursor.fetchall()
        return [f"{p['modulo']}.{p['nombre']}" for p in permisos]
    except Error as e:
        print(f"Error al obtener permisos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def tiene_permiso(usuario_id, permiso_requerido):
    """Verificar si un usuario tiene un permiso específico"""
    permisos = obtener_permisos_usuario(usuario_id)
    return permiso_requerido in permisos

def obtener_usuario_actual():
    """Obtener información del usuario actual desde la sesión"""
    from flask import session
    if 'usuario_id' not in session:
        return None
    
    db = Database()
    conn = db.conectar()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.descripcion as rol_descripcion
            FROM usuarios u 
            JOIN roles r ON u.rol_id = r.id 
            WHERE u.id = %s AND u.estado = 'activo'
        """, (session['usuario_id'],))
        
        usuario = cursor.fetchone()
        if usuario:
            usuario['permisos'] = obtener_permisos_usuario(usuario['id'])
        return usuario
    except Exception as e:
        print(f"Error al obtener usuario actual: {e}")
        return None
    finally:
        cursor.close()
        conn.close()