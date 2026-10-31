
import base64
import hashlib
import hmac

from datetime import datetime, timezone as datetime_timezone
from io import BytesIO

import pyotp
import qrcode

from django.contrib.auth import authenticate, get_user_model
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.models import DesafioLogin


User = get_user_model()


def registrar_desafio(usuario, challenge):
    """
    Registra un desafío de inicio de sesión.
    Guarda un hash del desafío, no el token original.
    """

    token_hash = hashlib.sha256(
        challenge.encode('utf-8')
    ).hexdigest()

    DesafioLogin.objects.create(
        usuario=usuario,
        token_hash=token_hash
    )


def validar_codigo_totp_unico(perfil, codigo):
    """
    Valida el código TOTP y evita que el mismo intervalo
    de tiempo se utilice más de una vez.
    """

    with transaction.atomic():

        perfil_bloqueado = (
            perfil.__class__.objects
            .select_for_update()
            .get(pk=perfil.pk)
        )

        secret = perfil_bloqueado.get_totp_secret()

        if not secret:
            return False

        totp = pyotp.TOTP(secret)
        intervalo = totp.interval

        instante_actual = int(timezone.now().timestamp())
        intervalo_actual = instante_actual // intervalo

        ultimo_intervalo = None

        if perfil_bloqueado.last_otp_at:
            ultimo_intervalo = (
                int(perfil_bloqueado.last_otp_at.timestamp())
                // intervalo
            )

        for intervalo_codigo in range(
            intervalo_actual - 1,
            intervalo_actual + 2
        ):

            if ultimo_intervalo is not None:
                if intervalo_codigo <= ultimo_intervalo:
                    continue

            codigo_esperado = totp.at(
                intervalo_codigo * intervalo
            )

            if hmac.compare_digest(codigo, codigo_esperado):

                perfil_bloqueado.last_otp_at = datetime.fromtimestamp(
                    intervalo_codigo * intervalo,
                    tz=datetime_timezone.utc
                )

                perfil_bloqueado.save(
                    update_fields=['last_otp_at']
                )

                return True

        return False


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

    secret = pyotp.random_base32()

    perfil.set_totp_secret(secret)
    perfil.save()

    totp = pyotp.TOTP(secret)

    uri = totp.provisioning_uri(
        name=request.user.email or request.user.username,
        issuer_name='ServiHome'
    )

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

    codigo = str(
        request.data.get('codigo', '')
    ).strip()

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
        perfil.get_totp_secret()

    except ImproperlyConfigured:
        return Response(
            {'error': 'No se pudo recuperar la clave del autenticador.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if validar_codigo_totp_unico(perfil, codigo):

        perfil.refresh_from_db()
        perfil.two_factor_enabled = True

        perfil.save(
            update_fields=['two_factor_enabled']
        )

        return Response({
            'mensaje': 'Microsoft Authenticator quedó activado correctamente.'
        })

    return Response(
        {'error': 'El código es incorrecto, ha caducado o ya fue utilizado.'},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def iniciar_sesion(request):
    """
    Valida usuario y contraseña.
    No entrega JWT hasta completar la verificación MFA.
    """

    username = str(
        request.data.get('username', '')
    ).strip()

    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': 'Debes ingresar usuario y contraseña.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario = authenticate(
        request,
        username=username,
        password=password
    )

    if usuario is None:
        return Response(
            {'error': 'Usuario o contraseña incorrectos.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not usuario.is_active:
        return Response(
            {'error': 'Esta cuenta está desactivada.'},
            status=status.HTTP_403_FORBIDDEN
        )

    perfil = usuario.perfil

    challenge = signing.dumps(
        {'user_id': usuario.pk},
        salt='servihome.mfa.login'
    )

    registrar_desafio(usuario, challenge)

    if perfil.two_factor_enabled:
        return Response({
            'mensaje': 'Ingresa el código de Microsoft Authenticator.',
            'mfa_required': True,
            'challenge': challenge
        })

    if not perfil.totp_secret:

        secret = pyotp.random_base32()

        perfil.set_totp_secret(secret)

        perfil.save(
            update_fields=['totp_secret']
        )

    else:
        secret = perfil.get_totp_secret()

    uri = pyotp.TOTP(secret).provisioning_uri(
        name=usuario.email or usuario.username,
        issuer_name='ServiHome'
    )

    qr = qrcode.make(uri)

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    imagen_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')

    return Response({
        'mensaje': 'Configura Microsoft Authenticator para continuar.',
        'mfa_setup_required': True,
        'challenge': challenge,
        'codigo_qr': f'data:image/png;base64,{imagen_base64}'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verificar_codigo_login(request):
    """
    Verifica el código MFA y consume el challenge
    una sola vez antes de entregar los JWT.

    Permite máximo cinco intentos incorrectos
    por desafío de inicio de sesión.
    """

    challenge = request.data.get('challenge', '')

    codigo = str(
        request.data.get('codigo', '')
    ).strip()

    if not challenge or not codigo.isdigit() or len(codigo) != 6:
        return Response(
            {'error': 'Debes enviar el desafío y un código de seis dígitos.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        datos = signing.loads(
            challenge,
            salt='servihome.mfa.login',
            max_age=600
        )

    except SignatureExpired:
        return Response(
            {
                'error': 'El proceso de inicio de sesión ha caducado. Inténtalo nuevamente.'
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    except BadSignature:
        return Response(
            {'error': 'El desafío de autenticación no es válido.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token_hash = hashlib.sha256(
        challenge.encode('utf-8')
    ).hexdigest()

    try:

        with transaction.atomic():

            desafio = (
                DesafioLogin.objects
                .select_for_update()
                .get(
                    token_hash=token_hash,
                    usuario_id=datos['user_id']
                )
            )

            if desafio.consumido:
                return Response(
                    {'error': 'Este desafío ya fue utilizado.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if desafio.bloqueado:
                return Response(
                    {
                        'error': 'Este desafío está bloqueado por superar los cinco intentos. Inicia sesión nuevamente.'
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            usuario = User.objects.get(
                pk=datos['user_id'],
                is_active=True
            )

            perfil = usuario.perfil

            secret = perfil.get_totp_secret()

            if not secret or not validar_codigo_totp_unico(
                perfil,
                codigo
            ):

                desafio.intentos_fallidos += 1

                if desafio.intentos_fallidos >= 5:
                    desafio.bloqueado = True

                desafio.save(
                    update_fields=[
                        'intentos_fallidos',
                        'bloqueado'
                    ]
                )

                if desafio.bloqueado:
                    return Response(
                        {
                            'error': 'Has superado los cinco intentos. Este desafío ha sido bloqueado. Inicia sesión nuevamente.',
                            'intentos_restantes': 0
                        },
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                return Response(
                    {
                        'error': 'El código es incorrecto, ha caducado o ya fue utilizado.',
                        'intentos_restantes': 5 - desafio.intentos_fallidos
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            desafio.consumido = True

            desafio.save(
                update_fields=['consumido']
            )

            if not perfil.two_factor_enabled:

                perfil.two_factor_enabled = True

                perfil.save(
                    update_fields=['two_factor_enabled']
                )

            refresh = RefreshToken.for_user(usuario)

            respuesta = {
                'mensaje': 'Autenticación completada correctamente.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'usuario': usuario.username,
                'rol': perfil.rol
            }

        return Response(respuesta)

    except DesafioLogin.DoesNotExist:
        return Response(
            {'error': 'El desafío no existe o ya no es válido.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except (User.DoesNotExist, AttributeError, ImproperlyConfigured):
        return Response(
            {'error': 'No se pudo validar la cuenta.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
