from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Avg, Count, Sum
from datetime import timedelta
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from django.db.models.functions import (
    TruncDate,
    TruncWeek,
    TruncMonth,
    TruncYear,
)
from .notificaciones import enviar_correo
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from usuarios.models import Perfil
import secrets
from .models import (
    Categoria,
    Servicio,
    SolicitudServicio,
    ServicioProfesional,
    PropuestaPrecio,
    TrabajoPortafolio,
    Resena,
    Pago,
    Incidente,
)

from .serializers import (
    CategoriaSerializer,
    ServicioSerializer,
    SolicitudServicioSerializer,
    OfertaPublicaSerializer,
    PropuestaPrecioSerializer,
    ServicioProfesionalSerializer,
    TrabajoPortafolioSerializer,
    ResenaSerializer,
    PagoSerializer,
    IncidenteSerializer,
    IncidenteAdminSerializer,
)
def exigir_profesional_aprobado(perfil):
    if (
        perfil.rol == 'profesional'
        and perfil.estado_verificacion != 'aprobado'
    ):
        raise PermissionDenied(
            'Debes estar aprobado por ServiHome para utilizar '
            'las funcionalidades profesionales.'
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
                    profesional__estado_identidad='aprobado',
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

        exigir_profesional_aprobado(perfil)
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
class SolicitudDetailAPIView(generics.RetrieveAPIView):

    serializer_class = SolicitudServicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            perfil = Perfil.objects.get(usuario=self.request.user)
        except Perfil.DoesNotExist:
            return SolicitudServicio.objects.none()
        exigir_profesional_aprobado(perfil)
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
class SolicitudEstadoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            perfil = Perfil.objects.get(usuario=request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )
        exigir_profesional_aprobado(perfil)
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

            if nuevo_estado in ['en_proceso', 'completada']:
                if perfil.rol != 'profesional':
                    raise PermissionDenied(
                        'Solo el profesional puede validar estos códigos.'
                    )

                codigo = str(
                    request.data.get('codigo', '')
                ).strip()

                if nuevo_estado == 'en_proceso':
                    codigo_esperado = solicitud.codigo_inicio
                    mensaje_error = 'El código de inicio es incorrecto.'
                else:
                    codigo_esperado = solicitud.codigo_finalizacion
                    mensaje_error = (
                        'El código de finalización es incorrecto.'
                    )

                if (
                    not codigo_esperado
                    or len(codigo) != 6
                    or not codigo.isdigit()
                    or not secrets.compare_digest(
                        codigo,
                        codigo_esperado
                    )
                ):
                    return Response(
                        {'error': mensaje_error},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if nuevo_estado == 'en_proceso':
                    solicitud.codigo_finalizacion = (
                        f"{secrets.randbelow(1000000):06d}"
                    )

                    solicitud.estado = 'en_proceso'
                    solicitud.save(
                        update_fields=[
                            'estado',
                            'codigo_finalizacion',
                        ]
                    )

                    destinatario = solicitud.cliente.usuario

                    asunto = 'Servicio iniciado - ServiHome'

                    mensaje_correo = (
                        f'Hola {destinatario.username},\n\n'
                        'El profesional ha iniciado tu servicio.\n\n'
                        f'Servicio: {solicitud.servicio.nombre}\n'
                        f'Profesional: '
                        f'{solicitud.profesional.usuario.username}\n\n'
                        'Puedes consultar el estado de tu solicitud '
                        'en ServiHome.\n\n'
                        'Equipo ServiHome'
                    )

                    transaction.on_commit(
                        lambda: enviar_correo(
                            destinatario=destinatario.email,
                            asunto=asunto,
                            mensaje=mensaje_correo,
                        )
                    )

                else:
                    solicitud.estado = 'completada'
                    solicitud.save(update_fields=['estado'])

                    destinatario = solicitud.cliente.usuario

                    asunto = 'Servicio completado - ServiHome'

                    mensaje_correo = (
                        f'Hola {destinatario.username},\n\n'
                        'Tu servicio ha sido marcado como completado.\n\n'
                        f'Servicio: {solicitud.servicio.nombre}\n'
                        f'Profesional: '
                        f'{solicitud.profesional.usuario.username}\n'
                        f'Precio acordado: ${solicitud.precio_acordado}\n\n'
                        'Gracias por utilizar ServiHome. '
                        'Puedes ingresar para consultar el servicio '
                        'y dejar tu reseña.\n\n'
                        'Equipo ServiHome'
                    )

                    transaction.on_commit(
                        lambda: enviar_correo(
                            destinatario=destinatario.email,
                            asunto=asunto,
                            mensaje=mensaje_correo,
                        )
                    )

            else:
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
                'estado_identidad': (
                oferta.profesional.estado_identidad
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
                if (
                    oferta.profesional.estado_identidad != 'aprobado'
                or oferta.profesional.estado_verificacion != 'aprobado'
                    ):
                    return Response(
            {
                'error': (
                    'No puedes aprobar una oferta de un profesional '
                    'que no tenga su identidad y verificación aprobadas.'
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
        exigir_profesional_aprobado(perfil)
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
    @extend_schema(
        request=PropuestaPrecioSerializer,
        responses={
            201: OpenApiResponse(
                response=PropuestaPrecioSerializer
            ),
        },
    )
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
            if perfil.id == solicitud.cliente_id:
                destinatario = solicitud.profesional.usuario
            else:
                destinatario = solicitud.cliente.usuario

            asunto = 'Nueva propuesta de precio - ServiHome'

            mensaje = (
                f'Hola {destinatario.username},\n\n'
                'Has recibido una nueva propuesta de precio.\n\n'
                f'Servicio: {solicitud.servicio.nombre}\n'
                f'Precio propuesto: ${propuesta.precio}\n'
                f'Propuesto por: {perfil.usuario.username}\n\n'
                'Ingresa a ServiHome para revisar la propuesta.\n\n'
                'Equipo ServiHome'
            )

            transaction.on_commit(
                lambda: enviar_correo(
                    destinatario=destinatario.email,
                    asunto=asunto,
                    mensaje=mensaje,
                )
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
            exigir_profesional_aprobado(perfil)
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

                solicitud.codigo_inicio = (
                    f"{secrets.randbelow(1000000):06d}"
                )

                solicitud.propuestas.filter(
                    estado='pendiente'
                ).exclude(
                    pk=propuesta.id
                ).update(
                    estado='reemplazada'
                )

                solicitud.precio_acordado = propuesta.precio
                solicitud.estado = 'aceptada'
                solicitud.save(
                update_fields=[
                    'precio_acordado',
                    'estado',
                    'codigo_inicio',
                ]
                )

                mensaje = (
                    'Propuesta aceptada. El precio quedó acordado.'
                )

            else:
                propuesta.estado = 'rechazada'
                propuesta.save(update_fields=['estado'])

                mensaje = 'Propuesta rechazada.'

            destinatario = propuesta.proponente.usuario

            asunto = (
                'Propuesta aceptada - ServiHome'
                if accion == 'aceptar'
                else 'Propuesta rechazada - ServiHome'
            )

            if accion == 'aceptar':
                detalle = (
                    'Tu propuesta fue aceptada. '
                    'El precio quedó acordado.'
                )
            else:
                detalle = (
                    'Tu propuesta fue rechazada. '
                    'Puedes revisar la solicitud en ServiHome.'
                )

            mensaje_correo = (
                f'Hola {destinatario.username},\n\n'
                f'{detalle}\n\n'
                f'Servicio: {solicitud.servicio.nombre}\n'
                f'Precio propuesto: ${propuesta.precio}\n\n'
                'Ingresa a ServiHome para consultar los detalles.\n\n'
                'Equipo ServiHome'
            )

            transaction.on_commit(
                lambda: enviar_correo(
                    destinatario=destinatario.email,
                    asunto=asunto,
                    mensaje=mensaje_correo,
                )
            )

        return Response({
            'mensaje': mensaje,
            'propuesta': PropuestaPrecioSerializer(propuesta).data,
        })

class ServicioProfesionalListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ServicioProfesionalSerializer
    permission_classes = [IsAuthenticated]

    def get_perfil(self):
        try:
            perfil = Perfil.objects.get(usuario=self.request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'profesional':
            raise PermissionDenied(
                'Solo los profesionales pueden gestionar ofertas.'
            )
        exigir_profesional_aprobado(perfil)
        return perfil

    def get_queryset(self):
        perfil = self.get_perfil()

        return ServicioProfesional.objects.filter(
            profesional=perfil
        ).select_related('servicio')

    def perform_create(self, serializer):
        perfil = self.get_perfil()

        if perfil.estado_identidad != 'aprobado':
            raise PermissionDenied(
            'Debes tener tu identidad aprobada para ofrecer servicios.'
        )
        if perfil.estado_verificacion != 'aprobado':
            raise PermissionDenied(
        'Debes estar aprobado por ServiHome para ofrecer servicios.'
    )

        serializer.save(
            profesional=perfil,
            estado_aprobacion='pendiente'
    )


class ServicioProfesionalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServicioProfesionalSerializer
    permission_classes = [IsAuthenticated]

    def get_perfil(self):
        try:
            perfil = Perfil.objects.get(usuario=self.request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'profesional':
            raise PermissionDenied(
                'Solo los profesionales pueden gestionar ofertas.'
            )
        exigir_profesional_aprobado(perfil)
        return perfil

    def get_queryset(self):
        perfil = self.get_perfil()

        return ServicioProfesional.objects.filter(
            profesional=perfil
        ).select_related('servicio')

    def perform_update(self, serializer):
        perfil = self.get_perfil()

        if perfil.estado_identidad != 'aprobado':
            raise PermissionDenied(
            'Debes tener tu identidad aprobada para modificar tus ofertas.'
        )
        if perfil.estado_verificacion != 'aprobado':
            raise PermissionDenied(
        'Debes estar aprobado por ServiHome para ofrecer servicios.'
    )

        serializer.save(
        estado_aprobacion='pendiente'
        )

class MiPortafolioListCreateAPIView(generics.ListCreateAPIView):

    serializer_class = TrabajoPortafolioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get_perfil(self):
        try:
            perfil = Perfil.objects.get(usuario=self.request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'profesional':
            raise PermissionDenied(
                'Solo los profesionales pueden gestionar su portafolio.'
            )
        exigir_profesional_aprobado(perfil)
        return perfil

    def get_queryset(self):
        perfil = self.get_perfil()

        return TrabajoPortafolio.objects.filter(
            profesional=perfil
        ).select_related('servicio')

    def perform_create(self, serializer):
        perfil = self.get_perfil()

        serializer.save(
            profesional=perfil
        )


class MiPortafolioDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TrabajoPortafolioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        try:
            perfil = Perfil.objects.get(usuario=self.request.user)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'profesional':
            raise PermissionDenied(
                'Solo los profesionales pueden gestionar su portafolio.'
            )
        exigir_profesional_aprobado(perfil)

        return TrabajoPortafolio.objects.filter(
            profesional=perfil
        )
class PortafolioProfesionalListAPIView(generics.ListAPIView):
    serializer_class = TrabajoPortafolioSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        profesional_id = self.kwargs['profesional_id']

        return (
            TrabajoPortafolio.objects
            .filter(
                    profesional_id=profesional_id,
                    profesional__rol='profesional',
                    profesional__estado_identidad='aprobado',
                    profesional__estado_verificacion='aprobado',
                    activo=True,
)
            .select_related('profesional__usuario', 'servicio')
            .order_by('-fecha_publicacion')
        )
# RESEÑAS Y CALIFICACIONES


class ResenaCreateAPIView(generics.CreateAPIView):

    serializer_class = ResenaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        perfil = get_object_or_404(
            Perfil,
            usuario=self.request.user
        )

        if perfil.rol != 'cliente':
            raise PermissionDenied(
                'Solo los clientes pueden crear reseñas.'
            )

        solicitud = get_object_or_404(
            SolicitudServicio,
            pk=self.kwargs['pk']
        )

        if solicitud.cliente_id != perfil.id:
            raise PermissionDenied(
                'Esta solicitud no te pertenece.'
            )

        if solicitud.estado != 'completada':
            raise ValidationError(
                'Solo puedes reseñar servicios completados.'
            )

        if Resena.objects.filter(solicitud=solicitud).exists():
            raise ValidationError(
                'Esta solicitud ya tiene una reseña.'
            )

        serializer.save(solicitud=solicitud)


class ResenasProfesionalListAPIView(generics.ListAPIView):

    serializer_class = ResenaSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):

        profesional = get_object_or_404(
            Perfil,
            pk=self.kwargs['profesional_id'],
            rol='profesional'
        )

        return (
            Resena.objects
            .filter(
                solicitud__profesional=profesional,
                solicitud__estado='completada'
            )
            .select_related(
                'solicitud__cliente__usuario',
                'solicitud__profesional__usuario'
            )
            .order_by('-fecha_creacion')
        )


class ReputacionProfesionalAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, profesional_id):

        profesional = get_object_or_404(
            Perfil,
            pk=profesional_id,
            rol='profesional'
        )

        resultado = Resena.objects.filter(
            solicitud__profesional=profesional,
            solicitud__estado='completada'
        ).aggregate(
            promedio=Avg('calificacion'),
            total=Count('id')
        )

        promedio = resultado['promedio']

        return Response({
            'profesional_id': profesional.id,
            'promedio_calificacion': (
                round(float(promedio), 2)
                if promedio is not None else 0
            ),
            'total_resenas': resultado['total']
        })
# PAGOS


class PagoCreateAPIView(generics.CreateAPIView):

    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        perfil = get_object_or_404(
            Perfil,
            usuario=self.request.user
        )

        if perfil.rol != 'cliente':
            raise PermissionDenied(
                'Solo los clientes pueden registrar pagos.'
            )

        solicitud = get_object_or_404(
            SolicitudServicio,
            pk=self.kwargs['pk']
        )

        if solicitud.cliente_id != perfil.id:
            raise PermissionDenied(
                'Esta solicitud no te pertenece.'
            )

        if solicitud.estado != 'completada':
            raise ValidationError(
                'Solo puedes registrar pagos de servicios completados.'
            )

        if solicitud.precio_acordado is None:
            raise ValidationError(
                'La solicitud no tiene un precio acordado.'
            )

        if Pago.objects.filter(solicitud=solicitud).exists():
            raise ValidationError(
                'Esta solicitud ya tiene un registro de pago.'
            )

        serializer.save(
            solicitud=solicitud,
            monto_total=solicitud.precio_acordado
        )


class MisPagosListAPIView(generics.ListAPIView):

    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        perfil = get_object_or_404(
            Perfil,
            usuario=self.request.user
        )

        pagos = Pago.objects.select_related(
            'solicitud__cliente__usuario',
            'solicitud__profesional__usuario'
        )

        if perfil.rol == 'cliente':
            return pagos.filter(
                solicitud__cliente=perfil
            )

        if perfil.rol == 'profesional':
            return pagos.filter(
                solicitud__profesional=perfil
            )

        if self.request.user.is_staff:
            return pagos

        raise PermissionDenied(
            'No tienes permisos para consultar estos pagos.'
        )


class PagoEstadoAPIView(APIView):

    permission_classes = [IsAdminUser]

    def patch(self, request, pk):

        pago = get_object_or_404(
            Pago,
            pk=pk
        )

        nuevo_estado = request.data.get('estado')

        transiciones = {
            'pendiente': ['pagado', 'fallido'],
            'pagado': ['reembolsado'],
            'fallido': [],
            'reembolsado': [],
        }

        if nuevo_estado not in transiciones.get(pago.estado, []):
            raise ValidationError(
                'La transición de estado no está permitida.'
            )

        pago.estado = nuevo_estado

        if nuevo_estado == 'pagado':
            from django.utils import timezone
            pago.fecha_pago = timezone.now()

        pago.save()

        return Response(
            PagoSerializer(pago).data,
            status=status.HTTP_200_OK
        )
@extend_schema(
    summary='Consultar resumen financiero de ServiHome',
    description='Consulta los ingresos y comisiones agrupados por periodo.',
    parameters=[
        OpenApiParameter(
            name='periodo',
            description='Periodo de agrupación de los datos.',
            required=False,
            type=str,
            enum=['dia', 'semana', 'mes', 'ano'],
        )
    ],
)
class FacturaPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pago = get_object_or_404(
            Pago.objects.select_related(
                'solicitud__cliente__usuario',
                'solicitud__profesional__usuario',
                'solicitud__servicio__categoria',
            ),
            pk=pk
        )

        # El administrador puede consultar cualquier factura.
        if request.user.is_staff:
            pass

        else:
            perfil = get_object_or_404(
                Perfil,
                usuario=request.user
            )

            # El cliente solo puede descargar sus propias facturas.
            if perfil.rol == 'cliente':
                if pago.solicitud.cliente_id != perfil.id:
                    raise PermissionDenied(
                        'No tienes permiso para consultar esta factura.'
                    )

            else:
                raise PermissionDenied(
                    'No tienes permiso para descargar esta factura.'
                )

        if pago.estado != 'pagado':
            raise ValidationError(
                'Solo se pueden generar facturas de pagos confirmados.'
            )

        solicitud = pago.solicitud
        cliente = solicitud.cliente
        profesional = solicitud.profesional

        respuesta = HttpResponse(
            content_type='application/pdf'
        )
        respuesta['Content-Disposition'] = (
            f'attachment; filename="factura_servihome_{pago.pk}.pdf"'
        )

        documento = SimpleDocTemplate(
            respuesta,
            pagesize=letter,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        estilos = getSampleStyleSheet()

        titulo = ParagraphStyle(
            'TituloFactura',
            parent=estilos['Title'],
            textColor=colors.HexColor('#174A7E'),
            fontSize=20,
            spaceAfter=12,
        )

        contenido = []

        contenido.append(
            Paragraph('SERVIHOME', titulo)
        )

        contenido.append(
            Paragraph(
                f'Comprobante de pago N.º {pago.pk}',
                estilos['Heading2']
            )
        )

        contenido.append(
            Paragraph(
                f'Fecha de emisión: {timezone.localtime().strftime("%d/%m/%Y %H:%M")}',
                estilos['Normal']
            )
        )

        contenido.append(Spacer(1, 15))

        datos = [
            ['INFORMACIÓN DEL CLIENTE', ''],
            [
                'Nombre',
                f'{cliente.usuario.first_name} {cliente.usuario.last_name}'.strip()
                or cliente.usuario.username
            ],
            ['Correo', cliente.usuario.email or 'No registrado'],
            ['Teléfono', cliente.telefono or 'No registrado'],
            ['', ''],
            ['INFORMACIÓN DEL PROFESIONAL', ''],
            [
                'Nombre',
                f'{profesional.usuario.first_name} {profesional.usuario.last_name}'.strip()
                or profesional.usuario.username
            ],
            ['Teléfono', profesional.telefono or 'No registrado'],
            ['', ''],
            ['DETALLE DEL SERVICIO', ''],
            ['Servicio', solicitud.servicio.nombre],
            ['Categoría', solicitud.servicio.categoria.nombre],
            ['Descripción', solicitud.descripcion],
            ['Dirección', solicitud.direccion_servicio],
            ['', ''],
            ['DETALLE DEL PAGO', ''],
            ['Método de pago', pago.get_metodo_display()],
            ['Referencia', pago.referencia or 'No registrada'],
            [
                'Fecha del pago',
                timezone.localtime(pago.fecha_pago).strftime('%d/%m/%Y %H:%M')
                if pago.fecha_pago else 'No registrada'
            ],
            ['Estado', pago.get_estado_display()],
            [
                'Valor total',
                f'$ {pago.monto_total:,.2f} COP'
            ],
            [
                f'Comisión ServiHome ({pago.porcentaje_comision}%)',
                f'$ {pago.monto_comision:,.2f} COP'
            ],
            [
                'Valor para el profesional',
                f'$ {pago.monto_profesional:,.2f} COP'
            ],
        ]

        tabla = Table(
            datos,
            colWidths=[65 * mm, 105 * mm]
        )

        tabla.setStyle(
            TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#174A7E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#174A7E')),
                ('TEXTCOLOR', (0, 5), (-1, 5), colors.white),
                ('SPAN', (0, 5), (-1, 5)),
                ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#174A7E')),
                ('TEXTCOLOR', (0, 10), (-1, 10), colors.white),
                ('SPAN', (0, 10), (-1, 10)),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
                ('FONTNAME', (0, 10), (-1, 10), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F6F8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D5DDE5')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ])
        )

        contenido.append(tabla)
        contenido.append(Spacer(1, 20))

        contenido.append(
            Paragraph(
                'Este documento es un comprobante de pago generado por ServiHome. '
                'No constituye una factura electrónica validada por la DIAN.',
                estilos['Italic']
            )
        )

        documento.build(contenido)

        return respuesta
class FinanzasResumenAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        periodo = request.query_params.get('periodo', 'mes')

        truncaciones = {
            'dia': TruncDate,
            'semana': TruncWeek,
            'mes': TruncMonth,
            'ano': TruncYear,
        }

        ventanas = {
            'dia': timedelta(days=30),
            'semana': timedelta(weeks=12),
            'mes': timedelta(days=365),
            'ano': timedelta(days=365 * 5),
        }

        if periodo not in truncaciones:
            return Response(
                {
                    'error': (
                        'Periodo no válido. Usa: dia, semana, mes o ano.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        ahora = timezone.now()
        fecha_inicio = ahora - ventanas[periodo]

        pagos = Pago.objects.filter(
            estado='pagado',
            fecha_pago__isnull=False
        )

        # Resumen general de todos los pagos confirmados.
        resumen = pagos.aggregate(
            total_pagado=Sum('monto_total', default=0),
            ganancia_servihome=Sum('monto_comision', default=0),
            total_profesionales=Sum('monto_profesional', default=0),
            cantidad_pagos=Count('id')
        )

        # Datos agrupados para las gráficas.
        datos = (
            pagos.filter(
                fecha_pago__gte=fecha_inicio,
                fecha_pago__lte=ahora
            )
            .annotate(periodo=truncaciones[periodo]('fecha_pago'))
            .values('periodo')
            .annotate(
                total_pagado=Sum('monto_total', default=0),
                ganancia_servihome=Sum('monto_comision', default=0),
                total_profesionales=Sum('monto_profesional', default=0),
                cantidad_pagos=Count('id')
            )
            .order_by('periodo')
        )

        resultados = []

        for dato in datos:
            fecha = dato['periodo']

            resultados.append({
                'periodo': (
                    fecha.date().isoformat()
                    if hasattr(fecha, 'date')
                    else fecha.isoformat()
                ),
                'total_pagado': dato['total_pagado'],
                'ganancia_servihome': dato['ganancia_servihome'],
                'total_profesionales': dato['total_profesionales'],
                'cantidad_pagos': dato['cantidad_pagos'],
            })

        return Response({
            'resumen': resumen,
            'periodo_seleccionado': periodo,
            'datos': resultados,
        })

class IncidenteCreateAPIView(generics.CreateAPIView):
    serializer_class = IncidenteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        perfil = get_object_or_404(
            Perfil,
            usuario=self.request.user
        )

        solicitud = serializer.validated_data['solicitud']

        if perfil.rol != 'cliente':
            raise PermissionDenied(
                'Solo los clientes pueden reportar incidentes.'
            )

        if solicitud.cliente_id != perfil.id:
            raise PermissionDenied(
                'No puedes reportar incidentes en solicitudes ajenas.'
            )

        incidente = serializer.save(reportado_por=perfil)

        Usuario = get_user_model()

        administradores = Usuario.objects.filter(
            is_superuser=True,
            is_active=True
        ).exclude(email='')

        asunto = 'Nuevo incidente reportado - ServiHome'

        mensaje = (
            'Hola administrador,\n\n'
            'Se ha reportado un nuevo incidente en ServiHome.\n\n'
            f'Número de incidente: {incidente.pk}\n'
            f'Número de solicitud: {solicitud.pk}\n'
            f'Servicio: {solicitud.servicio.nombre}\n'
            f'Cliente: {perfil.usuario.username}\n'
            f'Tipo de incidente: {incidente.tipo}\n'
            f'Descripción: {incidente.descripcion}\n\n'
            'Ingresa al panel de administración de ServiHome '
            'para revisar el incidente.\n\n'
            'Equipo ServiHome'
        )

        for administrador in administradores:
            transaction.on_commit(
                lambda email=administrador.email: enviar_correo(
                    destinatario=email,
                    asunto=asunto,
                    mensaje=mensaje,
                )
            )


class IncidentesAdminListAPIView(generics.ListAPIView):
    serializer_class = IncidenteSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Incidente.objects.select_related(
            'solicitud',
            'reportado_por',
        ).order_by('-fecha_creacion')




class IncidenteAdminDetailAPIView(generics.UpdateAPIView):
    serializer_class = IncidenteAdminSerializer
    permission_classes = [IsAdminUser]

    queryset = Incidente.objects.select_related(
        'solicitud',
        'reportado_por__usuario',
        'solicitud__servicio',
    )

    http_method_names = ['patch', 'head', 'options']

    def perform_update(self, serializer):
        incidente = self.get_object()

        estado_anterior = incidente.estado
        respuesta_anterior = incidente.respuesta_administrador

        incidente = serializer.save()

        if (
            incidente.estado != estado_anterior
            or incidente.respuesta_administrador != respuesta_anterior
        ):
            destinatario = incidente.reportado_por.usuario

            estados = {
                'pendiente': 'Pendiente',
                'en_revision': 'En revisión',
                'resuelto': 'Resuelto',
                'rechazado': 'Rechazado',
            }

            mensaje_estado = ''

            if incidente.estado != estado_anterior:
                mensaje_estado += (
                    f'Estado anterior: '
                    f'{estados.get(estado_anterior, estado_anterior)}\n'
                )

            mensaje_estado += (
                f'Estado actual: '
                f'{estados.get(incidente.estado, incidente.estado)}\n'
            )

            asunto = 'Actualización de tu incidente - ServiHome'

            mensaje = (
                f'Hola {destinatario.username},\n\n'
                'El administrador ha actualizado tu incidente '
                'en ServiHome.\n\n'
                f'Número de incidente: {incidente.pk}\n'
                f'Servicio: {incidente.solicitud.servicio.nombre}\n'
                f'{mensaje_estado}\n'
                f'Respuesta del administrador: '
                f'{incidente.respuesta_administrador or "Sin respuesta adicional."}\n\n'
                'Ingresa a ServiHome para consultar los detalles.\n\n'
                'Equipo ServiHome'
            )

            transaction.on_commit(
                lambda: enviar_correo(
                    destinatario=destinatario.email,
                    asunto=asunto,
                    mensaje=mensaje,
                )
            )
