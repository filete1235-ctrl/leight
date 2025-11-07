from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import GESTIONAR_ROLES, GESTIONAR_PERMISOS

@login_required
@permiso_requerido(GESTIONAR_ROLES)
def listar_roles():
    """Listar todos los roles del sistema"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('roles/listar.html', roles=[], permisos=[])
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener roles con conteo de usuarios
        cursor.execute("""
            SELECT 
                r.*, 
                COUNT(u.id) as total_usuarios,
                COUNT(rp.permiso_id) as total_permisos
            FROM roles r
            LEFT JOIN usuarios u ON r.id = u.rol_id AND u.estado = 'activo'
            LEFT JOIN rol_permisos rp ON r.id = rp.rol_id
            GROUP BY r.id
            ORDER BY r.nombre
        """)
        
        roles = cursor.fetchall()
        
        # Obtener todos los permisos disponibles
        cursor.execute("""
            SELECT p.*, m.nombre as modulo_nombre
            FROM permisos p
            ORDER BY p.modulo, p.nombre
        """)
        permisos = cursor.fetchall()
        
        # Para cada rol, obtener sus permisos asignados
        for rol in roles:
            cursor.execute("""
                SELECT p.id, p.nombre, p.modulo, p.descripcion
                FROM permisos p
                JOIN rol_permisos rp ON p.id = rp.permiso_id
                WHERE rp.rol_id = %s
                ORDER BY p.modulo, p.nombre
            """, (rol['id'],))
            rol['permisos_asignados'] = [p['id'] for p in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return render_template('roles/listar.html', 
                             roles=roles, 
                             permisos=permisos)
        
    except Exception as e:
        print(f"Error al listar roles: {e}")
        flash('Error al cargar los roles del sistema', 'danger')
        return render_template('roles/listar.html', roles=[], permisos=[])

@login_required
@permiso_requerido(GESTIONAR_ROLES)
def crear_rol():
    """Crear un nuevo rol"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        permisos = request.form.getlist('permisos')
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión a la base de datos', 'danger')
            return redirect(url_for('listar_roles'))
        
        try:
            cursor = conn.cursor()
            
            # Insertar nuevo rol
            cursor.execute("""
                INSERT INTO roles (nombre, descripcion)
                VALUES (%s, %s)
            """, (nombre, descripcion))
            
            rol_id = cursor.lastrowid
            
            # Asignar permisos seleccionados
            for permiso_id in permisos:
                cursor.execute("""
                    INSERT INTO rol_permisos (rol_id, permiso_id)
                    VALUES (%s, %s)
                """, (rol_id, permiso_id))
            
            conn.commit()
            flash('Rol creado exitosamente', 'success')
            
        except Exception as e:
            conn.rollback()
            if 'nombre' in str(e).lower():
                flash('Ya existe un rol con ese nombre', 'danger')
            else:
                flash(f'Error al crear rol: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('listar_roles'))
    
    # Obtener permisos disponibles
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_roles'))
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM permisos ORDER BY modulo, nombre")
    permisos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('roles/crear.html', permisos=permisos)

@login_required
@permiso_requerido(GESTIONAR_ROLES)
def editar_rol(id):
    """Editar un rol existente"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_roles'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            permisos = request.form.getlist('permisos')
            
            try:
                # Actualizar rol
                cursor.execute("""
                    UPDATE roles 
                    SET nombre = %s, descripcion = %s
                    WHERE id = %s
                """, (nombre, descripcion, id))
                
                # Eliminar permisos actuales
                cursor.execute("DELETE FROM rol_permisos WHERE rol_id = %s", (id,))
                
                # Asignar nuevos permisos
                for permiso_id in permisos:
                    cursor.execute("""
                        INSERT INTO rol_permisos (rol_id, permiso_id)
                        VALUES (%s, %s)
                    """, (id, permiso_id))
                
                conn.commit()
                flash('Rol actualizado exitosamente', 'success')
                
            except Exception as e:
                conn.rollback()
                if 'nombre' in str(e).lower():
                    flash('Ya existe un rol con ese nombre', 'danger')
                else:
                    flash(f'Error al actualizar rol: {str(e)}', 'danger')
            
            return redirect(url_for('listar_roles'))
        
        # Obtener datos del rol
        cursor.execute("SELECT * FROM roles WHERE id = %s", (id,))
        rol = cursor.fetchone()
        
        if not rol:
            flash('Rol no encontrado', 'danger')
            return redirect(url_for('listar_roles'))
        
        # Obtener permisos asignados al rol
        cursor.execute("""
            SELECT permiso_id 
            FROM rol_permisos 
            WHERE rol_id = %s
        """, (id,))
        permisos_asignados = [row['permiso_id'] for row in cursor.fetchall()]
        
        # Obtener todos los permisos disponibles
        cursor.execute("SELECT * FROM permisos ORDER BY modulo, nombre")
        permisos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('roles/editar.html', 
                             rol=rol, 
                             permisos=permisos,
                             permisos_asignados=permisos_asignados)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('listar_roles'))

@login_required
@permiso_requerido(GESTIONAR_ROLES)
def eliminar_rol(id):
    """Eliminar un rol"""
    # No permitir eliminar roles del sistema básicos
    if id in [1, 2, 3, 4]:  # IDs de administrador, guardia, recepción, supervisor
        flash('No se pueden eliminar los roles del sistema básicos', 'danger')
        return redirect(url_for('listar_roles'))
    
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_roles'))
    
    try:
        cursor = conn.cursor()
        
        # Verificar si hay usuarios con este rol
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol_id = %s", (id,))
        usuarios_con_rol = cursor.fetchone()['total']
        
        if usuarios_con_rol > 0:
            flash(f'No se puede eliminar el rol porque tiene {usuarios_con_rol} usuario(s) asignado(s)', 'danger')
            return redirect(url_for('listar_roles'))
        
        # Eliminar permisos del rol
        cursor.execute("DELETE FROM rol_permisos WHERE rol_id = %s", (id,))
        
        # Eliminar el rol
        cursor.execute("DELETE FROM roles WHERE id = %s", (id,))
        
        conn.commit()
        flash('Rol eliminado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar rol: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('listar_roles'))

@login_required
@permiso_requerido(GESTIONAR_ROLES)
def obtener_permisos_rol(id):
    """API para obtener los permisos de un rol (AJAX)"""
    db = Database()
    conn = db.conectar()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.id, p.nombre, p.modulo, p.descripcion
            FROM permisos p
            JOIN rol_permisos rp ON p.id = rp.permiso_id
            WHERE rp.rol_id = %s
            ORDER BY p.modulo, p.nombre
        """, (id,))
        
        permisos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(permisos)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500