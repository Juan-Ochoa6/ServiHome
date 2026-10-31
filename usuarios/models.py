
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

    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    descripcion_profesional = models.TextField(blank=True)
    experiencia_anos = models.PositiveSmallIntegerField(default=0)
    disponible = models.BooleanField(default=True)

    # Microsoft Authenticator
    totp_secret = models.TextField(blank=True, default='')
    two_factor_enabled = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def set_totp_secret(self, secret):
        self.totp_secret = encrypt_totp_secret(secret)

    def get_totp_secret(self):
        return decrypt_totp_secret(self.totp_secret)

    def __str__(self):
        return f'{self.usuario.username} - {self.get_rol_display()}'
