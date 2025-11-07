# Este archivo hace que la carpeta auth sea un paquete Python
from .auth import login_required, permiso_requerido, obtener_usuario_actual
from .permissions import *

__all__ = [
    'login_required', 
    'permiso_requerido', 
    'obtener_usuario_actual'
]