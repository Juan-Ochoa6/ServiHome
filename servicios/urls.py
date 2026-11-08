from django.urls import path

from .views import (
    CategoriaListAPIView,
    ServicioListAPIView,
    SolicitudListCreateAPIView,
    SolicitudDetailAPIView,
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
    ResenaCreateAPIView,
    ResenasProfesionalListAPIView,
    ReputacionProfesionalAPIView,
    PagoCreateAPIView,
    MisPagosListAPIView,
    PagoEstadoAPIView,
    FinanzasResumenAPIView,
    IncidenteCreateAPIView,
    IncidentesAdminListAPIView,
    IncidenteAdminDetailAPIView,
    FacturaPDFAPIView,
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
    # RESEÑAS Y CALIFICACIONES

    path(
        'solicitudes/<int:pk>/resena/',
        ResenaCreateAPIView.as_view(),
        name='crear-resena'
    ),

    path(
        'profesionales/<int:profesional_id>/resenas/',
        ResenasProfesionalListAPIView.as_view(),
        name='resenas-profesional'
    ),

    path(
        'profesionales/<int:profesional_id>/reputacion/',
        ReputacionProfesionalAPIView.as_view(),
        name='reputacion-profesional'
    ),
        # PAGOS

    path(
        'solicitudes/<int:pk>/pago/',
        PagoCreateAPIView.as_view(),
        name='crear-pago'
    ),

    path(
        'mis-pagos/',
        MisPagosListAPIView.as_view(),
        name='mis-pagos'
    ),

    path(
        'pagos/<int:pk>/estado/',
        PagoEstadoAPIView.as_view(),
        name='actualizar-estado-pago'
    ),
    path(
    'admin/finanzas/',
    FinanzasResumenAPIView.as_view(),
    name='admin-finanzas'
),
    # INCIDENTES

    path(
        'incidentes/',
        IncidenteCreateAPIView.as_view(),
        name='crear-incidente'
    ),

    path(
        'admin/incidentes/',
        IncidentesAdminListAPIView.as_view(),
        name='admin-listar-incidentes'
    ),

    path(
        'admin/incidentes/<int:pk>/',
        IncidenteAdminDetailAPIView.as_view(),
        name='admin-gestionar-incidente'
    ),
    path(
        'pagos/<int:pk>/factura/',
        FacturaPDFAPIView.as_view(),
        name='descargar-factura'
    ),
    path(
        'solicitudes/',
        SolicitudListCreateAPIView.as_view(),
        name='lista-crear-solicitudes',
    ),
    path(
    'solicitudes/<int:pk>/',
    SolicitudDetailAPIView.as_view(),
    name='detalle-solicitud',
    ),
]