# JAAO Tickets - Sistema de Boletería (BD1 UNAH)

Sistema de venta de boletas para eventos con selección de asientos visual, pagos por transferencia y códigos QR.

## Características
- Registro y login de usuarios
- Rol administrador
- Creación de eventos con imagen y precios por zona
- 3 establecimientos con mapas de asientos reales (cuadrado, rectangular, trapecio)
- Selección interactiva de asientos
- Subida de comprobante de pago
- Aprobación manual por admin
- Generación automática de QR
- Todo en Lempiras (L)

## Tecnologías
- Python 3.12
- Django 5.1 (sin ORM)
- MySQL puro
- Bootstrap 5
- qrcode + Pillow

## Instalación (para quien clone)

1. Clonar el repositorio
2. Ejecutar el script SQL: `mysql -u root -p < db/ticketmaster_rd.sql`
3. `pip install -r requirements.txt`
4. `python manage.py runserver`

Usuario admin: j@gmail.com / 123
               p3@gmail.com / 123

Usuario estandar: prueba@gmail.com / 123                

¡Listo para usar!