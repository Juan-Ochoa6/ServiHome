from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from servicios.models import Categoria, Servicio, ServicioProfesional
from usuarios.models import Perfil

User = get_user_model()

# Contraseña de los profesionales de prueba (solo para desarrollo).
CONTRASENA_PRUEBA = 'ServiHome2026*'

CATALOGO = {
    'Plomería': {
        'descripcion': 'Instalación y reparación de tuberías.',
        'servicios': [
            ('Reparación de fugas', 'Detección y arreglo de fugas en tuberías', 50000),
            ('Destape de cañerías', 'Destape de lavamanos, duchas y desagües', 60000),
        ],
    },
    'Electricidad': {
        'descripcion': 'Instalaciones y reparaciones eléctricas.',
        'servicios': [
            ('Instalación de tomacorrientes', 'Instalación y cambio de tomacorrientes', 40000),
            ('Revisión del sistema eléctrico', 'Diagnóstico completo del sistema eléctrico', 70000),
        ],
    },
    'Limpieza': {
        'descripcion': 'Limpieza y mantenimiento del hogar.',
        'servicios': [
            ('Limpieza general del hogar', 'Limpieza completa de la vivienda', 80000),
            ('Limpieza profunda de cocina y baños', 'Limpieza a fondo de cocina y baños', 120000),
        ],
    },
}

PROFESIONALES = [
    {
        'username': 'carlos_plomero',
        'first_name': 'Carlos',
        'last_name': 'Rodríguez',
        'email': 'carlos@servihome.test',
        'descripcion': 'Plomero con experiencia en instalaciones y reparaciones residenciales.',
        'experiencia': 8,
        'ofertas': [('Reparación de fugas', 50000), ('Destape de cañerías', 60000)],
    },
    {
        'username': 'laura_electricista',
        'first_name': 'Laura',
        'last_name': 'Martínez',
        'email': 'laura@servihome.test',
        'descripcion': 'Electricista certificada para instalaciones eléctricas del hogar.',
        'experiencia': 6,
        'ofertas': [
            ('Instalación de tomacorrientes', 40000),
            ('Revisión del sistema eléctrico', 70000),
        ],
    },
    {
        'username': 'andres_limpieza',
        'first_name': 'Andrés',
        'last_name': 'Gómez',
        'email': 'andres@servihome.test',
        'descripcion': 'Limpieza general y mantenimiento del hogar.',
        'experiencia': 4,
        'ofertas': [
            ('Limpieza general del hogar', 80000),
            ('Limpieza profunda de cocina y baños', 120000),
        ],
    },
    {
        'username': 'marta_multiple',
        'first_name': 'Marta',
        'last_name': 'Pérez',
        'email': 'marta@servihome.test',
        'descripcion': 'Atiende arreglos de plomería y limpieza del hogar.',
        'experiencia': 10,
        'ofertas': [('Reparación de fugas', 55000), ('Limpieza general del hogar', 75000)],
    },
]


class Command(BaseCommand):
    help = (
        'Crea categorías, servicios, profesionales aprobados y sus ofertas '
        'de prueba. Se puede ejecutar varias veces sin duplicar datos.'
    )

    @transaction.atomic
    def handle(self, *args, **opciones):
        servicios = self.crear_catalogo()
        self.crear_profesionales(servicios)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Datos de prueba listos.'))
        self.stdout.write(f'Contraseña de los profesionales: {CONTRASENA_PRUEBA}')

    def crear_catalogo(self):
        servicios = {}

        for nombre_categoria, datos in CATALOGO.items():
            categoria, creada = Categoria.objects.get_or_create(
                nombre=nombre_categoria,
                defaults={'descripcion': datos['descripcion'], 'activa': True},
            )
            if creada:
                self.stdout.write(f'  + Categoría creada: {nombre_categoria}')

            for nombre, descripcion, precio in datos['servicios']:
                servicio, creado = Servicio.objects.get_or_create(
                    categoria=categoria,
                    nombre=nombre,
                    defaults={
                        'descripcion': descripcion,
                        'precio_base': Decimal(precio),
                        'activo': True,
                    },
                )
                if creado:
                    self.stdout.write(f'  + Servicio creado: {nombre}')
                servicios[nombre] = servicio

        return servicios

    def crear_profesionales(self, servicios):
        for datos in PROFESIONALES:
            usuario, creado = User.objects.get_or_create(
                username=datos['username'],
                defaults={
                    'first_name': datos['first_name'],
                    'last_name': datos['last_name'],
                    'email': datos['email'],
                },
            )

            if creado:
                usuario.set_password(CONTRASENA_PRUEBA)
                usuario.save()
                self.stdout.write(f'  + Profesional creado: {datos["username"]}')

            # La señal de usuarios ya creó el perfil al crear el usuario.
            perfil = Perfil.objects.get(usuario=usuario)
            perfil.rol = 'profesional'
            perfil.estado_verificacion = 'aprobado'
            perfil.disponible = True
            perfil.descripcion_profesional = datos['descripcion']
            perfil.experiencia_anos = datos['experiencia']
            perfil.save()

            for nombre_servicio, precio in datos['ofertas']:
                ServicioProfesional.objects.update_or_create(
                    servicio=servicios[nombre_servicio],
                    profesional=perfil,
                    defaults={
                        'precio': Decimal(precio),
                        'estado_aprobacion': 'aprobado',
                    },
                )