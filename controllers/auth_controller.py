from flask import render_template, request, redirect, url_for, session, flash
from models.database import Database
from auth.auth import registrar_intento_login, esta_bloqueado, resetear_intentos_login
import hashlib

def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        recordar = request.form.get('recordar', False)
        
        # Obtener IP del cliente para control de intentos
        client_ip = request.remote_addr
        
        # Verificar si la IP está bloqueada
        if esta_bloqueado(client_ip):
            flash('Demasiados intentos fallidos. Espere 15 minutos.', 'danger')
            return render_template('login.html')
        
        db = Database()
        conn = db.conectar()
        if not conn:
            flash('Error de conexión con el servidor', 'danger')
            return render_template('login.html')
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.*, r.nombre as rol_nombre 
                FROM usuarios u 
                JOIN roles r ON u.rol_id = r.id 
                WHERE u.correo = %s AND u.estado = 'activo'
            """, (correo,))
            
            usuario = cursor.fetchone()
            
            if usuario and db.verificar_contrasena(contrasena, usuario['contrasena']):
                # Login exitoso
                resetear_intentos_login(client_ip)
                
                session['usuario_id'] = usuario['id']
                session['usuario_nombre'] = usuario['nombre']
                session['usuario_rol_id'] = usuario['rol_id']
                session['usuario_rol'] = usuario['rol_nombre']
                
                # Configurar cookie permanente si el usuario quiere "recordar"
                if recordar:
                    session.permanent = True
                
                # Registrar login exitoso
                cursor.execute("""
                    INSERT INTO accesos (usuario_id, tipo, autorizado, fecha_hora)
                    VALUES (%s, 'login', 1, NOW())
                """, (usuario['id'],))
                
                conn.commit()
                flash(f'Bienvenido, {usuario["nombre"]}', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Login fallido
                registrar_intento_login(client_ip)
                flash('Credenciales incorrectas', 'danger')
                
        except Exception as e:
            print(f"Error en login: {e}")
            flash('Error en el servidor', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

def logout():
    # Registrar logout
    if 'usuario_id' in session:
        db = Database()
        conn = db.conectar()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO accesos (usuario_id, tipo, autorizado, fecha_hora)
                    VALUES (%s, 'logout', 1, NOW())
                """, (session['usuario_id'],))
                conn.commit()
                cursor.close()
            except:
                pass
            finally:
                conn.close()
    
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))