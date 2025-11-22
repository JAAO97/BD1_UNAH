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
            # FORZAMOS TODO
            request.session['usuario_id'] = usuario['id']
            request.session['primer_nombre'] = usuario['primer_nombre']
            request.session['rol_id'] = usuario['rol_id']  # <-- ESTO ES LO QUE FALLABA
            request.session['is_admin'] = True if usuario['rol_id'] == 2 else False
            request.session.modified = True  # <-- FORZAR QUE GUARDE LA SESIÓN
            messages.success(request, '¡Bienvenido administrador!')
            return redirect('inicio')
        else:
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
    
    # Obtener el evento
    cursor.execute("""
        SELECT e.*, est.nombre as establecimiento_nombre
        FROM eventos e
        JOIN establecimientos est ON e.establecimiento_id = est.id
        WHERE e.id = %s
    """, (evento_id,))
    evento = cursor.fetchone()
    
    if not evento:
        conn.close()
        messages.error(request, "Evento no encontrado")
        return redirect('inicio')
    
    # Obtener precios por zona
    cursor.execute("SELECT zona, precio FROM precios_evento WHERE evento_id = %s", (evento_id,))
    precios_raw = cursor.fetchall()
    precios = {p['zona']: p['precio'] for p in precios_raw}
    conn.close()
    
    # Procesar compra rápida
    if request.method == 'POST':
        try:
            vip = int(request.POST.get('cantidad_vip', 0))
            preferencial = int(request.POST.get('cantidad_preferencial', 0))
            general = int(request.POST.get('cantidad_general', 0))
            
            total_boletos = vip + preferencial + general
            
            if total_boletos == 0:
                messages.error(request, "Por favor selecciona al menos un boleto")
            else:
                total = (vip * precios.get('vip', 0) +
                         preferencial * precios.get('preferencial', 0) +
                         general * precios.get('general', 0))
                
                messages.success(request, 
                    f"¡Excelente elección!\n"
                    f"Has seleccionado {total_boletos} boleto(s):\n"
                    f"• VIP: {vip} × L{precios.get('vip', 0):,}\n"
                    f"• Preferencial: {preferencial} × L{precios.get('preferencial', 0):,}\n"
                    f"• General: {general} × L{precios.get('general', 0):,}\n\n"
                    f"Total a pagar: L{total:,}\n\n"
                    f"Para completar tu compra, envía el comprobante de transferencia a:\n"
                    f"Banco Ficohsa - Cuenta: 1234-5678-90\n"
                    f"A nombre de Jeser Amaya\n"
                    f"y escribe a jeser.amaya@unah.hn con tu comprobante.\n"
                    f"¡Gracias por confiar en JAAO Tickets!"
                )
        except:
            messages.error(request, "Error en la selección de boletos")
    
    return render(request, 'detalle_evento.html', {
        'evento': evento,
        'precios': precios
    })

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

        # SUBIR FOTO
        imagen_portada = None
        if 'portada' in request.FILES:
            portada = request.FILES['portada']
            filename = f"eventos/{portada.name}"
            path = os.path.join(settings.MEDIA_ROOT, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb+') as destino:
                for chunk in portada.chunks():
                    destino.write(chunk)
            imagen_portada = filename

        cursor.execute("""
            INSERT INTO eventos (nombre, fecha_hora, establecimiento_id, imagen_portada, activo)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (nombre, fecha_hora, establecimiento_id, imagen_portada))
        evento_id = cursor.lastrowid

        # Precios por zona
        for zona in ['vip', 'preferencial', 'general']:
            precio = request.POST.get(f'precio_{zona}')
            if precio and precio.isdigit():
                cursor.execute("INSERT INTO precios_evento (evento_id, zona, precio) VALUES (%s, %s, %s)",
                               (evento_id, zona, precio))

        conn.commit()
        conn.close()
        messages.success(request, '¡Evento creado con éxito y foto subida!')
        return redirect('inicio')

    conn.close()
    return render(request, 'crear_evento.html', {'establecimientos': establecimientos})

def borrar_evento(request, evento_id):
    if not request.session.get('is_admin') and request.session.get('rol_id') != 2:
        messages.error(request, "No tienes permiso")
        return redirect('inicio')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))
    conn.commit()
    conn.close()
    messages.success(request, "Evento eliminado con éxito")
    return redirect('inicio')