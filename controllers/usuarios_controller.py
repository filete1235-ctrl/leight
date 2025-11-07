from flask import render_template, request, redirect, url_for, session, flash
from models.database import Database
from auth.auth import login_required, permiso_requerido
from auth.permissions import *

@login_required
@permiso_requerido(VER_USUARIOS)
def listar_usuarios():
    """Listar todos los usuarios del sistema"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('usuarios/listar.html', usuarios=[], roles=[])
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.*, r.nombre as rol_nombre, r.descripcion as rol_descripcion
            FROM usuarios u 
            JOIN roles r ON u.rol_id = r.id 
            ORDER BY u.fecha_creacion DESC
        """)
        
        usuarios = cursor.fetchall()
        
        # Obtener lista de roles para el formulario
        cursor.execute("SELECT * FROM roles ORDER BY nombre")
        roles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('usuarios/listar.html', usuarios=usuarios, roles=roles)
        
    except Exception as e:
        print(f"Error al listar usuarios: {e}")
        flash('Error al cargar la lista de usuarios', 'danger')
        return render_template('usuarios/listar.html', usuarios=[], roles=[])

@login_required
@permiso_requerido(CREAR_USUARIOS)
def agregar_usuario():
    """Agregar nuevo usuario al sistema"""
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        rol_id = request.form['rol_id']
        estado = request.form.get('estado', 'activo')
        
        # Validaciones básicas
        if len(contrasena) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('agregar_usuario'))
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión a la base de datos', 'danger')
            return redirect(url_for('agregar_usuario'))
        
        try:
            cursor = conn.cursor()
            contrasena_hash = db.hash_contrasena(contrasena)
            
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, contrasena, rol_id, estado)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, correo, contrasena_hash, rol_id, estado))
            
            conn.commit()
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('listar_usuarios'))
            
        except Exception as e:
            conn.rollback()
            if 'correo' in str(e).lower():
                flash('El correo electrónico ya está registrado', 'danger')
            else:
                flash(f'Error al crear usuario: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    # Obtener roles para el formulario
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM roles ORDER BY nombre")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('usuarios/agregar.html', roles=roles)

@login_required
@permiso_requerido(EDITAR_USUARIOS)
def editar_usuario(id):
    """Editar usuario existente"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            correo = request.form['correo']
            rol_id = request.form['rol_id']
            estado = request.form.get('estado', 'activo')
            cambiar_contrasena = request.form.get('cambiar_contrasena')
            
            try:
                if cambiar_contrasena:
                    contrasena = request.form['contrasena']
                    if len(contrasena) < 8:
                        flash('La contraseña debe tener al menos 8 caracteres', 'danger')
                        return redirect(url_for('editar_usuario', id=id))
                    
                    contrasena_hash = db.hash_contrasena(contrasena)
                    cursor.execute("""
                        UPDATE usuarios 
                        SET nombre=%s, correo=%s, contrasena=%s, rol_id=%s, estado=%s
                        WHERE id=%s
                    """, (nombre, correo, contrasena_hash, rol_id, estado, id))
                else:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET nombre=%s, correo=%s, rol_id=%s, estado=%s
                        WHERE id=%s
                    """, (nombre, correo, rol_id, estado, id))
                
                conn.commit()
                flash('Usuario actualizado exitosamente', 'success')
                return redirect(url_for('listar_usuarios'))
                
            except Exception as e:
                conn.rollback()
                flash(f'Error al actualizar usuario: {str(e)}', 'danger')
        
        # Obtener datos del usuario y roles
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        
        cursor.execute("SELECT * FROM roles ORDER BY nombre")
        roles = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('listar_usuarios'))
        
        return render_template('usuarios/editar.html', usuario=usuario, roles=roles)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('listar_usuarios'))

@login_required
@permiso_requerido(CAMBIAR_ESTADO_USUARIOS)
def cambiar_estado_usuario(id):
    """Activar/desactivar usuario"""
    db = Database()
    conn = db.conectar()
    if not conn:
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('listar_usuarios'))
        
        nuevo_estado = 'inactivo' if usuario['estado'] == 'activo' else 'activo'
        
        cursor.execute("UPDATE usuarios SET estado = %s WHERE id = %s", (nuevo_estado, id))
        conn.commit()
        
        accion = "desactivado" if nuevo_estado == 'inactivo' else "activado"
        flash(f'Usuario {accion} exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al cambiar estado del usuario: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('listar_usuarios'))