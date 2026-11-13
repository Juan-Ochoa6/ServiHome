
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.db import close_old_connections, connections

logger = logging.getLogger(__name__)


def enviar_correo(destinatario, asunto, mensaje):
    if not destinatario:
        logger.warning(
            'No se envió el correo porque el destinatario no tiene email.'
        )
        return False

    def tarea_envio():
        close_old_connections()

        try:
            resultado = send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )

            if resultado != 1:
                logger.warning(
                    'No se pudo confirmar el envío del correo a %s',
                    destinatario,
                )

        except Exception:
            logger.exception(
                'Error al enviar correo a %s',
                destinatario,
            )

        finally:
            connections.close_all()

    try:
        hilo = threading.Thread(
            target=tarea_envio,
            daemon=True,
        )
        hilo.start()
        return True

    except Exception:
        logger.exception('No se pudo iniciar el envío del correo.')
        return False
