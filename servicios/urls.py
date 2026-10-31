
from django.urls import path
from .views import (
    CategoriaListAPIView,
    ServicioListAPIView,
    SolicitudListCreateAPIView,
    SolicitudEstadoAPIView,
)
from .views import (
    OfertaPendienteListAPIView,
    OfertaEstadoAPIView,
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
    path(
    'admin/ofertas/',
    OfertaPendienteListAPIView.as_view(),
    name='admin-listar-ofertas',
),
path(
    'admin/ofertas/<int:pk>/',
    OfertaEstadoAPIView.as_view(),
    name='admin-cambiar-estado-oferta',
),
]
