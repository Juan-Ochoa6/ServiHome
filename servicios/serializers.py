
from rest_framework import serializers
from .models import (
    Categoria,
    Servicio,
    SolicitudServicio,
    ServicioProfesional,
    PropuestaPrecio,
    TrabajoPortafolio
)
from usuarios.models import Perfil


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