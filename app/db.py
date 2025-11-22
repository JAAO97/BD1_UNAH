import mysql.connector
import bcrypt
from django.contrib import messages
from django.shortcuts import redirect

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='123456789',
        database='ticketmaster_rd',
        charset='utf8mb4'
    )

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            messages.error(request, 'Debes iniciar sesión')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            messages.error(request, 'Debes iniciar sesión')
            return redirect('login')
        if request.session.get('rol_id') != 2:
            messages.error(request, 'Acceso denegado')
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return wrapper