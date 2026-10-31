from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Perfil


class RegistroUsuarioSerializer(serializers.ModelSerializer):
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