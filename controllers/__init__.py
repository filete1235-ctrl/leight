# controllers/__init__.py actualizado
from .auth_controller import login, logout
from .dashboard_controller import dashboard
from .visitantes_controller import (
    listar_visitantes, agregar_visitante, editar_visitante, 
    cambiar_estado_visitante
)
from .acceso_controller import control_acceso, listar_accesos
from .usuarios_controller import (
    listar_usuarios, agregar_usuario, editar_usuario, 
    cambiar_estado_usuario
)
from .roles_controller import (
    listar_roles, crear_rol, editar_rol, eliminar_rol, 
    obtener_permisos_rol
)
from .alertas_controller import (
    listar_alertas, crear_alerta, eliminar_alerta, 
    crear_alerta_automatica
)
from .reportes_controller import (
    generar_reporte, ver_reporte, exportar_reporte_csv, 
    exportar_reporte_pdf, reporte_estadisticas
)

__all__ = [
    'login', 'logout', 'dashboard',
    'listar_visitantes', 'agregar_visitante', 'editar_visitante', 'cambiar_estado_visitante',
    'control_acceso', 'listar_accesos',
    'listar_usuarios', 'agregar_usuario', 'editar_usuario', 'cambiar_estado_usuario',
    'listar_roles', 'crear_rol', 'editar_rol', 'eliminar_rol', 'obtener_permisos_rol',
    'listar_alertas', 'crear_alerta', 'eliminar_alerta', 'crear_alerta_automatica',
    'generar_reporte', 'ver_reporte', 'exportar_reporte_csv', 'exportar_reporte_pdf', 'reporte_estadisticas'
]