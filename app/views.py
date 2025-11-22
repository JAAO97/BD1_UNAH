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
            messages.success(request, '¡Bienvenido!')
            return redirect('inicio')
        messages.error(request, 'Credenciales incorrectas')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('inicio')

def registro(request):
    if request.method == 'POST':
        dni = request.POST['dni'].replace('-', '').replace('.', '')
        if len(dni) != 13:
            messages.error(request, 'El DNI debe tener 13 dígitos')
            return render(request, 'registro.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(request.POST['password'])
            cursor.execute("""
                INSERT INTO usuarios 
                (primer_nombre, primer_apellido, telefono, correo, dni, password_hash)
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
            messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión')
            conn.close()
            return redirect('login')
        except mysql.connector.Error as err:
            messages.error(request, f'Error: {err.msg}')
            conn.close()
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
            conn.close()
        pass
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
    
    if not evento:
        conn.close()
        messages.error(request, "Evento no encontrado")
        return redirect('inicio')
  
    cursor.execute("SELECT zona, precio FROM precios_evento WHERE evento_id = %s", (evento_id,))
    precios_raw = cursor.fetchall()
    precios = {p['zona']: p['precio'] for p in precios_raw}
    conn.close()
    

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
    pass

@admin_required
def crear_evento(request):
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.session.get('rol_id') != 2:
        messages.error(request, "Solo administradores pueden crear eventos")
        return redirect('inicio')    

    cursor.execute("SELECT id, nombre FROM establecimientos ORDER BY nombre")
    establecimientos = cursor.fetchall()
    
    if request.method == 'POST':
   
        nuevo_establecimiento = request.POST.get('nuevo_establecimiento')
        establecimiento_id = request.POST.get('establecimiento')
        
        if nuevo_establecimiento:
            cursor.execute("INSERT INTO establecimientos (nombre, descripcion, layout_type, filas, columnas) VALUES (%s, 'Creado por admin', 'rectangular', 15, 10)", (nuevo_establecimiento,))
            establecimiento_id = cursor.lastrowid
            messages.success(request, f"Nuevo establecimiento '{nuevo_establecimiento}' creado")
        elif not establecimiento_id:
            messages.error(request, "Selecciona o crea un establecimiento")
            conn.close()
            return render(request, 'crear_evento.html', {'establecimientos': establecimientos})
        
        nombre = request.POST['nombre']
        fecha_hora = request.POST['fecha_hora']
        
   
        imagen_portada = None
        if 'portada' in request.FILES:
            portada = request.FILES['portada']
            filename = f"eventos/{portada.name}"
            path = os.path.join(settings.MEDIA_ROOT, filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb+') as f:
                for chunk in portada.chunks():
                    f.write(chunk)
            imagen_portada = filename
        
        cursor.execute("""
            INSERT INTO eventos (nombre, fecha_hora, establecimiento_id, imagen_portada, activo)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (nombre, fecha_hora, establecimiento_id, imagen_portada))
        evento_id = cursor.lastrowid
        

        for zona in ['vip', 'preferencial', 'general']:
            precio = request.POST.get(f'precio_{zona}')
            if precio:
                cursor.execute("INSERT INTO precios_evento (evento_id, zona, precio) VALUES (%s, %s, %s)",
                               (evento_id, zona, precio))
        
        conn.commit()
        conn.close()
        messages.success(request, "¡Evento creado con éxito!")
        return redirect('inicio')
    
    conn.close()
    return render(request, 'crear_evento.html', {'establecimientos': establecimientos})

def borrar_evento(request, evento_id):
    if request.session.get('rol_id') != 2:
        messages.error(request, "Solo administradores pueden eliminar eventos")
        return redirect('inicio')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))
    conn.commit()
    conn.close()
    messages.success(request, "Evento eliminado correctamente")
    return redirect('inicio')