
import base64
from io import BytesIO

import pyotp
import qrcode

from django.http import HttpResponse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def configurar_mfa(request):
    """
    Genera una clave TOTP y un código QR
    para configurar Microsoft Authenticator.
    """

    perfil = request.user.perfil

    if perfil.two_factor_enabled:
        return Response(
            {'error': 'La verificación en dos pasos ya está activada.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Generar clave secreta individual
    secret = pyotp.random_base32()

    # Guardar la clave cifrada
    perfil.set_totp_secret(secret)
    perfil.save()

    # Crear URI compatible con Microsoft Authenticator
    totp = pyotp.TOTP(secret)

    uri = totp.provisioning_uri(
        name=request.user.email or request.user.username,
        issuer_name='ServiHome'
    )

    # Generar código QR
    qr = qrcode.make(uri)

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    imagen_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')

    return Response({
        'mensaje': 'Escanea el código QR con Microsoft Authenticator.',
        'codigo_qr': f'data:image/png;base64,{imagen_base64}'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_mfa(request):
    """
    Comprueba el código de Microsoft Authenticator
    y activa la verificación en dos pasos.
    """

    perfil = request.user.perfil
    codigo = str(request.data.get('codigo', '')).strip()

    if perfil.two_factor_enabled:
        return Response(
            {'error': 'La verificación en dos pasos ya está activada.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not perfil.totp_secret:
        return Response(
            {'error': 'Primero debes configurar el autenticador.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (codigo.isdigit() and len(codigo) == 6):
        return Response(
            {'error': 'Debes ingresar un código de seis dígitos.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        secret = perfil.get_totp_secret()
    except ImproperlyConfigured:
        return Response(
            {'error': 'No se pudo recuperar la clave del autenticador.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    totp = pyotp.TOTP(secret)

    if totp.verify(codigo, valid_window=1):
        perfil.two_factor_enabled = True
        perfil.save(update_fields=['two_factor_enabled'])

        return Response({
            'mensaje': 'Microsoft Authenticator quedó activado correctamente.'
        })

    return Response(
        {'error': 'El código es incorrecto o ha caducado.'},
        status=status.HTTP_400_BAD_REQUEST
    )
