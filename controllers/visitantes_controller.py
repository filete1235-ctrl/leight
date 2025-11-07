from flask import render_template, request, redirect, url_for, session, flash
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import *
import uuid
from datetime import datetime, timedelta

@login_required
@permiso_requerido(VER_VISITANTES)
def listar_visitantes():
    """Listar todos los visitantes"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('visitantes/listar.html', visitantes=[])
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener parámetros de filtrado
        estado = request.args.get('estado', 'activo')
        buscar = request.args.get('buscar', '')
        
        # Construir consulta base
        query = """
            SELECT v.*, 
                   c.codigo,
                   c.estado as credencial_estado,
                   (SELECT COUNT(*) FROM accesos WHERE visitante_id = v.id AND tipo = 'entrada') as total_visitas
            FROM visitantes v
            LEFT JOIN credenciales c ON v.id = c.visitante_id AND c.estado = 'activa'
            WHERE 1=1
        """
        params = []
        
        # Aplicar filtros
        if estado:
            query += " AND v.estado = %s"
            params.append(estado)
        
        if buscar:
            query += " AND (v.nombre LIKE %s OR v.identificacion LIKE %s OR v.empresa LIKE %s)"
            params.extend([f'%{buscar}%', f'%{buscar}%', f'%{buscar}%'])
        
        query += " ORDER BY v.fecha_registro DESC"
        
        cursor.execute(query, params)
        visitantes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('visitantes/listar.html', 
                             visitantes=visitantes,
                             estado_seleccionado=estado,
                             buscar=buscar)
        
    except Exception as e:
        print(f"Error al listar visitantes: {e}")
        flash('Error al cargar la lista de visitantes', 'danger')
        return render_template('visitantes/listar.html', visitantes=[])

@login_required
@permiso_requerido(CREAR_VISITANTES)
def agregar_visitante():
    """Agregar nuevo visitante"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        identificacion = request.form['identificacion']
        empresa = request.form['empresa']
        motivo = request.form['motivo']
        generar_credencial = request.form.get('generar_credencial', 'no')
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión a la base de datos', 'danger')
            return redirect(url_for('agregar_visitante'))
        
        try:
            cursor = conn.cursor()
            
            # Insertar visitante
            cursor.execute("""
                INSERT INTO visitantes (nombre, identificacion, empresa, motivo, estado)
                VALUES (%s, %s, %s, %s, 'activo')
            """, (nombre, identificacion, empresa, motivo))
            
            visitante_id = cursor.lastrowid
            
            # Generar credencial si se solicitó
            if generar_credencial == 'si':
                codigo = str(uuid.uuid4())[:8].upper()
                fecha_expiracion = datetime.now() + timedelta(hours=8)
                
                cursor.execute("""
                    INSERT INTO credenciales (visitante_id, codigo, estado, fecha_expiracion)
                    VALUES (%s, %s, 'activa', %s)
                """, (visitante_id, codigo, fecha_expiracion))
                
                flash(f'Visitante registrado exitosamente. Credencial generada: {codigo}', 'success')
            else:
                flash('Visitante registrado exitosamente', 'success')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return redirect(url_for('listar_visitantes'))
            
        except Exception as e:
            conn.rollback()
            if 'identificacion' in str(e).lower():
                flash('La identificación ya está registrada', 'danger')
            else:
                flash(f'Error al registrar visitante: {str(e)}', 'danger')
            return redirect(url_for('agregar_visitante'))
    
    return render_template('visitantes/agregar.html')

@login_required
@permiso_requerido(EDITAR_VISITANTES)
def editar_visitante(id):
    """Editar visitante existente"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_visitantes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            identificacion = request.form['identificacion']
            empresa = request.form['empresa']
            motivo = request.form['motivo']
            
            cursor.execute("""
                UPDATE visitantes 
                SET nombre=%s, identificacion=%s, empresa=%s, motivo=%s
                WHERE id=%s
            """, (nombre, identificacion, empresa, motivo, id))
            
            conn.commit()
            flash('Visitante actualizado exitosamente', 'success')
            return redirect(url_for('listar_visitantes'))
        
        # Obtener datos del visitante
        cursor.execute("SELECT * FROM visitantes WHERE id = %s", (id,))
        visitante = cursor.fetchone()
        
        if not visitante:
            flash('Visitante no encontrado', 'danger')
            return redirect(url_for('listar_visitantes'))
        
        cursor.close()
        conn.close()
        
        return render_template('visitantes/editar.html', visitante=visitante)
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar visitante: {str(e)}', 'danger')
        return redirect(url_for('listar_visitantes'))

@login_required
@permiso_requerido(CAMBIAR_ESTADO_VISITANTES)
def cambiar_estado_visitante(id):
    """Activar/desactivar visitante"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_visitantes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM visitantes WHERE id = %s", (id,))
        visitante = cursor.fetchone()
        
        if not visitante:
            flash('Visitante no encontrado', 'danger')
            return redirect(url_for('listar_visitantes'))
        
        nuevo_estado = 'inactivo' if visitante['estado'] == 'activo' else 'activo'
        
        cursor.execute("UPDATE visitantes SET estado = %s WHERE id = %s", (nuevo_estado, id))
        
        # Desactivar credenciales activas si se desactiva el visitante
        if nuevo_estado == 'inactivo':
            cursor.execute("UPDATE credenciales SET estado = 'inactiva' WHERE visitante_id = %s AND estado = 'activa'", (id,))
        
        conn.commit()
        
        accion = "desactivado" if nuevo_estado == 'inactivo' else "activado"
        flash(f'Visitante {accion} exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al cambiar estado del visitante: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('listar_visitantes'))