from flask import render_template, request, redirect, url_for, session, flash
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import *
from datetime import datetime

@login_required
@permiso_requerido(CONTROL_ACCESO)
def control_acceso():
    """Control de acceso - registrar entradas y salidas"""
    if request.method == 'POST':
        codigo = request.form['codigo']
        tipo = request.form['tipo']  # 'entrada' o 'salida'
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión a la base de datos', 'danger')
            return redirect(url_for('control_acceso'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Verificar credencial
            cursor.execute("""
                SELECT v.*, c.id as credencial_id 
                FROM credenciales c 
                JOIN visitantes v ON c.visitante_id = v.id 
                WHERE c.codigo = %s AND c.estado = 'activa' 
                AND (c.fecha_expiracion IS NULL OR c.fecha_expiracion > NOW())
                AND v.estado = 'activo'
            """, (codigo,))
            
            credencial = cursor.fetchone()
            
            if credencial:
                # Verificar horario (8:00 AM - 6:00 PM)
                hora_actual = datetime.now().time()
                hora_inicio = datetime.strptime('08:00', '%H:%M').time()
                hora_fin = datetime.strptime('18:00', '%H:%M').time()
                
                if hora_actual < hora_inicio or hora_actual > hora_fin:
                    # Registrar acceso no autorizado por horario
                    cursor.execute("""
                        INSERT INTO accesos (usuario_id, visitante_id, tipo, autorizado)
                        VALUES (%s, %s, %s, %s)
                    """, (session['usuario_id'], credencial['id'], tipo, 0))
                    
                    # Registrar alerta
                    cursor.execute("""
                        INSERT INTO alertas (descripcion, nivel, usuario_id, visitante_id)
                        VALUES (%s, %s, %s, %s)
                    """, (f'Intento de acceso fuera de horario: {credencial["nombre"]}', 'medio', session['usuario_id'], credencial['id']))
                    
                    conn.commit()
                    flash(f'Acceso denegado: Fuera del horario permitido (8:00 AM - 6:00 PM)', 'warning')
                else:
                    # Registrar acceso autorizado
                    cursor.execute("""
                        INSERT INTO accesos (usuario_id, visitante_id, tipo, autorizado)
                        VALUES (%s, %s, %s, %s)
                    """, (session['usuario_id'], credencial['id'], tipo, 1))
                    
                    # Si es salida, desactivar credencial
                    if tipo == 'salida':
                        cursor.execute("UPDATE credenciales SET estado = 'inactiva' WHERE id = %s", (credencial['credencial_id'],))
                    
                    conn.commit()
                    flash(f'Acceso registrado: {credencial["nombre"]} ({tipo})', 'success')
            else:
                # Registrar intento de acceso no autorizado
                cursor.execute("""
                    INSERT INTO alertas (descripcion, nivel, usuario_id)
                    VALUES (%s, %s, %s)
                """, (f'Intento de acceso con código inválido: {codigo}', 'alto', session['usuario_id']))
                
                conn.commit()
                flash('Código inválido, expirado o visitante inactivo', 'danger')
            
            cursor.close()
            conn.close()
            return redirect(url_for('control_acceso'))
            
        except Exception as e:
            conn.rollback()
            print(f"Error en control de acceso: {e}")
            flash('Error al procesar el acceso', 'danger')
            return redirect(url_for('control_acceso'))
    
    return render_template('acceso/control.html')

@login_required
@permiso_requerido(VER_REGISTRO_ACCESOS)
def listar_accesos():
    """Listar historial de accesos"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('acceso/listar.html', accesos=[])
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener parámetros de filtrado
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        tipo = request.args.get('tipo', '')
        autorizado = request.args.get('autorizado', '')
        
        # Construir consulta base
        query = """
            SELECT a.*, v.nombre as visitante_nombre, u.nombre as usuario_nombre
            FROM accesos a
            LEFT JOIN visitantes v ON a.visitante_id = v.id
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.tipo IN ('entrada', 'salida')
        """
        params = []
        
        # Aplicar filtros
        if fecha_desde:
            query += " AND DATE(a.fecha_hora) >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND DATE(a.fecha_hora) <= %s"
            params.append(fecha_hasta)
        
        if tipo:
            query += " AND a.tipo = %s"
            params.append(tipo)
        
        if autorizado:
            query += " AND a.autorizado = %s"
            params.append(1 if autorizado == 'si' else 0)
        
        query += " ORDER BY a.fecha_hora DESC"
        
        cursor.execute(query, params)
        accesos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('acceso/listar.html', 
                             accesos=accesos,
                             fecha_desde=fecha_desde,
                             fecha_hasta=fecha_hasta,
                             tipo_seleccionado=tipo,
                             autorizado_seleccionado=autorizado)
        
    except Exception as e:
        print(f"Error al listar accesos: {e}")
        flash('Error al cargar el historial de accesos', 'danger')
        return render_template('acceso/listar.html', accesos=[])