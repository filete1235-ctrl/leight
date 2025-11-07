"""
Script principal para ejecutar la aplicación
"""
from app import app
import os

if __name__ == '__main__':
    # Verificar si la base de datos existe
    try:
        from models.database import Database
        db = Database()
        conn = db.conectar()
        if conn:
            print("✅ Conexión a la base de datos exitosa")
            conn.close()
        else:
            print("❌ Error: No se pudo conectar a la base de datos")
            print("💡 Ejecuta primero el script SQL proporcionado")
    except Exception as e:
        print(f"❌ Error de base de datos: {e}")
    
    # Ejecutar la aplicación
    print("\n🚀 Iniciando Sistema de Control de Acceso...")
    print("📊 Sistema de permisos cargado")
    print("🔐 Autenticación con cookies configurada")
    print("🌐 Servidor web listo")
    print("\n📍 Accede a: http://localhost:5000")
    print("👤 Usuario demo: admin@controlacceso.com")
    print("🔑 Contraseña demo: admin123")
    print("\n⏹️  Presiona Ctrl+C para detener el servidor\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)