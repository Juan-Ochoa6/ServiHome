from django.db import transaction

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
)
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiResponse

from usuarios.models import Perfil

from .models import (
    Categoria,
    Servicio,
    SolicitudServicio,
    ServicioProfesional,
    PropuestaPrecio,
)

from .serializers import (
    CategoriaSerializer,
    ServicioSerializer,
    SolicitudServicioSerializer,
    OfertaPublicaSerializer,
    PropuestaPrecioSerializer,
)

class OfertaPublicaListAPIView(generics.ListAPIView):
    """Ofertas aprobadas de profesionales aprobados y disponibles."""

    serializer_class = OfertaPublicaSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            ServicioProfesional.objects
            .filter(
                estado_aprobacion='aprobado',
                profesional__estado_verificacion='aprobado',
                profesional__disponible=True,
                servicio__activo=True,
            )
            .select_related(
                'profesional__usuario',
                'servicio__categoria',
            )
            .order_by('id')
        )
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
    permission_classes = [AllowAny]


class ServicioListAPIView(generics.ListAPIView):
    queryset = (
        Servicio.objects
        .filter(activo=True)
        .select_related('categoria')
    )
    serializer_class = ServicioSerializer
    permission_classes = [AllowAny]


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
                'pendiente': ['rechazada'],
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
class PropuestaPrecioListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_solicitud_y_perfil(self, request, pk):
        try:
            perfil = Perfil.objects.get(usuario=request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        try:
            solicitud = (
                SolicitudServicio.objects
                .select_for_update()
                .get(pk=pk)
            )
        except SolicitudServicio.DoesNotExist:
            return None, perfil

        if perfil.id not in [
            solicitud.cliente_id,
            solicitud.profesional_id,
        ]:
            raise PermissionDenied(
                'No participas en esta solicitud.'
            )

        return solicitud, perfil

    def get(self, request, pk):
        with transaction.atomic():
            solicitud, perfil = self.get_solicitud_y_perfil(
                request, pk
            )

            if solicitud is None:
                return Response(
                    {'error': 'La solicitud no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            propuestas = solicitud.propuestas.select_related(
                'proponente__usuario'
            ).order_by('fecha_creacion')

            serializer = PropuestaPrecioSerializer(
                propuestas,
                many=True
            )

            return Response(serializer.data)

    def post(self, request, pk):
        serializer = PropuestaPrecioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        precio = serializer.validated_data['precio']

        with transaction.atomic():
            solicitud, perfil = self.get_solicitud_y_perfil(
                request, pk
            )

            if solicitud is None:
                return Response(
                    {'error': 'La solicitud no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if solicitud.estado != 'pendiente':
                return Response(
                    {
                        'error': (
                            'Esta solicitud ya no está en negociación.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            propuesta_pendiente = solicitud.propuestas.filter(
                estado='pendiente'
            ).first()

            if propuesta_pendiente:
                if propuesta_pendiente.proponente_id == perfil.id:
                    return Response(
                        {
                            'error': (
                                'Debes esperar a que la otra persona '
                                'responda tu propuesta.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                propuesta_pendiente.estado = 'reemplazada'
                propuesta_pendiente.save(
                    update_fields=['estado']
                )

            propuesta = PropuestaPrecio.objects.create(
                solicitud=solicitud,
                proponente=perfil,
                precio=precio,
            )

        respuesta = PropuestaPrecioSerializer(propuesta)

        return Response(
            {
                'mensaje': 'Propuesta enviada correctamente.',
                'propuesta': respuesta.data,
            },
            status=status.HTTP_201_CREATED,
        )


class PropuestaPrecioRespuestaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, propuesta_id):
        accion = request.data.get('accion')

        if accion not in ['aceptar', 'rechazar']:
            return Response(
                {'error': 'La acción debe ser aceptar o rechazar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            try:
                perfil = Perfil.objects.get(usuario=request.user)
            except Perfil.DoesNotExist:
                raise PermissionDenied(
                    'Tu usuario no tiene un perfil configurado.'
                )

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

            if perfil.id not in [
                solicitud.cliente_id,
                solicitud.profesional_id,
            ]:
                raise PermissionDenied(
                    'No participas en esta solicitud.'
                )

            try:
                propuesta = solicitud.propuestas.select_for_update().get(
                    pk=propuesta_id
                )
            except PropuestaPrecio.DoesNotExist:
                return Response(
                    {'error': 'La propuesta no existe.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if propuesta.estado != 'pendiente':
                return Response(
                    {'error': 'Esta propuesta ya fue respondida.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if propuesta.proponente_id == perfil.id:
                return Response(
                    {
                        'error': (
                            'No puedes responder tu propia propuesta.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if solicitud.estado != 'pendiente':
                return Response(
                    {
                        'error': (
                            'La solicitud ya no está en negociación.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if accion == 'aceptar':
                propuesta.estado = 'aceptada'
                propuesta.save(update_fields=['estado'])

                solicitud.precio_acordado = propuesta.precio
                solicitud.estado = 'aceptada'
                solicitud.save(
                    update_fields=['precio_acordado', 'estado']
                )

                mensaje = (
                    'Propuesta aceptada. El precio quedó acordado.'
                )

            else:
                propuesta.estado = 'rechazada'
                propuesta.save(update_fields=['estado'])

                mensaje = 'Propuesta rechazada.'

        return Response({
            'mensaje': mensaje,
            'propuesta': PropuestaPrecioSerializer(propuesta).data,
        })