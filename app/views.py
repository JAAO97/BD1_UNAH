from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import os
from .db import get_db_connection, hash_password, check_password, login_required, admin_required

def inicio(request):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, est.nombre as establecimiento_nombre
        FROM eventos e
        JOIN establecimientos est ON e.establecimiento_id = est.id
        WHERE e.activo = TRUE ORDER BY e.fecha_hora DESC
    """)
    eventos = cursor.fetchall()
    conn.close()
    return render(request, 'inicio.html', {'eventos': eventos})

def login_view(request):
    if request.method == 'POST':
        correo = request.POST['correo']
        password = request.POST['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password(usuario['password_hash'], password):
            request.session['usuario_id'] = usuario['id']
            request.session['primer_nombre'] = usuario['primer_nombre']
            request.session['rol_id'] = usuario['rol_id']
            request.session.modified = True  
            messages.success(request, '¡Bienvenido!')
            return redirect('inicio')
        messages.error(request, 'Credenciales incorrectas')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('inicio')

def registro(request):
    pass  

def detalle_evento(request, evento_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, est.nombre as establecimiento_nombre
        FROM eventos e
        JOIN establecimientos est ON e.establecimiento_id = est.id
        WHERE e.id = %s
    """, (evento_id,))
    evento = cursor.fetchone()
    cursor.execute("SELECT zona, precio FROM precios_evento WHERE evento_id = %s", (evento_id,))
    precios = {p['zona']: p['precio'] for p in cursor.fetchall()}
    conn.close()
    return render(request, 'detalle_evento.html', {'evento': evento, 'precios': precios})

@login_required
def seleccionar_asientos(request, evento_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()
    cursor.execute("""
        SELECT a.id, a.fila, a.columna, a.zona,
               IFNULL(b.asiento_id, 0) as ocupado
        FROM asientos a
        LEFT JOIN boletos b ON a.id = b.asiento_id
        LEFT JOIN compras c ON b.compra_id = c.id AND c.evento_id = %s
        WHERE a.establecimiento_id = %s
        ORDER BY a.fila, a.columna
    """, (evento_id, evento['establecimiento_id']))
    asientos = cursor.fetchall()
    conn.close()
    return render(request, 'seleccionar_asientos.html', {'evento': evento, 'asientos': asientos})

@admin_required
def crear_evento(request):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM establecimientos")
    establecimientos = cursor.fetchall()

    if request.method == 'POST':
        nombre = request.POST['nombre']
        fecha_hora = request.POST['fecha_hora']
        establecimiento_id = request.POST['establecimiento']

        cursor.execute("""
            INSERT INTO eventos (nombre, fecha_hora, establecimiento_id)
            VALUES (%s, %s, %s)
        """, (nombre, fecha_hora, establecimiento_id))
        evento_id = cursor.lastrowid

        for zona in ['vip', 'preferencial', 'general']:
            precio = request.POST.get(f'precio_{zona}')
            if precio:
                cursor.execute("INSERT INTO precios_evento (evento_id, zona, precio) VALUES (%s, %s, %s)",
                               (evento_id, zona, precio))

        conn.commit()
        conn.close()
        messages.success(request, 'Evento creado con éxito')
        return redirect('inicio')

    conn.close()
    return render(request, 'crear_evento.html', {'establecimientos': establecimientos})