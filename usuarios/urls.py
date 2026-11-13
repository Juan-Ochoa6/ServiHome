from django.urls import path
from . import views


urlpatterns = [
    path('registro/', views.registrar_usuario, name='registro_usuario'),
    path('mfa/configurar/', views.configurar_mfa, name='configurar_mfa'),
    path('mfa/verificar/', views.verificar_mfa, name='verificar_mfa'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('login/mfa/', views.verificar_codigo_login, name='verificar_codigo_login'),

    path(
        'admin/profesionales/',
        views.listar_profesionales_pendientes,
        name='admin-listar-profesionales'
    ),
    path(
        'admin/profesionales/<int:pk>/',
        views.cambiar_estado_profesional,
        name='admin-cambiar-estado-profesional'
    ),
    path(
    'disponibilidad/',
    views.cambiar_disponibilidad,
    name='cambiar-disponibilidad'
    ),
    path(
    'mis-documentos/',
    views.MisDocumentosVerificacionAPIView.as_view(),
    name='mis-documentos-verificacion'
    ),
    path(
    'documentos/<int:pk>/descargar/',
    views.DocumentoVerificacionDescargaAPIView.as_view(),
    name='documento-verificacion-descarga'
    ),
    path(
    'admin/documentos/',
    views.AdminDocumentosVerificacionAPIView.as_view(),
    name='admin-documentos-verificacion'
    ),
    path(
    'admin/documentos/<int:pk>/',
    views.AdminDocumentoVerificacionDetailAPIView.as_view(),
    name='admin-documento-verificacion-detalle'
    ),
    path(
    'mi-verificacion/',
    views.MiVerificacionAPIView.as_view(),
    name='mi-verificacion'
    ),
    path(
    'perfil/',
    views.MiPerfilAPIView.as_view(),
    name='mi-perfil'
    ),
    path(
    'profesionales/',
    views.listar_profesionales_disponibles,
    name='listar-profesionales-disponibles'
    ),
]