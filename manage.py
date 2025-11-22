#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    # Nombre del settings que vamos a usar
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticketmaster_rd.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Estás seguro de que lo instalaste y "
            "activaste un entorno virtual? Recuerda que necesitas ejecutar "
            "'pip install -r requirements.txt' primero."
        ) from exc
    
    execute_from_command_line(sys.argv)