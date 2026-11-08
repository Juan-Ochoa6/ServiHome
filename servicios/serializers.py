
from rest_framework import serializers
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
from usuarios.models import Perfil
from django.utils import timezone


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = [
            'id',
            'nombre',
            'descripcion',
            'activa',
        ]
        read_only_fields = fields


class ServicioSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    class Meta:
        model = Servicio
        fields = [
            'id',
            'categoria',
            'categoria_nombre',
            'nombre',
            'descripcion',
            'precio_base',
            'activo',
            'fecha_creacion',
        ]
        read_only_fields = fields


class SolicitudServicioSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(
        source='cliente.usuario.username',
        read_only=True
    )

    profesional_nombre = serializers.CharField(
        source='profesional.usuario.username',
        read_only=True
    )

    servicio_nombre = serializers.CharField(
        source='servicio.nombre',
        read_only=True
    )

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    codigo_inicio = serializers.SerializerMethodField()
    codigo_finalizacion = serializers.SerializerMethodField()

    def get_codigo_inicio(self, solicitud):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            if solicitud.cliente.usuario_id == request.user.id:
                return solicitud.codigo_inicio or None

        return None

    def get_codigo_finalizacion(self, solicitud):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            if solicitud.cliente.usuario_id == request.user.id:
                return solicitud.codigo_finalizacion or None

        return None

    class Meta:
        model = SolicitudServicio
        fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'profesional',
            'profesional_nombre',
            'servicio',
            'servicio_nombre',
            'descripcion',
            'direccion_servicio',
            'fecha_solicitada',
            'estado',
            'estado_display',
            'precio_acordado',
            'fecha_creacion',
            'codigo_inicio',
            'codigo_finalizacion',
        ]

        read_only_fields = [
            'id',
            'cliente',
            'cliente_nombre',
            'profesional_nombre',
            'servicio_nombre',
            'estado',
            'estado_display',
            'precio_acordado',
            'fecha_creacion',
        ]
    def validate_fecha_solicitada(self, fecha_solicitada):
        if fecha_solicitada < timezone.now():
            raise serializers.ValidationError(
                'La fecha solicitada no puede ser anterior a la fecha actual.'
            )

        return fecha_solicitada
    def validate_profesional(self, profesional):
        if profesional.rol != 'profesional':
            raise serializers.ValidationError(
                'El usuario seleccionado no es un profesional.'
            )

        if not profesional.disponible:
            raise serializers.ValidationError(
                'El profesional no está disponible.'
            )

        return profesional

    def validate_servicio(self, servicio):
        if not servicio.activo:
            raise serializers.ValidationError(
                'El servicio seleccionado no está disponible.'
            )

        return servicio

    def validate(self, attrs):
        profesional = attrs.get('profesional')
        servicio = attrs.get('servicio')

        if profesional:
            if profesional.rol != 'profesional':
                raise serializers.ValidationError({
                    'profesional': (
                        'El usuario seleccionado no es un profesional.'
                    )
                })

            if profesional.estado_verificacion != 'aprobado':
                raise serializers.ValidationError({
                    'profesional': (
                        'Este profesional todavía no está aprobado por ServiHome.'
                    )
                })
            if profesional.estado_identidad != 'aprobado':
                raise serializers.ValidationError({
                'profesional': (
                'Este profesional todavía no tiene su identidad verificada.'
                )
                })

            if not profesional.disponible:
                raise serializers.ValidationError({
                    'profesional': (
                        'Este profesional no está disponible.'
                    )
                })

        if profesional and servicio:
            oferta_aprobada = ServicioProfesional.objects.filter(
                profesional=profesional,
                servicio=servicio,
                estado_aprobacion='aprobado'
            ).exists()

            if not oferta_aprobada:
                raise serializers.ValidationError({
                    'servicio': (
                        'Este profesional no tiene aprobado este servicio.'
                    )
                })

        return attrs
class OfertaPublicaSerializer(serializers.ModelSerializer):
    profesional_nombre = serializers.SerializerMethodField()
    descripcion_profesional = serializers.CharField(
        source='profesional.descripcion_profesional',
        read_only=True
    )
    experiencia_anos = serializers.IntegerField(
        source='profesional.experiencia_anos',
        read_only=True
    )
    servicio_nombre = serializers.CharField(
        source='servicio.nombre',
        read_only=True
    )
    servicio_descripcion = serializers.CharField(
        source='servicio.descripcion',
        read_only=True
    )
    categoria = serializers.IntegerField(
        source='servicio.categoria_id',
        read_only=True
    )
    categoria_nombre = serializers.CharField(
        source='servicio.categoria.nombre',
        read_only=True
    )

    class Meta:
        model = ServicioProfesional
        fields = [
            'id',
            'profesional',
            'profesional_nombre',
            'descripcion_profesional',
            'experiencia_anos',
            'servicio',
            'servicio_nombre',
            'servicio_descripcion',
            'categoria',
            'categoria_nombre',
            'precio',
        ]
        read_only_fields = fields

    def get_profesional_nombre(self, oferta):
        usuario = oferta.profesional.usuario
        return usuario.get_full_name().strip() or usuario.username
class PropuestaPrecioSerializer(serializers.ModelSerializer):
    proponente_nombre = serializers.CharField(
        source='proponente.usuario.username',
        read_only=True
    )

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    class Meta:
        model = PropuestaPrecio
        fields = [
            'id',
            'solicitud',
            'proponente',
            'proponente_nombre',
            'precio',
            'estado',
            'estado_display',
            'fecha_creacion',
        ]

        read_only_fields = [
            'id',
            'solicitud',
            'proponente',
            'proponente_nombre',
            'estado',
            'estado_display',
            'fecha_creacion',
        ]

    def validate_precio(self, precio):
        if precio < 30000:
            raise serializers.ValidationError(
            'El precio mínimo permitido es de $30.000 COP.'
        )

        return precio
class ServicioProfesionalSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(
        source='servicio.nombre',
        read_only=True
    )

    class Meta:
        model = ServicioProfesional
        fields = [
            'id',
            'servicio',
            'servicio_nombre',
            'precio',
            'estado_aprobacion',
        ]
        read_only_fields = [
            'id',
            'estado_aprobacion',
        ]

    def validate_precio(self, value):
        if value < 30000:
            raise serializers.ValidationError(
                'El precio mínimo de una oferta es $30.000 COP.'
            )
        return value

    def validate_servicio(self, value):
        if not value.activo:
            raise serializers.ValidationError(
                'No puedes ofrecer un servicio que está inactivo.'
            )
        return value
    def validate(self, attrs):
        servicio = attrs.get(
        'servicio',
        self.instance.servicio if self.instance else None
    )

        if servicio:
            profesional = self.context['request'].user.perfil

        existe = ServicioProfesional.objects.filter(
            profesional=profesional,
            servicio=servicio
        ).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists()

        if existe:
            raise serializers.ValidationError({
                'servicio': 'Ya tienes una oferta registrada para este servicio.'
            })

        return attrs
class TrabajoPortafolioSerializer(serializers.ModelSerializer):
    profesional = serializers.ReadOnlyField(
        source='profesional.usuario.username'
    )

    servicio_nombre = serializers.ReadOnlyField(
        source='servicio.nombre'
    )

    class Meta:
        model = TrabajoPortafolio
        fields = [
            'id',
            'profesional',
            'servicio',
            'servicio_nombre',
            'titulo',
            'descripcion',
            'imagen',
            'fecha_publicacion',
            'activo',
        ]

        read_only_fields = [
            'id',
            'profesional',
            'fecha_publicacion',
        ]
class ResenaSerializer(serializers.ModelSerializer):

    cliente_nombre = serializers.CharField(
        source='solicitud.cliente.usuario.username',
        read_only=True
    )

    profesional_nombre = serializers.CharField(
        source='solicitud.profesional.usuario.username',
        read_only=True
    )

    solicitud = serializers.IntegerField(
    source='solicitud.id',
    read_only=True
)

    class Meta:
        model = Resena
        fields = [
            'id',
            'solicitud',
            'cliente_nombre',
            'profesional_nombre',
            'calificacion',
            'comentario',
            'fecha_creacion',
        ]

        read_only_fields = [
            'id',
            'solicitud',
            'cliente_nombre',
            'profesional_nombre',
            'fecha_creacion',
        ]

    def validate_calificacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                'La calificación debe estar entre 1 y 5 estrellas.'
            )

        return value
class PagoSerializer(serializers.ModelSerializer):

    solicitud = serializers.IntegerField(
        source='solicitud.id',
        read_only=True
    )

    cliente_nombre = serializers.CharField(
        source='solicitud.cliente.usuario.username',
        read_only=True
    )

    profesional_nombre = serializers.CharField(
        source='solicitud.profesional.usuario.username',
        read_only=True
    )

    class Meta:
        model = Pago
        fields = [
            'id',
            'solicitud',
            'cliente_nombre',
            'profesional_nombre',
            'monto_total',
            'porcentaje_comision',
            'monto_comision',
            'monto_profesional',
            'metodo',
            'estado',
            'referencia',
            'fecha_pago',
            'fecha_creacion',
        ]

        read_only_fields = [
            'id',
            'solicitud',
            'cliente_nombre',
            'profesional_nombre',
            'monto_total',
            'porcentaje_comision',
            'monto_comision',
            'monto_profesional',
            'estado',
            'referencia',
            'fecha_pago',
            'fecha_creacion',
        ]
class IncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidente
        fields = [
            'id',
            'solicitud',
            'reportado_por',
            'tipo',
            'descripcion',
            'estado',
            'respuesta_administrador',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'reportado_por',
            'estado',
            'respuesta_administrador',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
class IncidenteAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incidente
        fields = [
            'id',
            'solicitud',
            'reportado_por',
            'tipo',
            'descripcion',
            'estado',
            'respuesta_administrador',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

        read_only_fields = [
            'id',
            'solicitud',
            'reportado_por',
            'tipo',
            'descripcion',
            'fecha_creacion',
            'fecha_actualizacion',
        ]