
from rest_framework import serializers
from .models import Categoria, Servicio, SolicitudServicio


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ServicioSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    class Meta:
        model = Servicio
        fields = '__all__'


class SolicitudServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudServicio
        fields = [
            'id',
            'cliente',
            'profesional',
            'servicio',
            'descripcion',
            'direccion_servicio',
            'fecha_solicitada',
            'estado',
            'precio_acordado',
            'fecha_creacion',
        ]

        read_only_fields = [
            'id',
            'cliente',
            'estado',
            'precio_acordado',
            'fecha_creacion',
        ]
        
    def validate(self, attrs):
        profesional = attrs.get('profesional')
        servicio = attrs.get('servicio')

        if profesional and servicio:
            if profesional.rol != 'profesional':
                raise serializers.ValidationError({
                    'profesional': 'El usuario seleccionado no es un profesional.'
                })

            ofrece_servicio = servicio.profesionales.filter(
                pk=profesional.pk
            ).exists()

            if not ofrece_servicio:
                raise serializers.ValidationError({
                    'servicio': 'Este profesional no ofrece el servicio seleccionado.'
                })

        return attrs

