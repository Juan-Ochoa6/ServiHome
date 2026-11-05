
from django.db import models
from django.core.exceptions import ValidationError


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
    ESTADOS_APROBACION = [
        ('pendiente', 'Pendiente de aprobación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    estado_aprobacion = models.CharField(
        max_length=20,
        choices=ESTADOS_APROBACION,
        default='pendiente'
    )

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

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['servicio', 'profesional'],
                name='servicio_profesional_unico'
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gte=30000),
                name='oferta_precio_min_30000'
            ),
        ]

    def clean(self):
        if self.precio is not None and self.precio < 30000:
            raise ValidationError({
                'precio': 'El precio mínimo permitido es de $30.000 COP.'
            })

        if self.profesional_id:
            if self.profesional.rol != 'profesional':
                raise ValidationError({
                    'profesional': 'El perfil debe pertenecer a un profesional.'
                })

    def __str__(self):
        return f'{self.profesional} - {self.servicio}'

class TrabajoPortafolio(models.Model):
    profesional = models.ForeignKey(
        'usuarios.Perfil',
        on_delete=models.CASCADE,
        related_name='trabajos_portafolio'
    )

    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trabajos_portafolio'
    )

    titulo = models.CharField(max_length=150)

    descripcion = models.TextField()

    imagen = models.ImageField(
        upload_to='portafolio_profesionales/'
    )

    fecha_publicacion = models.DateTimeField(
        auto_now_add=True
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return (
            f'{self.titulo} - '
            f'{self.profesional.usuario.username}'
        )
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(precio_acordado__isnull=True) |
                    models.Q(precio_acordado__gte=30000)
                ),
                name='solicitud_precio_min_30000'
            ),
        ]

    def clean(self):
        if (
            self.precio_acordado is not None
            and self.precio_acordado < 30000
        ):
            raise ValidationError({
                'precio_acordado': 'El precio mínimo permitido es de $30.000 COP.'
            })

    def __str__(self):
        return f'Solicitud #{self.pk} - {self.get_estado_display()}'


class PropuestaPrecio(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('reemplazada', 'Reemplazada'),
    ]

    solicitud = models.ForeignKey(
        SolicitudServicio,
        on_delete=models.CASCADE,
        related_name='propuestas'
    )

    proponente = models.ForeignKey(
        'usuarios.Perfil',
        on_delete=models.PROTECT,
        related_name='propuestas_precio'
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio__gte=30000),
                name='propuesta_precio_min_30000'
            ),
        ]

    def clean(self):
        if self.precio is not None and self.precio < 30000:
            raise ValidationError({
                'precio': 'El precio mínimo permitido es de $30.000 COP.'
            })

        if self.proponente_id and self.solicitud_id:
            participantes = [
                self.solicitud.cliente_id,
                self.solicitud.profesional_id,
            ]

            if self.proponente_id not in participantes:
                raise ValidationError({
                    'proponente': (
                        'Solo el cliente o el profesional de la solicitud '
                        'pueden realizar propuestas.'
                    )
                })

    def __str__(self):
        return f'Propuesta #{self.pk} - {self.precio}'
