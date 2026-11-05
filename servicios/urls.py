from django.urls import path

from .views import (
    CategoriaListAPIView,
    ServicioListAPIView,
    SolicitudListCreateAPIView,
    SolicitudEstadoAPIView,
    OfertaPendienteListAPIView,
    OfertaEstadoAPIView,
    OfertaPublicaListAPIView,
    PropuestaPrecioListCreateAPIView,
    PropuestaPrecioRespuestaAPIView,
    ServicioProfesionalListCreateAPIView,
    ServicioProfesionalDetailAPIView,
    MiPortafolioListCreateAPIView,
    MiPortafolioDetailAPIView,
    PortafolioProfesionalListAPIView,   
)

urlpatterns = [
    path(
        'ofertas/',
        OfertaPublicaListAPIView.as_view(),
        name='lista-ofertas',
    ),
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
    path(
        'solicitudes/<int:pk>/propuestas/',
        PropuestaPrecioListCreateAPIView.as_view(),
        name='propuestas-precio',
    ),
    path(
        'solicitudes/<int:pk>/propuestas/<int:propuesta_id>/',
        PropuestaPrecioRespuestaAPIView.as_view(),
        name='responder-propuesta-precio',
    ),
    path(
    'mis-ofertas/',
    ServicioProfesionalListCreateAPIView.as_view(),
    name='mis-ofertas'
    ),
    path(
    'mis-ofertas/<int:pk>/',
    ServicioProfesionalDetailAPIView.as_view(),
    name='detalle-mi-oferta'
    ),
    # PORTAFOLIO PROFESIONAL

    path(
    'mi-portafolio/',
    MiPortafolioListCreateAPIView.as_view(),
    name='mi-portafolio'
),

    path(
    'mi-portafolio/<int:pk>/',
    MiPortafolioDetailAPIView.as_view(),
    name='mi-portafolio-detail'
),

    path(
    'profesionales/<int:profesional_id>/portafolio/',
    PortafolioProfesionalListAPIView.as_view(),
    name='portafolio-profesional'
),
]