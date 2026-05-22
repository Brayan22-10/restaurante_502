from django.urls import path 
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    
    path('usuarios/asignar-rol/', views.asignar_rol_view, name='asignar_rol'),

    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),

    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/editar/<int:id>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:id>/', views.eliminar_empleado, name='eliminar_empleado'),
    
    path('mesas/', views.lista_mesas, name='lista_mesas'),
    path('mesas/crear/', views.crear_mesa, name='crear_mesa'),
    path('mesas/editar/<int:id>/', views.editar_mesa, name='editar_mesa'),
    path('mesas/eliminar/<int:id>/', views.eliminar_mesa, name='eliminar_mesa'),

    path('platos/', views.lista_platos, name='lista_platos'),
    path('platos/crear/', views.crear_plato, name='crear_plato'),
    path('platos/editar/<int:id>/', views.editar_plato, name='editar_plato'),
    path('platos/eliminar/<int:id>/', views.eliminar_plato, name='eliminar_plato'),

    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    path('ordenes/crear/', views.crear_orden, name='crear_orden'),
    path('ordenes/editar/<int:id>/', views.editar_orden, name='editar_orden'),
    path('ordenes/eliminar/<int:id>/', views.eliminar_orden, name='eliminar_orden'), 
    path('ordenes/<int:orden_id>/platos/', views.agregar_platos_orden, name='agregar_platos_orden'),
    path('ordenes/plato/eliminar/<int:detalle_id>/', views.eliminar_plato_orden, name='eliminar_plato_orden'), 
    path('ordenes/<int:orden_id>/confirmar/', views.confirmar_orden, name='confirmar_orden'),
    path('ordenes/<int:orden_id>/entregar/', views.entregar_orden, name='entregar_orden'),
    path('ordenes/cancelar/<int:orden_id>/', views.cancelar_orden, name='cancelar_orden'),

    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('ordenes/<int:orden_id>/cargar-caja/', views.cargar_factura, name='cargar_factura'),
    path('ordenes/<int:orden_id>/facturar/', views.crear_factura, name='crear_factura'), 
    path('facturas/editar/<int:id>/', views.editar_factura, name='editar_factura'),
    path('facturas/eliminar/<int:id>/', views.eliminar_factura, name='eliminar_factura'),
    path('facturas/cobrar/<int:factura_id>/', views.finalizar_pago_factura, name='finalizar_pago_factura'),
]
