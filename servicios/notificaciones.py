import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import BadHeaderError
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def enviar_correo(destinatario, asunto, mensaje):
    if not destinatario:
        logger.warning(
            'No se envió el correo porque el destinatario no tiene email.'
        )
        return False

    try:
        resultado = send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )

        return resultado == 1

    except Exception:
        logger.exception(
            'Error al enviar correo a %s',
            destinatario
        )
        return False