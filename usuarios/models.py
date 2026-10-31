
from django.db import models
from django.contrib.auth.models import User

from .security import encrypt_totp_secret, decrypt_totp_secret


class Perfil(models.Model):

    ROLES = [
        ('cliente', 'Cliente'),
        ('profesional', 'Profesional'),
    ]

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='cliente'
    )
    ESTADOS_VERIFICACION = [
    ('no_aplica', 'No aplica'),
    ('pendiente', 'Pendiente de revisión'),
    ('en_revision', 'En revisión'),
    ('aprobado', 'Aprobado'),
    ('rechazado', 'Rechazado'),
    ]
    estado_verificacion = models.CharField(
    max_length=20,
    choices=ESTADOS_VERIFICACION,
    default='no_aplica'
    )

    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    descripcion_profesional = models.TextField(blank=True)
    experiencia_anos = models.PositiveSmallIntegerField(default=0)
    disponible = models.BooleanField(default=True)

    # Microsoft Authenticator
    totp_secret = models.TextField(blank=True, default='')
    two_factor_enabled = models.BooleanField(default=False)

# Seguridad: último código TOTP utilizado
    last_otp_at = models.DateTimeField(null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def set_totp_secret(self, secret):
        self.totp_secret = encrypt_totp_secret(secret)

    def get_totp_secret(self):
        return decrypt_totp_secret(self.totp_secret)

    def __str__(self):
        return f'{self.usuario.username} - {self.get_rol_display()}'


class DesafioLogin(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='desafios_login'
    )

    token_hash = models.CharField(
        max_length=64,
        unique=True
    )

    consumido = models.BooleanField(default=False)

    intentos_fallidos = models.PositiveSmallIntegerField(default=0)

    bloqueado = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Desafío de {self.usuario.username}'

class CodigoRecuperacionMFA(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='codigos_recuperacion_mfa'
    )

    codigo_hash = models.CharField(
        max_length=64,
        unique=True
    )

    utilizado = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_uso = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Código de recuperación de {self.usuario.username}'
