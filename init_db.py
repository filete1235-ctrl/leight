#!/usr/bin/env python3
"""
Script de inicialización de la base de datos
"""
import mysql.connector
from mysql.connector import Error
import hashlib
import os

def ejecutar_sql(conexion, sql_file):
    """Ejecutar archivo SQL"""
    try:
        cursor = conexion.cursor()
        
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Ejecutar cada sentencia por separado
        statements = sql_script.split(';')
        for statement in statements:
            if statement.strip():
                cursor.execute(statement)
        
        conexion.commit()
        print(f"✅ Script {sql_file} ejecutado correctamente")
        
    except Error as e:
        print(f"❌ Error ejecutando {sql_file}: {e}")
        conexion.rollback()
    finally:
        cursor.close()

def verificar_base_datos():
    """Verificar y crear la base de datos si no existe"""
    try:
        # Conectar sin especificar base de datos
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        
        cursor = conexion.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute("SHOW DATABASES LIKE 'control_acceso'")
        resultado = cursor.fetchone()
        
        if not resultado:
            print("📦 Creando base de datos...")
            cursor.execute("CREATE DATABASE control_acceso CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            print("✅ Base de datos creada")
        else:
            print("✅ Base de datos ya existe")
        
        cursor.close()
        conexion.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicializando Sistema de Control de Acceso")
    print("=" * 50)
    
    # Verificar base de datos
    if not verificar_base_datos():
        return
    
    # Conectar a la base de datos específica
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="control_acceso"
        )
        
        print("✅ Conectado a la base de datos")
        
        # Ejecutar script SQL
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