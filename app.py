from flask import Flask, render_template
from auth.auth import login_required, obtener_usuario_actual
from controllers import (
    auth_controller, dashboard_controller, visitantes_controller, 
    acceso_controller, usuarios_controller, alertas_controller, 
    reportes_controller, roles_controller
)
import os
from datetime import timedelta

app = Flask(__name__)

# Cargar configuración (si existe) antes de asignar claves/cookies
try:
    app.config.from_pyfile('config.py')
except Exception:
    print("⚠️  Config.py no encontrado, usando configuración por defecto")

# Establecer secret key consistente: prioridad a la variable de entorno, luego a config.py, luego valor por defecto
app.secret_key = os.environ.get('SECRET_KEY', app.config.get('SECRET_KEY', 'clave_secreta_super_segura_mejorada_2024'))
# Configurar duración de sesión usando la configuración (si fue sobrescrita en config.py)
app.config['PERMANENT_SESSION_LIFETIME'] = app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=24))

# Context processor para inyectar usuario actual en todas las plantillas
@app.context_processor
def inject_user():
    return dict(usuario_actual=obtener_usuario_actual())

# Nota: no forzamos session.permanent aquí para no sobrescribir la preferencia del usuario

# ==================== RUTAS DE AUTENTICACIÓN ====================
app.add_url_rule('/', view_func=auth_controller.login, methods=['GET', 'POST'])
app.add_url_rule('/login', view_func=auth_controller.login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=auth_controller.logout)

# ==================== RUTAS DEL DASHBOARD ====================
app.add_url_rule('/dashboard', view_func=dashboard_controller.dashboard)

# ==================== RUTAS DE VISITANTES ====================
app.add_url_rule('/visitantes', view_func=visitantes_controller.listar_visitantes)
app.add_url_rule('/visitantes/agregar', view_func=visitantes_controller.agregar_visitante, methods=['GET', 'POST'])
app.add_url_rule('/visitantes/editar/<int:id>', view_func=visitantes_controller.editar_visitante, methods=['GET', 'POST'])
app.add_url_rule('/visitantes/estado/<int:id>', view_func=visitantes_controller.cambiar_estado_visitante)

# ==================== RUTAS DE CONTROL DE ACCESO ====================
app.add_url_rule('/control_acceso', view_func=acceso_controller.control_acceso, methods=['GET', 'POST'])
app.add_url_rule('/accesos', view_func=acceso_controller.listar_accesos)

# ==================== RUTAS DE USUARIOS ====================
app.add_url_rule('/usuarios', view_func=usuarios_controller.listar_usuarios)
app.add_url_rule('/usuarios/agregar', view_func=usuarios_controller.agregar_usuario, methods=['GET', 'POST'])
app.add_url_rule('/usuarios/editar/<int:id>', view_func=usuarios_controller.editar_usuario, methods=['GET', 'POST'])
app.add_url_rule('/usuarios/estado/<int:id>', view_func=usuarios_controller.cambiar_estado_usuario)

# ==================== RUTAS DE ROLES ====================
app.add_url_rule('/roles', view_func=roles_controller.listar_roles)
app.add_url_rule('/roles/crear', view_func=roles_controller.crear_rol, methods=['GET', 'POST'])
app.add_url_rule('/roles/editar/<int:id>', view_func=roles_controller.editar_rol, methods=['GET', 'POST'])
app.add_url_rule('/roles/eliminar/<int:id>', view_func=roles_controller.eliminar_rol)
app.add_url_rule('/roles/permisos/<int:id>', view_func=roles_controller.obtener_permisos_rol)

# ==================== RUTAS DE ALERTAS ====================
app.add_url_rule('/alertas', view_func=alertas_controller.listar_alertas)
app.add_url_rule('/alertas/crear', view_func=alertas_controller.crear_alerta, methods=['GET', 'POST'])
app.add_url_rule('/alertas/eliminar/<int:id>', view_func=alertas_controller.eliminar_alerta)

# ==================== RUTAS DE REPORTES ====================
app.add_url_rule('/reportes', view_func=reportes_controller.generar_reporte, methods=['GET', 'POST'])
app.add_url_rule('/reportes/ver', view_func=reportes_controller.ver_reporte)
app.add_url_rule('/reportes/exportar/csv', view_func=reportes_controller.exportar_reporte_csv)
app.add_url_rule('/reportes/exportar/pdf', view_func=reportes_controller.exportar_reporte_pdf)
app.add_url_rule('/reportes/estadisticas', view_func=reportes_controller.reporte_estadisticas)

# ==================== MANEJO DE ERRORES ====================
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def acceso_denegado(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def error_interno(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    print("🚀 Iniciando Sistema de Control de Acceso...")
    print("📊 Base de datos configurada")
    print("🔐 Sistema de autenticación listo")
    print("🍪 Cookies configuradas (24 horas)")
    print("🌐 Servidor iniciado en http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
