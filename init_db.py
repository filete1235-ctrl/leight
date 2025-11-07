#!/usr/bin/env python3
"""
Script de inicialización de la base de datos
"""
import mysql.connector
from mysql.connector import Error
import hashlib
import os
import re
import config


def ejecutar_sql(conexion, sql_file):
    """Ejecutar archivo SQL en la base de datos conectada.
    Filtra sentencias CREATE DATABASE y USE para no cambiar la base destino (útil para Railway).
    """
    cursor = None
    try:
        cursor = conexion.cursor()

        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # Separar por ; y filtrar sentencias problemáticas
        statements = sql_script.split(';')
        for statement in statements:
            stmt = statement.strip()
            if not stmt:
                continue
            low = stmt.lower()
            # Ignorar creación o cambio de base de datos para ejecutar en la DB actual
            if low.startswith('create database') or low.startswith('use ') or low.startswith('drop database'):
                continue
            try:
                cursor.execute(stmt)
                # Si la sentencia devuelve filas, consumirlas para evitar 'Unread result found'
                try:
                    if getattr(cursor, 'with_rows', False):
                        _ = cursor.fetchall()
                except Exception:
                    # Ignorar errores al consumir resultados de consultas auxiliares
                    pass
            except Error as e:
                print(f"⚠️  Error ejecutando sentencia: {e}\nSentencia: {stmt[:200]}...")

        conexion.commit()
        print(f"✅ Script {sql_file} ejecutado correctamente")

    except Error as e:
        print(f"❌ Error ejecutando {sql_file}: {e}")
        try:
            conexion.rollback()
        except Exception:
            pass
    finally:
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass

def verificar_base_datos(conn_config: dict):
    """Intentar conectar a la base de datos destino; si no existe, intentar crearla.
    conn_config: dict con host,user,password,database,port
    """
    try:
        # Intentar conectar a la base de datos especificada
        conexion = mysql.connector.connect(
            host=conn_config.get('host', 'localhost'),
            user=conn_config.get('user', 'root'),
            password=conn_config.get('password', ''),
            database=conn_config.get('database')
        )
        conexion.close()
        print(f"✅ Conexión a la base '{conn_config.get('database')}' verificada")
        return True
    except Error as e:
        msg = str(e).lower()
        # Si la base no existe, intentar crearla conectando sin database
        if 'unknown database' in msg or "1049" in msg:
            try:
                print(f"📦 La base '{conn_config.get('database')}' no existe. Intentando crearla...")
                conexion = mysql.connector.connect(
                    host=conn_config.get('host', 'localhost'),
                    user=conn_config.get('user', 'root'),
                    password=conn_config.get('password', '')
                )
                cursor = conexion.cursor()
                cursor.execute(f"CREATE DATABASE {conn_config.get('database')} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                conexion.commit()
                cursor.close()
                conexion.close()
                print("✅ Base de datos creada")
                return True
            except Error as e2:
                print(f"❌ No se pudo crear la base de datos: {e2}")
                return False
        else:
            print(f"❌ Error verificando base de datos: {e}")
            return False

def main():
    """Función principal"""
    print("🚀 Inicializando Sistema de Control de Acceso")
    print("=" * 50)
    
    # Usar la configuración desde config.py (se adapta a variables de entorno/railway)
    conn_config = getattr(config, 'DB_CONFIG', None) or {
        'host': 'localhost', 'user': 'root', 'password': '', 'database': 'control_acceso', 'port': 3306
    }

    # Verificar/crear base de datos si es necesario
    if not verificar_base_datos(conn_config):
        return

    # Conectar a la base de datos específica
    try:
        conexion = mysql.connector.connect(
            host=conn_config.get('host'),
            user=conn_config.get('user'),
            password=conn_config.get('password'),
            database=conn_config.get('database'),
            port=conn_config.get('port')
        )

        print("✅ Conectado a la base de datos")

        # Ejecutar script SQL (filtrado internamente)
        if os.path.exists('control_acceso_3.sql'):
            ejecutar_sql(conexion, 'control_acceso_3.sql')
        else:
            print("❌ Archivo SQL no encontrado")
            print("💡 Asegúrate de que el archivo 'control_acceso_3.sql' esté en el directorio raíz")

        conexion.close()

        print("\n🎉 Inicialización completada!")
        print("\n👤 Usuarios de prueba creados:")
        print("   📧 admin@controlacceso.com / 🔑 admin123 (Administrador)")
        print("   📧 guardia@controlacceso.com / 🔑 guardia123 (Guardia)")
        print("   📧 recepcion@controlacceso.com / 🔑 recepcion123 (Recepción)")
        print("   📧 supervisor@controlacceso.com / 🔑 supervisor123 (Supervisor)")

    except Error as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Verifica que MySQL esté ejecutándose y las credenciales sean correctas")

if __name__ == '__main__':
    main()
