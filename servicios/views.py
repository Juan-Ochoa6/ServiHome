
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from usuarios.models import Perfil
from rest_framework.exceptions import PermissionDenied
from usuarios.models import Perfil

from .models import Categoria, Servicio, SolicitudServicio
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
        print("Usuario autenticado:", self.request.user.username)
        usuario = self.request.user
        try:
            perfil = usuario.perfil
        except Exception:
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

   
    def perform_create(self, serializer):
        usuario = self.request.user

        try:
            perfil = Perfil.objects.get(usuario=usuario)
        except Perfil.DoesNotExist:
            raise PermissionDenied(
                'Tu usuario no tiene un perfil configurado.'
            )

        if perfil.rol != 'cliente':
            raise PermissionDenied(
                'Solo los clientes pueden crear solicitudes.'
            )

        serializer.save(
            cliente=perfil,
            estado='pendiente',
            precio_acordado=None,
        )


class SolicitudEstadoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            perfil = request.user.perfil
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
