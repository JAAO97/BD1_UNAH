# app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro, name='registro'),
    
    path('evento/<int:evento_id>/', views.detalle_evento, name='detalle_evento'),
    path('seleccionar-asientos/<int:evento_id>/', views.seleccionar_asientos, name='seleccionar_asientos'),
    #path('carrito/', views.carrito, name='carrito'),
    #path('subir-comprobante/', views.subir_comprobante, name='subir_comprobante'),
    
    # Admin
    #path('admin/crear-evento/', views.crear_evento, name='crear_evento'),
    #path('admin/pagos-pendientes/', views.pagos_pendientes, name='pagos_pendientes'),
    #path('admin/aprobar-pago/<int:pago_id>/', views.aprobar_pago, name='aprobar_pago'),
    #path('admin/rechazar-pago/<int:pago_id>/', views.rechazar_pago, name='rechazar_pago'),
    
    #path('mis-boletos/', views.mis_boletos, name='mis_boletos'),
]