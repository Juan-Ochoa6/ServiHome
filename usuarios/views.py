
import base64
import hashlib
import secrets
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

from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAdminUser,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    inline_serializer,
)

from usuarios.models import DesafioLogin, CodigoRecuperacionMFA
from .serializers import RegistroUsuarioSerializer
from .models import Perfil


User = get_user_model()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def registrar_desafio(usuario, challenge):
    """Guarda el hash del desafío para validar su registro y uso."""

    token_hash = hashlib.sha256(
        challenge.encode('utf-8')
    ).hexdigest()

    return DesafioLogin.objects.create(
        usuario=usuario,
        token_hash=token_hash
    )


def generar_codigos_recuperacion(usuario):
    """Genera ocho códigos y almacena solamente sus hashes."""

    codigos = [
        secrets.token_hex(16).upper()
        for _ in range(8)
    ]

    with transaction.atomic():
        CodigoRecuperacionMFA.objects.filter(
            usuario=usuario
        ).delete()

        registros = []

        for codigo in codigos:
            codigo_hash = hashlib.sha256(
                codigo.encode('utf-8')
            ).hexdigest()

            registros.append(
                CodigoRecuperacionMFA(
                    usuario=usuario,
                    codigo_hash=codigo_hash
                )
            )

        CodigoRecuperacionMFA.objects.bulk_create(registros)

    return codigos


def validar_codigo_totp_unico(perfil, codigo):
    """Valida un TOTP e impide reutilizar el mismo intervalo."""

    if not codigo or not codigo.isdigit() or len(codigo) != 6:
        return False

    try:
        with transaction.atomic():
            perfil_bloqueado = type(perfil).objects.select_for_update().get(
                pk=perfil.pk
            )

            secret = perfil_bloqueado.get_totp_secret()

            if not secret:
                return False

            totp = pyotp.TOTP(secret)

            instante = timezone.now()
            timestamp = instante.timestamp()

            if not totp.verify(
                codigo,
                for_time=timestamp,
                valid_window=1
            ):
                return False

            instante_codigo = totp.timecode(
                datetime.fromtimestamp(
                    timestamp,
                    tz=datetime_timezone.utc
                )
            )

            instante_codigo = datetime.fromtimestamp(
                instante_codigo * totp.interval,
                tz=datetime_timezone.utc
            )

            if perfil_bloqueado.last_otp_at is not None:
                ultimo = perfil_bloqueado.last_otp_at

                if timezone.is_naive(ultimo):
                    ultimo = timezone.make_aware(
                        ultimo,
                        datetime_timezone.utc
                    )

                if instante_codigo <= ultimo:
                    return False

            perfil_bloqueado.last_otp_at = instante_codigo
            perfil_bloqueado.save(update_fields=['last_otp_at'])

            return True

    except (AttributeError, ImproperlyConfigured, ValueError):
        return False


def obtener_hash_challenge(challenge):
    return hashlib.sha256(
        challenge.encode('utf-8')
    ).hexdigest()


def generar_codigo_qr(usuario, perfil):
    """Genera el código QR para configurar Microsoft Authenticator."""

    if not perfil.totp_secret:
        secret = pyotp.random_base32()
        perfil.set_totp_secret(secret)
        perfil.save(update_fields=['totp_secret'])
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

    return f'data:image/png;base64,{imagen_base64}'


# =========================================================
# CONFIGURACIÓN MFA
# =========================================================

@extend_schema(
    tags=['MFA'],
    summary='Configurar autenticación MFA',
    description='Genera un código QR para configurar Microsoft Authenticator.',
    request=None,
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='ConfigurarMFARespuesta',
                fields={
                    'mensaje': serializers.CharField(),
                    'codigo_qr': serializers.CharField(),
                },
            ),
            description='Código QR generado correctamente.',
        ),
        400: OpenApiResponse(description='MFA ya está activado.'),
        401: OpenApiResponse(description='Usuario no autenticado.'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def configurar_mfa(request):
    """Genera la información para configurar MFA."""

    perfil = request.user.perfil

    if perfil.two_factor_enabled:
        return Response(
            {'error': 'MFA ya está activado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    imagen_base64 = generar_codigo_qr(
        request.user,
        perfil
    )

    return Response({
        'mensaje': 'Escanea el código QR con tu aplicación autenticadora.',
        'codigo_qr': imagen_base64
    })


@extend_schema(
    tags=['MFA'],
    summary='Verificar y activar MFA',
    description='Verifica el código TOTP y activa la autenticación multifactor.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'codigo': {
                    'type': 'string',
                    'description': 'Código de seis dígitos de la aplicación autenticadora.',
                    'minLength': 6,
                    'maxLength': 6,
                },
            },
            'required': ['codigo'],
        },
    },
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='VerificarMFARespuesta',
                fields={
                    'mensaje': serializers.CharField(),
                    'codigos_recuperacion': serializers.ListField(
                        child=serializers.CharField(),
                    ),
                },
            ),
            description='MFA activado y códigos de recuperación generados.',
        ),
        400: OpenApiResponse(
            description='Código incorrecto, MFA ya activado o configuración pendiente.',
        ),
        401: OpenApiResponse(description='Usuario no autenticado.'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_mfa(request):
    """Verifica el código y activa MFA."""

    codigo = str(request.data.get('codigo', '')).strip()
    perfil = request.user.perfil

    if perfil.two_factor_enabled:
        return Response(
            {'error': 'MFA ya está activado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not perfil.totp_secret:
        return Response(
            {'error': 'Primero debes configurar MFA.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not validar_codigo_totp_unico(perfil, codigo):
        return Response(
            {'error': 'Código de autenticación incorrecto.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():
        perfil = type(perfil).objects.select_for_update().get(
            pk=perfil.pk
        )

        if perfil.two_factor_enabled:
            return Response(
                {'error': 'MFA ya está activado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        perfil.two_factor_enabled = True
        perfil.save(update_fields=['two_factor_enabled'])

        codigos = generar_codigos_recuperacion(request.user)

    return Response({
        'mensaje': 'MFA activado correctamente.',
        'codigos_recuperacion': codigos
    })


# =========================================================
# INICIO DE SESIÓN
# =========================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Iniciar sesión',
    description=(
        'Valida las credenciales y genera un desafío para completar '
        'la autenticación MFA.'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string', 'format': 'password'}
            },
            'required': ['username', 'password']
        }
    },
    responses={
        200: OpenApiResponse(description='Desafío MFA generado.'),
        400: OpenApiResponse(description='Faltan credenciales.'),
        401: OpenApiResponse(description='Credenciales incorrectas.'),
        403: OpenApiResponse(description='Cuenta desactivada.')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def iniciar_sesion(request):
    """Valida usuario y contraseña sin entregar JWT todavía."""

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
        {
            'user_id': usuario.pk,
            'nonce': secrets.token_urlsafe(16)
        },
        salt='servihome.mfa.login'
    )

    registrar_desafio(usuario, challenge)

    if perfil.two_factor_enabled:
        return Response({
            'mensaje': 'Ingresa el código de Microsoft Authenticator.',
            'mfa_required': True,
            'challenge': challenge
        })

    imagen_base64 = generar_codigo_qr(
        usuario,
        perfil
    )

    return Response({
        'mensaje': 'Configura Microsoft Authenticator para continuar.',
        'mfa_setup_required': True,
        'challenge': challenge,
        'codigo_qr': imagen_base64
    })


# =========================================================
# VERIFICACIÓN MFA DURANTE EL LOGIN
# =========================================================

@extend_schema(
    tags=['Autenticación'],
    summary='Verificar código MFA durante el login',
    description=(
        'Valida el desafío y un código TOTP o de recuperación. '
        'Si son correctos, entrega los tokens JWT.'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'challenge': {'type': 'string'},
                'codigo': {'type': 'string'}
            },
            'required': ['challenge', 'codigo']
        }
    },
    responses={
        200: OpenApiResponse(description='Autenticación exitosa y tokens JWT.'),
        400: OpenApiResponse(description='Código incorrecto o formato inválido.'),
        401: OpenApiResponse(description='Desafío inválido, vencido o bloqueado.'),
        403: OpenApiResponse(description='Cuenta desactivada.')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verificar_codigo_login(request):
    """Valida el desafío y el código MFA antes de entregar JWT."""

    challenge = request.data.get('challenge')
    codigo = str(request.data.get('codigo', '')).strip()

    # 1. Comprobar los campos obligatorios.
    if not challenge or not codigo:
        return Response(
            {'error': 'Debes proporcionar el desafío y el código.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 2. Validar el formato antes de consumir intentos.
    es_totp = len(codigo) == 6 and codigo.isdigit()

    es_recuperacion = (
        len(codigo) == 32
        and all(
            caracter in '0123456789ABCDEFabcdef'
            for caracter in codigo
        )
    )

    if not es_totp and not es_recuperacion:
        return Response(
            {'error': 'El formato del código es incorrecto.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 3. Validar el desafío firmado.
    try:
        datos = signing.loads(
            challenge,
            salt='servihome.mfa.login',
            max_age=600
        )
    except SignatureExpired:
        return Response(
            {'error': 'El desafío ha caducado.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except BadSignature:
        return Response(
            {'error': 'El desafío no es válido.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    usuario_id = datos.get('user_id')

    if not usuario_id or not datos.get('nonce'):
        return Response(
            {'error': 'El desafío no es válido.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token_hash = obtener_hash_challenge(challenge)

    # 4. Bloquear el desafío durante su validación.
    with transaction.atomic():

        try:
            desafio = DesafioLogin.objects.select_for_update().get(
                usuario_id=usuario_id,
                token_hash=token_hash
            )
        except DesafioLogin.DoesNotExist:
            return Response(
                {'error': 'El desafío no está registrado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if desafio.consumido:
            return Response(
                {'error': 'El desafío ya fue utilizado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if desafio.bloqueado:
            return Response(
                {'error': 'El desafío está bloqueado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 5. Obtener el usuario y su perfil.
        try:
            usuario = User.objects.get(pk=usuario_id)
            perfil = usuario.perfil
        except (User.DoesNotExist, AttributeError):
            return Response(
                {'error': 'Usuario no encontrado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not usuario.is_active:
            return Response(
                {'error': 'Esta cuenta está desactivada.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 6. Validar TOTP o código de recuperación.
        codigo_valido = False

        if es_recuperacion and perfil.two_factor_enabled:

            codigo_hash = hashlib.sha256(
                codigo.upper().encode('utf-8')
            ).hexdigest()

            registro = CodigoRecuperacionMFA.objects.select_for_update().filter(
                usuario=usuario,
                codigo_hash=codigo_hash,
                utilizado=False
            ).first()

            if registro:
                registro.utilizado = True
                registro.fecha_uso = timezone.now()
                registro.save(
                    update_fields=['utilizado', 'fecha_uso']
                )

                codigo_valido = True

        elif es_totp:

            codigo_valido = validar_codigo_totp_unico(
                perfil,
                codigo
            )

        # 7. Controlar los intentos fallidos.
        if not codigo_valido:

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
                    {'error': 'Demasiados intentos. Desafío bloqueado.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            return Response({
                'error': 'Código de autenticación incorrecto.',
                'intentos_restantes': 5 - desafio.intentos_fallidos
            }, status=status.HTTP_400_BAD_REQUEST)

        # 8. Consumir el desafío.
        desafio.consumido = True
        desafio.save(update_fields=['consumido'])

        # 9. Activar MFA si es la primera autenticación.
        primera_activacion = not perfil.two_factor_enabled

        if primera_activacion:
            perfil.two_factor_enabled = True
            perfil.save(update_fields=['two_factor_enabled'])

            codigos_recuperacion = generar_codigos_recuperacion(
                usuario
            )
        else:
            codigos_recuperacion = None

        # 10. Generar JWT.
        refresh = RefreshToken.for_user(usuario)

        respuesta = {
            'mensaje': 'Inicio de sesión exitoso.',
            'usuario': usuario.username,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

        if codigos_recuperacion is not None:
            respuesta['codigos_recuperacion'] = codigos_recuperacion

        return Response(
            respuesta,
            status=status.HTTP_200_OK
        )


# =========================================================
# REGISTRO DE USUARIOS
# =========================================================

@extend_schema(
    tags=['Usuarios'],
    summary='Registrar usuario',
    description='Registra un cliente o profesional en ServiHome.',
    request=RegistroUsuarioSerializer,
    responses={
        201: OpenApiResponse(description='Usuario registrado correctamente.'),
        400: OpenApiResponse(description='Datos de registro inválidos.')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_usuario(request):
    serializer = RegistroUsuarioSerializer(data=request.data)

    if serializer.is_valid():
        usuario = serializer.save()
        perfil = Perfil.objects.get(usuario=usuario)

        return Response(
            {
                'mensaje': 'Usuario registrado correctamente.',
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'perfil': {
                        'id': perfil.id,
                        'rol': perfil.rol,
                        'telefono': perfil.telefono,
                        'direccion': perfil.direccion,
                        'disponible': perfil.disponible
                    }
                }
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# =========================================================
# ADMINISTRACIÓN DE PROFESIONALES
# =========================================================

@extend_schema(
    tags=['Administración de profesionales'],
    summary='Listar profesionales pendientes',
    description='Lista profesionales que están pendientes o en revisión administrativa.',
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='ProfesionalPendiente',
                many=True,
                fields={
                    'id': serializers.IntegerField(),
                    'usuario_id': serializers.IntegerField(),
                    'username': serializers.CharField(),
                    'email': serializers.EmailField(allow_blank=True),
                    'telefono': serializers.CharField(allow_blank=True),
                    'direccion': serializers.CharField(allow_blank=True),
                    'descripcion_profesional': serializers.CharField(allow_blank=True),
                    'experiencia_anos': serializers.IntegerField(),
                    'estado_verificacion': serializers.CharField(),
                    'disponible': serializers.BooleanField(),
                },
            ),
            description='Lista de profesionales pendientes de revisión.',
        ),
        403: OpenApiResponse(description='Se requieren permisos de administrador.'),
    },
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def listar_profesionales_pendientes(request):
    """Lista profesionales que esperan revisión administrativa."""

    perfiles = Perfil.objects.filter(
        rol='profesional',
        estado_verificacion__in=['pendiente', 'en_revision']
    ).select_related('usuario').order_by('id')

    resultados = []

    for perfil in perfiles:
        resultados.append({
            'id': perfil.id,
            'usuario_id': perfil.usuario_id,
            'username': perfil.usuario.username,
            'email': perfil.usuario.email,
            'telefono': perfil.telefono,
            'direccion': perfil.direccion,
            'descripcion_profesional': perfil.descripcion_profesional,
            'experiencia_anos': perfil.experiencia_anos,
            'estado_verificacion': perfil.estado_verificacion,
            'disponible': perfil.disponible,
        })

    return Response(resultados)


@extend_schema(
    tags=['Administración de profesionales'],
    summary='Aprobar o rechazar profesional',
    description='Actualiza el estado de verificación de un profesional.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'estado_verificacion': {
                    'type': 'string',
                    'enum': ['aprobado', 'rechazado'],
                },
            },
            'required': ['estado_verificacion'],
        },
    },
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='CambiarEstadoProfesionalRespuesta',
                fields={
                    'mensaje': serializers.CharField(),
                    'profesional_id': serializers.IntegerField(),
                    'estado_verificacion': serializers.CharField(),
                    'disponible': serializers.BooleanField(),
                },
            ),
            description='Estado del profesional actualizado.',
        ),
        400: OpenApiResponse(
            description='Estado inválido o profesional ya revisado.',
        ),
        403: OpenApiResponse(description='Se requieren permisos de administrador.'),
        404: OpenApiResponse(description='El profesional no existe.'),
    },
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def cambiar_estado_profesional(request, pk):
    """Aprueba o rechaza la verificación de un profesional."""

    nuevo_estado = request.data.get('estado_verificacion')

    if nuevo_estado not in ['aprobado', 'rechazado']:
        return Response(
            {
                'error': (
                    'El estado debe ser aprobado o rechazado.'
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        perfil = Perfil.objects.get(
            pk=pk,
            rol='profesional'
        )
    except Perfil.DoesNotExist:
        return Response(
            {'error': 'El profesional no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if perfil.estado_verificacion not in ['pendiente', 'en_revision']:
        return Response(
            {'error': 'Este profesional ya fue revisado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    perfil.estado_verificacion = nuevo_estado

    if nuevo_estado == 'rechazado':
        perfil.disponible = False

    perfil.save(
        update_fields=['estado_verificacion', 'disponible']
    )

    return Response({
        'mensaje': 'Estado del profesional actualizado.',
        'profesional_id': perfil.id,
        'estado_verificacion': perfil.estado_verificacion,
        'disponible': perfil.disponible,
    })
