
from django.db import models
from django.contrib.auth.models import User


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

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.username} - {self.get_rol_display()}'
