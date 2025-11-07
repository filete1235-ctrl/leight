from flask import render_template
from models.database import Database, obtener_usuario_actual
from auth.auth import login_required
from auth.permissions import VER_ALERTAS, VER_USUARIOS, VER_REGISTRO_ACCESOS

@login_required
def dashboard():
    """Dashboard principal con estadísticas según permisos"""
    db = Database()
    conn = db.conectar()
    if not conn:
        return render_template('dashboard.html', estadisticas={})
    
    usuario_actual = obtener_usuario_actual()
    estadisticas = {}
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Estadísticas básicas para todos los roles
        cursor.execute("SELECT COUNT(*) as total FROM visitantes WHERE estado = 'activo'")
        estadisticas['total_visitantes'] = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM accesos WHERE DATE(fecha_hora) = CURDATE() AND tipo IN ('entrada', 'salida')")
        estadisticas['accesos_hoy'] = cursor.fetchone()['total']
        
        # Estadísticas según permisos del usuario actual
        if usuario_actual and 'alertas.ver_alertas' in usuario_actual['permisos']:
            cursor.execute("SELECT COUNT(*) as total FROM alertas WHERE DATE(fecha) = CURDATE()")
            estadisticas['alertas_hoy'] = cursor.fetchone()['total']
        
        if usuario_actual and 'usuarios.ver_usuarios' in usuario_actual['permisos']:
            cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE estado = 'activo'")
            estadisticas['total_usuarios'] = cursor.fetchone()['total']
        
        # Visitantes actualmente en las instalaciones
        cursor.execute("""
            SELECT COUNT(DISTINCT a1.visitante_id) as total
            FROM accesos a1
            LEFT JOIN accesos a2 ON a1.visitante_id = a2.visitante_id 
                AND a2.tipo = 'salida' 
                AND a2.fecha_hora > a1.fecha_hora
            WHERE a1.tipo = 'entrada' 
                AND a2.id IS NULL
                AND DATE(a1.fecha_hora) = CURDATE()
        """)
        estadisticas['visitantes_dentro'] = cursor.fetchone()['total']
        
        # Accesos recientes (últimos 10)
        if usuario_actual and 'acceso.ver_registro_accesos' in usuario_actual['permisos']:
            cursor.execute("""
                SELECT a.*, v.nombre as visitante_nombre, u.nombre as usuario_nombre
                FROM accesos a
                LEFT JOIN visitantes v ON a.visitante_id = v.id
                LEFT JOIN usuarios u ON a.usuario_id = u.id
                WHERE a.tipo IN ('entrada', 'salida')
                ORDER BY a.fecha_hora DESC
                LIMIT 10
            """)
            estadisticas['accesos_recientes'] = cursor.fetchall()
        
        # Alertas recientes no revisadas
        if usuario_actual and 'alertas.ver_alertas' in usuario_actual['permisos']:
            cursor.execute("""
                SELECT * FROM alertas 
                WHERE nivel IN ('alto', 'medio')
                ORDER BY fecha DESC
                LIMIT 5
            """)
            estadisticas['alertas_recientes'] = cursor.fetchall()
            
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
    finally:
        cursor.close()
        conn.close()
    
    return render_template('dashboard.html', estadisticas=estadisticas)