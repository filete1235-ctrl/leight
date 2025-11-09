"""Utilidades para el manejo de accesos"""

def normalizar_tipo_acceso(tipo: str) -> str:
    """
    Normaliza el tipo de acceso a los valores válidos del enum ('entrada', 'salida')
    
    Args:
        tipo: El tipo de acceso a normalizar (cualquier string)
        
    Returns:
        str: 'entrada' o 'salida' según corresponda
    """
    tipo = str(tipo).strip().lower()
    mapeo = {
        'entrada': 'entrada', 'ingreso': 'entrada', 'ingress': 'entrada',
        'enter': 'entrada', 'in': 'entrada', 'login': 'entrada',
        'salida': 'salida', 'egreso': 'salida', 'exit': 'salida',
        'out': 'salida', 'logout': 'salida', 'egress': 'salida'
    }
    return mapeo.get(tipo, 'entrada')  # valor por defecto seguro