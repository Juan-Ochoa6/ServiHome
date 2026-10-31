
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from usuarios.models import Perfil

from .models import (
    Categoria,
    Servicio,
    SolicitudServicio,
    ServicioProfesional,
)
from .serializers import (
    CategoriaSerializer,
    ServicioSerializer,
    SolicitudServicioSerializer,
)


class CategoriaListAPIView(generics.ListAPIView):
    queryset = Categoria.objects.filter(activa=True)
    serializer_class = CategoriaSerializer


class ServicioListAPIView(generics.ListAPIView):
    queryset = (
        Servicio.objects
        .filter(activo=True)
        .select_related('categoria')
    )
    serializer_class = ServicioSerializer


class SolicitudListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SolicitudServicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user

        try:
            perfil = Perfil.objects.get(usuario=usuario)
        except Perfil.DoesNotExist:
            return SolicitudServicio.objects.none()

        if perfil.rol == 'cliente':
            filtro = {'cliente': perfil}
        elif perfil.rol == 'profesional':
            filtro = {'profesional': perfil}
        else:
            return SolicitudServicio.objects.none()

        return (
            SolicitudServicio.objects
            .filter(**filtro)
            .select_related(
                'cliente__usuario',
                'profesional__usuario',
                'servicio',
            )
        )

    def create(self, request, *args, **kwargs):
        try:
            perfil = Perfil.objects.get(usuario=request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'cliente':
            raise PermissionDenied(
                'Solo los clientes pueden crear solicitudes.'
            )

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        perfil = Perfil.objects.get(usuario=self.request.user)

        serializer.save(
            cliente=perfil,
            estado='pendiente',
            precio_acordado=None,
        )

@extend_schema(
    tags=['Solicitudes'],
    summary='Actualizar estado de una solicitud',
    description=(
        'Permite al profesional aceptar, rechazar, iniciar o completar '
        'una solicitud. El cliente puede cancelar solicitudes pendientes '
        'o aceptadas.'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'estado': {
                    'type': 'string',
                    'enum': [
                        'aceptada',
                        'rechazada',
                        'en_proceso',
                        'completada',
                        'cancelada',
                    ],
                }
            },
            'required': ['estado'],
        }
    },
    responses={
        200: OpenApiResponse(description='Estado actualizado correctamente.'),
        400: OpenApiResponse(description='Cambio de estado no permitido.'),
        403: OpenApiResponse(description='No tienes permiso para modificar esta solicitud.'),
        404: OpenApiResponse(description='La solicitud no existe.'),
    },
)
class SolicitudEstadoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            perfil = Perfil.objects.get(usuario=request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        with transaction.atomic():
            try:
                solicitud = (
                    SolicitudServicio.objects
                    .select_for_update()
                    .get(pk=pk)
                )
            except SolicitudServicio.DoesNotExist:
                return Response(
                    {'error': 'La solicitud no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if perfil.rol == 'profesional':
                if solicitud.profesional_id != perfil.id:
                    raise PermissionDenied(
                        'Esta solicitud no te corresponde.'
                    )

                estados_permitidos = {
                    'pendiente': ['aceptada', 'rechazada'],
                    'aceptada': ['en_proceso'],
                    'en_proceso': ['completada'],
                }

            elif perfil.rol == 'cliente':
                if solicitud.cliente_id != perfil.id:
                    raise PermissionDenied(
                        'Esta solicitud no te corresponde.'
                    )

                estados_permitidos = {
                    'pendiente': ['cancelada'],
                    'aceptada': ['cancelada'],
                }

            else:
                raise PermissionDenied(
                    'Tu rol no puede cambiar solicitudes.'
                )

            nuevo_estado = request.data.get('estado')
            permitidos = estados_permitidos.get(
                solicitud.estado, []
            )

            if nuevo_estado not in permitidos:
                return Response(
                    {'error': 'No puedes realizar ese cambio de estado.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            solicitud.estado = nuevo_estado
            solicitud.save(update_fields=['estado'])

        return Response({
            'mensaje': 'Estado actualizado correctamente.',
            'solicitud_id': solicitud.id,
            'estado': solicitud.estado,
        })

# =========================================================
# ADMINISTRACIÓN DE OFERTAS PROFESIONALES
# =========================================================
@extend_schema(
    tags=['Administración de ofertas'],
    summary='Listar ofertas pendientes',
    description='Lista las ofertas profesionales que esperan aprobación administrativa.',
    responses={
        200: OpenApiResponse(
            description='Lista de ofertas pendientes con información del profesional y servicio.'
        ),
        403: OpenApiResponse(description='No tienes permisos de administrador.'),
    },
)
class OfertaPendienteListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Lista las ofertas que esperan aprobación."""

        ofertas = (
            ServicioProfesional.objects
            .filter(estado_aprobacion='pendiente')
            .select_related(
                'profesional__usuario',
                'servicio',
                'servicio__categoria',
            )
            .order_by('id')
        )

        resultados = []

        for oferta in ofertas:
            resultados.append({
                'id': oferta.id,
                'profesional_id': oferta.profesional_id,
                'profesional': oferta.profesional.usuario.username,
                'estado_profesional': (
                    oferta.profesional.estado_verificacion
                ),
                'servicio_id': oferta.servicio_id,
                'servicio': oferta.servicio.nombre,
                'categoria': oferta.servicio.categoria.nombre,
                'precio': oferta.precio,
                'estado_aprobacion': oferta.estado_aprobacion,
            })

        return Response(resultados)

@extend_schema(
    tags=['Administración de ofertas'],
    summary='Aprobar o rechazar una oferta',
    description=(
        'Permite al administrador aprobar o rechazar una oferta. '
        'Para aprobarla, el profesional debe estar previamente aprobado.'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'estado_aprobacion': {
                    'type': 'string',
                    'enum': ['aprobado', 'rechazado'],
                }
            },
            'required': ['estado_aprobacion'],
        }
    },
    responses={
        200: OpenApiResponse(description='Estado de la oferta actualizado.'),
        400: OpenApiResponse(description='Estado inválido o la oferta ya fue revisada.'),
        403: OpenApiResponse(description='No tienes permisos de administrador.'),
        404: OpenApiResponse(description='La oferta no existe.'),
    },
)
class OfertaEstadoAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        """Aprueba o rechaza una oferta profesional."""

        nuevo_estado = request.data.get('estado_aprobacion')

        if nuevo_estado not in ['aprobado', 'rechazado']:
            return Response(
                {
                    'error': (
                        'El estado debe ser aprobado o rechazado.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                oferta = (
                    ServicioProfesional.objects
                    .select_for_update()
                    .select_related('profesional')
                    .get(pk=pk)
                )
            except ServicioProfesional.DoesNotExist:
                return Response(
                    {'error': 'La oferta no existe.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if oferta.estado_aprobacion != 'pendiente':
                return Response(
                    {'error': 'Esta oferta ya fue revisada.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if nuevo_estado == 'aprobado':
                if oferta.profesional.estado_verificacion != 'aprobado':
                    return Response(
                        {
                            'error': (
                                'No puedes aprobar una oferta de un '
                                'profesional que todavía no está aprobado.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            oferta.estado_aprobacion = nuevo_estado
            oferta.save(update_fields=['estado_aprobacion'])

        return Response({
            'mensaje': 'Estado de la oferta actualizado.',
            'oferta_id': oferta.id,
            'estado_aprobacion': oferta.estado_aprobacion,
        })
