from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Perfil, DocumentoVerificacion
from servicios.models import ServicioProfesional

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
    required=True,
    allow_blank=False,
    trim_whitespace=True
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    rol = serializers.ChoiceField(
        choices=Perfil.ROLES,
        write_only=True
    )
    telefono = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True
    )
    direccion = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )


    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'rol',
            'telefono',
            'direccion',
        ]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'Este nombre de usuario ya está registrado.'
            )
        return value

    def validate_email(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                'El correo electrónico es obligatorio.'
            )

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Este correo electrónico ya está registrado.'
            )
        return value.lower().strip()

    @transaction.atomic
    def create(self, validated_data):
        rol = validated_data.pop('rol')
        telefono = validated_data.pop('telefono', '')
        direccion = validated_data.pop('direccion', '')
        password = validated_data.pop('password')

        # Crea el usuario con contraseña cifrada mediante Django.
        usuario = User.objects.create_user(
            password=password,
            **validated_data
        )

        # La señal post_save ya creó este perfil automáticamente.
        perfil = Perfil.objects.select_for_update().get(
            usuario=usuario
        )


        perfil.rol = rol
        perfil.telefono = telefono
        perfil.direccion = direccion

        if rol == 'profesional':
            perfil.estado_verificacion = 'pendiente'
            perfil.disponible = False
        else:
            perfil.estado_verificacion = 'no_aplica'

        perfil.save()

        # El profesional no queda disponible hasta su aprobación.
        if rol == 'profesional':
            perfil.disponible = False

        perfil.save()

        return usuario
class DocumentoVerificacionSerializer(serializers.ModelSerializer):

    def validate_archivo(self, archivo):
        extensiones_permitidas = ['.pdf', '.jpg', '.jpeg', '.png']
        extensiones = archivo.name.lower()

        if not any(
            extensiones.endswith(ext)
            for ext in extensiones_permitidas
        ):
            raise serializers.ValidationError(
                'Solo se permiten archivos PDF, JPG y PNG.'
            )

        limite = 5 * 1024 * 1024

        if archivo.size > limite:
            raise serializers.ValidationError(
                'El archivo no puede superar los 5 MB.'
            )

        return archivo
    archivo = serializers.FileField(write_only=True)
    url_descarga = serializers.SerializerMethodField()

    def get_url_descarga(self, obj):
        return f'/api/usuarios/documentos/{obj.pk}/descargar/'
    class Meta:
        model = DocumentoVerificacion
        fields = [
                    'id',
                    'tipo',
                    'archivo',
                    'url_descarga',
                    'estado',
                    'observacion',
                    'fecha_subida',
        ]

        read_only_fields = [
            'id',
            'estado',
            'observacion',
            'fecha_subida',
        ]

class AdminDocumentoVerificacionSerializer(serializers.ModelSerializer):
    profesional_id = serializers.IntegerField(
        source='perfil.id',
        read_only=True
    )
    username = serializers.CharField(
        source='perfil.usuario.username',
        read_only=True
    )
    email = serializers.EmailField(
        source='perfil.usuario.email',
        read_only=True
    )

    url_descarga = serializers.SerializerMethodField()

    def get_url_descarga(self, obj):
        return f'/api/usuarios/documentos/{obj.pk}/descargar/'
    class Meta:
        model = DocumentoVerificacion
        fields = [
            'id',
            'profesional_id',
            'username',
            'email',
            'tipo',
            'url_descarga',
            'estado',
            'observacion',
            'fecha_subida',
        ]

        read_only_fields = [
            'id',
            'profesional_id',
            'username',
            'email',
            'tipo',
            'archivo',
            'fecha_subida',
        ]

class MiPerfilSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='usuario.username',
        read_only=True
    )
    email = serializers.EmailField(
        source='usuario.email',
        required=False
    )
    first_name = serializers.CharField(
        source='usuario.first_name',
        required=False,
        allow_blank=True
    )
    last_name = serializers.CharField(
        source='usuario.last_name',
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Perfil
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'rol',
            'telefono',
            'direccion',
            'descripcion_profesional',
            'experiencia_anos',
            'estado_verificacion',
            'estado_identidad',
            'disponible',
        ]

        read_only_fields = [
            'rol',
            'estado_verificacion',
            'estado_identidad',
            'disponible',
        ]

    def update(self, instance, validated_data):
        datos_usuario = validated_data.pop('usuario', {})

        for campo, valor in datos_usuario.items():
            setattr(instance.usuario, campo, valor)

        if datos_usuario:
            instance.usuario.save()

        return super().update(instance, validated_data)
class ProfesionalDisponibleSerializer(serializers.ModelSerializer):
    profesional_id = serializers.IntegerField(
        source='profesional.id',
        read_only=True
    )

    username = serializers.CharField(
        source='profesional.usuario.username',
        read_only=True
    )

    descripcion_profesional = serializers.CharField(
        source='profesional.descripcion_profesional',
        read_only=True
    )

    experiencia_anos = serializers.IntegerField(
        source='profesional.experiencia_anos',
        read_only=True
    )

    class Meta:
        model = ServicioProfesional
        fields = [
            'profesional_id',
            'username',
            'descripcion_profesional',
            'experiencia_anos',
            'precio',
        ]