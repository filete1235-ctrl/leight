"""Utilidades de caché para mejorar el rendimiento"""
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json

# Cache en memoria simple
_cache = {}

def cache_key(prefix, *args, **kwargs):
    """Genera una clave única para el caché basada en los argumentos"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return hashlib.md5(":".join(key_parts).encode()).hexdigest()

def cache_for(seconds=300):
    """
    Decorator para cachear resultados de funciones
    
    Args:
        seconds: Tiempo en segundos que el resultado permanecerá en caché
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Verificar si existe en caché y no ha expirado
            if key in _cache:
                result, expire_time = _cache[key]
                if datetime.now() < expire_time:
                    return result
                
            # Si no está en caché o expiró, ejecutar función
            result = func(*args, **kwargs)
            
            # Almacenar en caché con tiempo de expiración
            expire_time = datetime.now() + timedelta(seconds=seconds)
            _cache[key] = (result, expire_time)
            
            return result
        return wrapper
    return decorator

def clear_cache():
    """Limpia todo el caché"""
    global _cache
    _cache = {}