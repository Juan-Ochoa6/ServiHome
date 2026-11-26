import base64
import json
import logging
import threading
import urllib.parse
import urllib.request

from email.mime.text import MIMEText

from django.conf import settings
from django.db import close_old_connections, connections


logger = logging.getLogger(__name__)


def obtener_access_token():
    datos = urllib.parse.urlencode({
        'client_id': settings.GMAIL_CLIENT_ID,
        'client_secret': settings.GMAIL_CLIENT_SECRET,
        'refresh_token': settings.GMAIL_REFRESH_TOKEN,
        'grant_type': 'refresh_token',
    }).encode('utf-8')

    solicitud = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=datos,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )

    with urllib.request.urlopen(solicitud, timeout=15) as respuesta:
        resultado = json.loads(respuesta.read().decode('utf-8'))

    return resultado['access_token']


def enviar_por_gmail_api(destinatario, asunto, mensaje):
    access_token = obtener_access_token()

    correo = MIMEText(mensaje, 'plain', 'utf-8')
    correo['To'] = destinatario
    correo['From'] = settings.DEFAULT_FROM_EMAIL
    correo['Subject'] = asunto

    correo_codificado = base64.urlsafe_b64encode(
        correo.as_bytes()
    ).decode('ascii').rstrip('=')

    datos = json.dumps({
        'raw': correo_codificado,
    }).encode('utf-8')

    solicitud = urllib.request.Request(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        data=datos,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    with urllib.request.urlopen(solicitud, timeout=15) as respuesta:
        resultado = json.loads(respuesta.read().decode('utf-8'))

    logger.info(
        'Correo enviado correctamente a %s. ID: %s',
        destinatario,
        resultado.get('id'),
    )


def enviar_correo(destinatario, asunto, mensaje):
    if not destinatario:
        logger.warning(
            'No se envió el correo porque el destinatario no tiene email.'
        )
        return False

    def tarea_envio():
        close_old_connections()

        try:
            enviar_por_gmail_api(
                destinatario,
                asunto,
                mensaje,
            )

        except Exception:
            logger.exception(
                'Error al enviar correo mediante Gmail API a %s',
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