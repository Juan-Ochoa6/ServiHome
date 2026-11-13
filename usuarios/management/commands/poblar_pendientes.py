from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from servicios.models import Servicio, ServicioProfesional
from usuarios.models import Perfil

User = get_user_model()

# Contraseña de los profesionales de prueba (solo para desarrollo).
CONTRASENA_PRUEBA = 'ServiHome2026*'

PROFESIONALES_PENDIENTES = [
    {
        'username': 'pedro_plomero',
        'first_name': 'Pedro',
        'last_name': 'Ramírez',
        'email': 'pedro@servihome.test',
        'estado': 'pendiente',
        'descripcion': 'Plomero con experiencia en instalaciones domiciliarias.',
        'experiencia': 5,
        'oferta': ('Reparación de fugas', 52000),
    },
    {
        'username': 'sofia_limpieza',
        'first_name': 'Sofía',
        'last_name': 'Herrera',
        'email': 'sofia@servihome.test',
        'estado': 'en_revision',
        'descripcion': 'Limpieza residencial y de oficinas.',
        'experiencia': 3,
        'oferta': ('Limpieza general del hogar', 70000),
    },
]


class Command(BaseCommand):
    help = (
        'Crea profesionales en revisión y ofertas pendientes para probar el '
        'panel de administración. Se puede repetir: vuelve a dejarlos pendientes.'
    )

    @transaction.atomic
    def handle(self, *args, **opciones):
        for datos in PROFESIONALES_PENDIENTES:
            self.crear_profesional_pendiente(datos)

        self.crear_oferta_pendiente_de_aprobado()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Datos pendientes listos.'))

    def obtener_servicio(self, nombre):
        servicio = Servicio.objects.filter(nombre=nombre).first()
        if servicio is None:
            raise CommandError(
                f'No existe el servicio "{nombre}". '
                'Ejecuta primero: python manage.py poblar_datos'
            )
        return servicio

    def crear_profesional_pendiente(self, datos):
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

        perfil = Perfil.objects.get(usuario=usuario)
        perfil.rol = 'profesional'
        perfil.estado_verificacion = datos['estado']
        perfil.disponible = False
        perfil.descripcion_profesional = datos['descripcion']
        perfil.experiencia_anos = datos['experiencia']
        perfil.save()

        nombre_servicio, precio = datos['oferta']
        ServicioProfesional.objects.update_or_create(
            servicio=self.obtener_servicio(nombre_servicio),
            profesional=perfil,
            defaults={
                'precio': Decimal(precio),
                'estado_aprobacion': 'pendiente',
            },
        )

    def crear_oferta_pendiente_de_aprobado(self):
        # Una oferta pendiente de un profesional ya aprobado (laura_electricista).
        try:
            perfil = Perfil.objects.get(usuario__username='laura_electricista')
        except Perfil.DoesNotExist:
            raise CommandError(
                'No existe laura_electricista. '
                'Ejecuta primero: python manage.py poblar_datos'
            )

        ServicioProfesional.objects.update_or_create(
            servicio=self.obtener_servicio('Limpieza general del hogar'),
            profesional=perfil,
            defaults={
                'precio': Decimal(65000),
                'estado_aprobacion': 'pendiente',
            },
        )
        self.stdout.write('  + Oferta pendiente de laura_electricista')