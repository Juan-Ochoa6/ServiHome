
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import DesafioLogin


class Command(BaseCommand):

    help = 'Elimina desafíos de inicio de sesión con más de 10 minutos.'

    def handle(self, *args, **options):

        limite = timezone.now() - timedelta(minutes=10)

        eliminados, detalle = DesafioLogin.objects.filter(
            fecha_creacion__lt=limite
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Limpieza completada. Registros eliminados: {eliminados}'
            )
        )
