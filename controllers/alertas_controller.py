from flask import render_template, request, redirect, url_for, session, flash
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import VER_ALERTAS, CREAR_ALERTAS, EDITAR_ALERTAS, ELIMINAR_ALERTAS
from datetime import datetime

@login_required
@permiso_requerido(VER_ALERTAS)
def listar_alertas():
    """Listar todas las alertas del sistema"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('alertas/listar.html', alertas=[])
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener parámetros de filtrado
        nivel = request.args.get('nivel', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        
        # Construir consulta base
        query = """
            SELECT a.*, u.nombre as usuario_nombre, v.nombre as visitante_nombre
            FROM alertas a
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN visitantes v ON a.visitante_id = v.id
            WHERE 1=1
        """
        params = []
        
        # Aplicar filtros
        if nivel:
            query += " AND a.nivel = %s"
            params.append(nivel)
        
        if fecha_desde:
            query += " AND DATE(a.fecha) >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND DATE(a.fecha) <= %s"
            params.append(fecha_hasta)
        
        query += " ORDER BY a.fecha DESC"
        
        cursor.execute(query, params)
        alertas = cursor.fetchall()
        
        # Obtener estadísticas de alertas
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN nivel = 'alto' THEN 1 ELSE 0 END) as altas,
                SUM(CASE WHEN nivel = 'medio' THEN 1 ELSE 0 END) as medias,
                SUM(CASE WHEN nivel = 'bajo' THEN 1 ELSE 0 END) as bajas
            FROM alertas 
            WHERE DATE(fecha) = CURDATE()
        """)
        estadisticas = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('alertas/listar.html', 
                             alertas=alertas,
                             estadisticas=estadisticas,
                             nivel_seleccionado=nivel,
                             fecha_desde=fecha_desde,
                             fecha_hasta=fecha_hasta)
        
    except Exception as e:
        print(f"Error al listar alertas: {e}")
        flash('Error al cargar las alertas del sistema', 'danger')
        return render_template('alertas/listar.html', alertas=[])

@login_required
@permiso_requerido(CREAR_ALERTAS)
def crear_alerta():
    """Crear una nueva alerta manualmente"""
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        nivel = request.form['nivel']
        visitante_id = request.form.get('visitante_id') or None
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión a la base de datos', 'danger')
            return redirect(url_for('listar_alertas'))
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO alertas (descripcion, nivel, usuario_id, visitante_id)
                VALUES (%s, %s, %s, %s)
            """, (descripcion, nivel, session['usuario_id'], visitante_id))
            
            conn.commit()
            flash('Alerta creada exitosamente', 'success')
            
        except Exception as e:
            conn.rollback()
            flash(f'Error al crear alerta: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('listar_alertas'))
    
    # Obtener visitantes para el formulario
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_alertas'))
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM visitantes WHERE estado = 'activo' ORDER BY nombre")
    visitantes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('alertas/crear.html', visitantes=visitantes)

@login_required
@permiso_requerido(ELIMINAR_ALERTAS)
def eliminar_alerta(id):
    """Eliminar una alerta"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_alertas'))
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la alerta existe
        cursor.execute("SELECT id FROM alertas WHERE id = %s", (id,))
        if not cursor.fetchone():
            flash('Alerta no encontrada', 'danger')
            return redirect(url_for('listar_alertas'))
        
        cursor.execute("DELETE FROM alertas WHERE id = %s", (id,))
        conn.commit()
        
        flash('Alerta eliminada exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar alerta: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('listar_alertas'))

def crear_alerta_automatica(descripcion, nivel='medio', usuario_id=None, visitante_id=None):
    """Función para crear alertas automáticamente desde otros módulos"""
    db = Database()
    conn = db.conectar()
    if not conn:
        print("Error: No se pudo conectar a la base de datos para crear alerta")
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alertas (descripcion, nivel, usuario_id, visitante_id)
            VALUES (%s, %s, %s, %s)
        """, (descripcion, nivel, usuario_id, visitante_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creando alerta automática: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()