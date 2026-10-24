
from django.urls import path
from .views import (
    CategoriaListAPIView,
    ServicioListAPIView,
    SolicitudListCreateAPIView,
    SolicitudEstadoAPIView,
)

urlpatterns = [
    path(
        'categorias/',
        CategoriaListAPIView.as_view(),
        name='lista-categorias',
    ),
    path(
        'servicios/',
        ServicioListAPIView.as_view(),
        name='lista-servicios',
    ),
    path(
        'solicitudes/',
        SolicitudListCreateAPIView.as_view(),
        name='lista-crear-solicitudes',
    ),
    path(
        'solicitudes/<int:pk>/estado/',
        SolicitudEstadoAPIView.as_view(),
        name='cambiar-estado-solicitud',
    ),
]
