
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='servicios'
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    profesionales = models.ManyToManyField(
        'usuarios.Perfil',
        through='ServicioProfesional',
        related_name='servicios_ofrecidos',
        blank=True
    )

    def __str__(self):
        return self.nombre


class ServicioProfesional(models.Model):
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='ofertas_profesionales'
    )
    profesional = models.ForeignKey(
        'usuarios.Perfil',
        on_delete=models.CASCADE,
        related_name='ofertas_servicios'
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['servicio', 'profesional'],
                name='servicio_profesional_unico'
            )
        ]

    def __str__(self):
        return f'{self.profesional} - {self.servicio}'


class SolicitudServicio(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('en_proceso', 'En proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(
        'usuarios.Perfil',
        on_delete=models.PROTECT,
        related_name='solicitudes_realizadas'
    )
    profesional = models.ForeignKey(
        'usuarios.Perfil',
        on_delete=models.PROTECT,
        related_name='solicitudes_recibidas'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='solicitudes'
    )
    descripcion = models.TextField()
    direccion_servicio = models.CharField(max_length=255)
    fecha_solicitada = models.DateTimeField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )
    precio_acordado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Solicitud #{self.pk} - {self.get_estado_display()}'
