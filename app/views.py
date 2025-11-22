# app/views.py  <-- VERSIÓN FINAL 100% FUNCIONAL
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
    return render(request, 'inicio.html', {'eventos': eventos, 'session': request.session})

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
            messages.success(request, f'Bienvenido {usuario["primer_nombre"]}')
            return redirect('inicio')
        else:
            messages.error(request, 'Credenciales incorrectas')

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('inicio')

def registro(request):
    if request.method == 'POST':
        dni = request.POST['dni'].replace('-', '').replace('.', '')
        if len(dni) != 13:
            messages.error(request, 'DNI debe tener 13 dígitos')
            return render(request, 'registro.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(request.POST['password'])
            cursor.execute("""
                INSERT INTO usuarios (primer_nombre, primer_apellido, telefono, correo, dni, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                request.POST['primer_nombre'],
                request.POST['primer_apellido'],
                request.POST['telefono'],
                request.POST['correo'],
                dni,
                password_hash
            ))
            conn.commit()
            messages.success(request, 'Registro exitoso')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        finally:
            conn.close()

    return render(request, 'registro.html')

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
        SELECT a.*, IF(b.asiento_id IS NOT NULL, 1, 0) as ocupado
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
    return render(request, 'crear_evento.html')