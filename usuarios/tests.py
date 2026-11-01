
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from unittest.mock import patch

import pyotp

from django.contrib.auth.models import User
from django.core.signing import SignatureExpired
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from rest_framework.test import APIClient

from usuarios.models import (
    DesafioLogin,
    CodigoRecuperacionMFA
)

from usuarios.views import (
    validar_codigo_totp_unico,
    generar_codigos_recuperacion
)


class LoginMFATests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.usuario = User.objects.create_user(
            username='usuario_prueba',
            email='prueba@servihome.test',
            password='PruebaBackend2026!'
        )

        self.url_login = '/api/usuarios/login/'
        self.url_mfa = '/api/usuarios/login/mfa/'

    def iniciar_sesion(
        self,
        username='usuario_prueba',
        password='PruebaBackend2026!'
    ):
        return self.client.post(
            self.url_login,
            {
                'username': username,
                'password': password
            },
            format='json'
        )

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def activar_mfa(self):
        """Prepara un usuario con MFA activado."""

        perfil = self.usuario.perfil
        secret = pyotp.random_base32()

        perfil.set_totp_secret(secret)
        perfil.two_factor_enabled = True
        perfil.save()

        return perfil

    def crear_codigo_recuperacion(self):
        """Crea un código de recuperación para las pruebas."""

        codigo = 'ABCDEF0123456789ABCDEF0123456789'

        codigo_hash = hashlib.sha256(
            codigo.encode('utf-8')
        ).hexdigest()

        CodigoRecuperacionMFA.objects.create(
            usuario=self.usuario,
            codigo_hash=codigo_hash
        )

        return codigo

    def obtener_challenge(self):
        respuesta = self.iniciar_sesion()

        self.assertEqual(respuesta.status_code, 200)

        return respuesta.data['challenge']

    # ==========================================
    # PRUEBAS DE CÓDIGOS DE RECUPERACIÓN
    # ==========================================

    def test_generar_ocho_codigos_recuperacion(self):
        codigos = generar_codigos_recuperacion(self.usuario)

        self.assertEqual(len(codigos), 8)
        self.assertEqual(len(set(codigos)), 8)

        self.assertEqual(
            CodigoRecuperacionMFA.objects.filter(
                usuario=self.usuario
            ).count(),
            8
        )

    def test_codigos_recuperacion_son_almacenados_como_hash(self):
        codigos = generar_codigos_recuperacion(self.usuario)

        registros = CodigoRecuperacionMFA.objects.filter(
            usuario=self.usuario
        )

        hashes = list(
            registros.values_list('codigo_hash', flat=True)
        )

        for codigo in codigos:
            codigo_hash = hashlib.sha256(
                codigo.encode('utf-8')
            ).hexdigest()

            self.assertIn(codigo_hash, hashes)
            self.assertNotIn(codigo, hashes)

    def test_codigos_recuperacion_tienen_formato_correcto(self):
        codigos = generar_codigos_recuperacion(self.usuario)

        for codigo in codigos:
            self.assertEqual(len(codigo), 32)

            self.assertTrue(
                all(
                    caracter in '0123456789ABCDEF'
                    for caracter in codigo
                )
            )

    def test_generar_nuevos_codigos_invalida_los_anteriores(self):
        codigos_anteriores = generar_codigos_recuperacion(
            self.usuario
        )

        codigos_nuevos = generar_codigos_recuperacion(
            self.usuario
        )

        self.assertEqual(len(codigos_nuevos), 8)

        for codigo in codigos_anteriores:
            codigo_hash = hashlib.sha256(
                codigo.encode('utf-8')
            ).hexdigest()

            self.assertFalse(
                CodigoRecuperacionMFA.objects.filter(
                    usuario=self.usuario,
                    codigo_hash=codigo_hash
                ).exists()
            )

        for codigo in codigos_nuevos:
            codigo_hash = hashlib.sha256(
                codigo.encode('utf-8')
            ).hexdigest()

            self.assertTrue(
                CodigoRecuperacionMFA.objects.filter(
                    usuario=self.usuario,
                    codigo_hash=codigo_hash
                ).exists()
            )

    def test_generar_codigos_elimina_codigos_utilizados_y_no_utilizados(self):
        codigo = self.crear_codigo_recuperacion()

        codigo_hash = hashlib.sha256(
            codigo.encode('utf-8')
        ).hexdigest()

        CodigoRecuperacionMFA.objects.filter(
            usuario=self.usuario,
            codigo_hash=codigo_hash
        ).update(utilizado=True)

        # Se crea un segundo código que permanece sin utilizar.
        segundo_codigo = '1234567890ABCDEF1234567890ABCDEF'

        segundo_hash = hashlib.sha256(
            segundo_codigo.encode('utf-8')
        ).hexdigest()

        CodigoRecuperacionMFA.objects.create(
            usuario=self.usuario,
            codigo_hash=segundo_hash
        )

        nuevos = generar_codigos_recuperacion(self.usuario)

        self.assertEqual(len(nuevos), 8)

        registros = CodigoRecuperacionMFA.objects.filter(
            usuario=self.usuario
        )

        self.assertEqual(registros.count(), 8)

        self.assertFalse(
            registros.filter(utilizado=True).exists()
        )

        self.assertFalse(
            registros.filter(
                codigo_hash__in=[codigo_hash, segundo_hash]
            ).exists()
        )

    # ==========================================
    # INICIO DE SESIÓN CON CÓDIGO DE RECUPERACIÓN
    # ==========================================

    def test_login_correcto_con_codigo_recuperacion(self):
        self.activar_mfa()

        codigo = self.crear_codigo_recuperacion()
        challenge = self.obtener_challenge()

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': codigo
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)

        registro = CodigoRecuperacionMFA.objects.get(
            usuario=self.usuario
        )

        self.assertTrue(registro.utilizado)
        self.assertIsNotNone(registro.fecha_uso)

    def test_codigo_recuperacion_no_se_puede_reutilizar(self):
        self.activar_mfa()

        codigo = self.crear_codigo_recuperacion()

        primer_challenge = self.obtener_challenge()

        primera_respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': primer_challenge,
                'codigo': codigo
            },
            format='json'
        )

        self.assertEqual(primera_respuesta.status_code, 200)

        segundo_challenge = self.obtener_challenge()

        segunda_respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': segundo_challenge,
                'codigo': codigo
            },
            format='json'
        )

        self.assertEqual(segunda_respuesta.status_code, 400)

        registro = CodigoRecuperacionMFA.objects.get(
            usuario=self.usuario
        )

        self.assertTrue(registro.utilizado)

    def test_codigo_recuperacion_no_utilizado_no_se_consume_si_es_incorrecto(self):
        self.activar_mfa()

        self.crear_codigo_recuperacion()
        challenge = self.obtener_challenge()

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        registro = CodigoRecuperacionMFA.objects.get(
            usuario=self.usuario
        )

        self.assertFalse(registro.utilizado)
        self.assertIsNone(registro.fecha_uso)

    def test_codigo_recuperacion_incorrecto_incrementa_intentos(self):
        self.activar_mfa()

        challenge = self.obtener_challenge()

        for intento in range(1, 5):
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
                },
                format='json'
            )

            self.assertEqual(respuesta.status_code, 400)
            self.assertEqual(
                respuesta.data['intentos_restantes'],
                5 - intento
            )

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertEqual(desafio.intentos_fallidos, 4)
        self.assertFalse(desafio.bloqueado)

    def test_quinto_codigo_recuperacion_incorrecto_bloquea_desafio(self):
        self.activar_mfa()

        challenge = self.obtener_challenge()

        for _ in range(5):
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
                },
                format='json'
            )

        self.assertEqual(respuesta.status_code, 401)

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertEqual(desafio.intentos_fallidos, 5)
        self.assertTrue(desafio.bloqueado)

    def test_codigo_recuperacion_no_funciona_sin_mfa_activo(self):
        codigo = self.crear_codigo_recuperacion()
        challenge = self.obtener_challenge()

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': codigo
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        registro = CodigoRecuperacionMFA.objects.get(
            usuario=self.usuario
        )

        self.assertFalse(registro.utilizado)

    def test_codigo_recuperacion_mal_formado_es_rechazado(self):
        self.activar_mfa()

        challenge = self.obtener_challenge()

        codigos_invalidos = [
            '12345',
            '1234567',
            'ABCDEF',
            'G' * 32,
            'A' * 31,
            'A' * 33,
            'A' * 32 + '!'
        ]

        for codigo in codigos_invalidos:
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': codigo
                },
                format='json'
            )

            self.assertEqual(respuesta.status_code, 400)

    def test_login_totp_no_genera_codigos_nuevos_si_mfa_ya_esta_activo(self):
        self.activar_mfa()

        generar_codigos_recuperacion(self.usuario)

        cantidad_anterior = CodigoRecuperacionMFA.objects.filter(
            usuario=self.usuario
        ).count()

        challenge = self.obtener_challenge()

        with patch(
            'usuarios.views.validar_codigo_totp_unico',
            return_value=True
        ):
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': '123456'
                },
                format='json'
            )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            'codigos_recuperacion',
            respuesta.data
        )

        self.assertEqual(
            CodigoRecuperacionMFA.objects.filter(
                usuario=self.usuario
            ).count(),
            cantidad_anterior
        )

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=True
    )
    def test_primera_activacion_mfa_entrega_ocho_codigos(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': '123456'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            'codigos_recuperacion',
            respuesta.data
        )

        codigos = respuesta.data['codigos_recuperacion']

        self.assertEqual(len(codigos), 8)
        self.assertEqual(len(set(codigos)), 8)

        self.assertEqual(
            CodigoRecuperacionMFA.objects.filter(
                usuario=self.usuario
            ).count(),
            8
        )

        perfil = self.usuario.perfil
        perfil.refresh_from_db()

        self.assertTrue(perfil.two_factor_enabled)

    # ==========================================
    # PRUEBAS GENERALES DE INICIO DE SESIÓN
    # ==========================================

    def test_login_campos_vacios(self):
        respuesta = self.client.post(
            self.url_login,
            {},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_login_usuario_inexistente(self):
        respuesta = self.iniciar_sesion(
            username='usuario_inexistente'
        )

        self.assertEqual(respuesta.status_code, 401)

    def test_login_contrasena_incorrecta(self):
        respuesta = self.iniciar_sesion(
            password='ContrasenaIncorrecta'
        )

        self.assertEqual(respuesta.status_code, 401)

    def test_login_solicita_configuracion_mfa(self):
        respuesta = self.iniciar_sesion()

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.data['mfa_setup_required'])
        self.assertIn('challenge', respuesta.data)
        self.assertIn('codigo_qr', respuesta.data)

    def test_login_usuario_con_mfa_activo(self):
        perfil = self.usuario.perfil

        secret = pyotp.random_base32()
        perfil.set_totp_secret(secret)
        perfil.two_factor_enabled = True
        perfil.save()

        respuesta = self.iniciar_sesion()

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.data['mfa_required'])
        self.assertIn('challenge', respuesta.data)

    def test_verificacion_codigo_incorrecto(self):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': '000000'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=False
    )
    def test_cuatro_codigos_incorrectos_no_bloquean(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        for _ in range(4):
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': '000000'
                },
                format='json'
            )

            self.assertEqual(respuesta.status_code, 400)

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertEqual(desafio.intentos_fallidos, 4)
        self.assertFalse(desafio.bloqueado)
        self.assertFalse(desafio.consumido)

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=False
    )
    def test_quinto_codigo_incorrecto_bloquea_desafio(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        for _ in range(5):
            respuesta = self.client.post(
                self.url_mfa,
                {
                    'challenge': challenge,
                    'codigo': '000000'
                },
                format='json'
            )

        self.assertEqual(respuesta.status_code, 401)

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertEqual(desafio.intentos_fallidos, 5)
        self.assertTrue(desafio.bloqueado)

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=False
    )
    def test_sexto_intento_no_incrementa_contador(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        datos = {
            'challenge': challenge,
            'codigo': '000000'
        }

        for _ in range(5):
            self.client.post(
                self.url_mfa,
                datos,
                format='json'
            )

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertEqual(desafio.intentos_fallidos, 5)
        self.assertTrue(desafio.bloqueado)

        sexta_respuesta = self.client.post(
            self.url_mfa,
            datos,
            format='json'
        )

        self.assertEqual(sexta_respuesta.status_code, 401)

        desafio.refresh_from_db()

        self.assertEqual(desafio.intentos_fallidos, 5)
        self.assertTrue(desafio.bloqueado)

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=True
    )
    def test_verificacion_correcta_entrega_jwt(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': '123456'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.data)
        self.assertIn('refresh', respuesta.data)

        self.assertEqual(
            respuesta.data['usuario'],
            'usuario_prueba'
        )

        self.usuario.perfil.refresh_from_db()
        self.assertTrue(self.usuario.perfil.two_factor_enabled)

    def test_verificacion_sin_challenge(self):
        respuesta = self.client.post(
            self.url_mfa,
            {'codigo': '123456'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_codigo_totp_no_se_puede_reutilizar(self):
        perfil = self.usuario.perfil

        secret = pyotp.random_base32()
        perfil.set_totp_secret(secret)
        perfil.save()

        totp = pyotp.TOTP(secret)

        instante = datetime(
            2026, 1, 1, 12, 0, 0,
            tzinfo=timezone.utc
        )

        codigo = totp.at(instante.timestamp())

        with patch(
            'usuarios.views.timezone.now',
            return_value=instante
        ):
            primera_validacion = validar_codigo_totp_unico(
                perfil,
                codigo
            )

            segunda_validacion = validar_codigo_totp_unico(
                perfil,
                codigo
            )

        self.assertTrue(primera_validacion)
        self.assertFalse(segunda_validacion)

    @patch(
        'usuarios.views.signing.loads',
        side_effect=SignatureExpired
    )
    def test_verificacion_desafio_vencido(self, mock_loads):
        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': 'desafio_de_prueba',
                'codigo': '123456'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertIn(
            'caducado',
            respuesta.data['error'].lower()
        )

    @patch(
        'usuarios.views.validar_codigo_totp_unico',
        return_value=True
    )
    def test_challenge_no_se_puede_reutilizar(self, mock_validar):
        respuesta_login = self.iniciar_sesion()
        challenge = respuesta_login.data['challenge']

        datos = {
            'challenge': challenge,
            'codigo': '123456'
        }

        primera_respuesta = self.client.post(
            self.url_mfa,
            datos,
            format='json'
        )

        self.assertEqual(primera_respuesta.status_code, 200)

        segunda_respuesta = self.client.post(
            self.url_mfa,
            datos,
            format='json'
        )

        self.assertEqual(segunda_respuesta.status_code, 401)

        self.assertIn(
            'utilizado',
            segunda_respuesta.data['error'].lower()
        )

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertTrue(desafio.consumido)

    def test_challenge_no_registrado_es_rechazado(self):
        from django.core import signing

        challenge = signing.dumps(
            {'user_id': self.usuario.pk},
            salt='servihome.mfa.login'
        )

        respuesta = self.client.post(
            self.url_mfa,
            {
                'challenge': challenge,
                'codigo': '123456'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 401)


class LoginMFAConcurrenciaTests(TransactionTestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='usuario_concurrencia',
            email='concurrencia@servihome.test',
            password='PruebaBackend2026!'
        )

        self.url_login = '/api/usuarios/login/'
        self.url_mfa = '/api/usuarios/login/mfa/'

    def test_dos_solicitudes_simultaneas_solo_permiten_un_login(self):
        cliente_login = APIClient()

        respuesta_login = cliente_login.post(
            self.url_login,
            {
                'username': 'usuario_concurrencia',
                'password': 'PruebaBackend2026!'
            },
            format='json'
        )

        self.assertEqual(respuesta_login.status_code, 200)

        challenge = respuesta_login.data['challenge']

        perfil = self.usuario.perfil
        perfil.refresh_from_db()

        secret = perfil.get_totp_secret()

        instante = datetime.now(timezone.utc)

        totp = pyotp.TOTP(secret)
        codigo = totp.at(instante.timestamp())

        self.assertTrue(
            totp.verify(
                codigo,
                for_time=instante.timestamp()
            )
        )

        barrera = threading.Barrier(2)

        def realizar_solicitud():
            close_old_connections()

            try:
                cliente = APIClient()

                datos = {
                    'challenge': challenge,
                    'codigo': codigo
                }

                barrera.wait(timeout=15)

                return cliente.post(
                    self.url_mfa,
                    datos,
                    format='json'
                )

            finally:
                close_old_connections()

        with patch(
            'usuarios.views.timezone.now',
            return_value=instante
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futuro_1 = executor.submit(realizar_solicitud)
                futuro_2 = executor.submit(realizar_solicitud)

                respuesta_1 = futuro_1.result(timeout=30)
                respuesta_2 = futuro_2.result(timeout=30)

        codigos_respuesta = [
            respuesta_1.status_code,
            respuesta_2.status_code
        ]

        self.assertEqual(codigos_respuesta.count(200), 1)
        self.assertEqual(codigos_respuesta.count(401), 1)

        respuestas_exitosas = [
            respuesta
            for respuesta in [respuesta_1, respuesta_2]
            if respuesta.status_code == 200
        ]

        self.assertIn('access', respuestas_exitosas[0].data)
        self.assertIn('refresh', respuestas_exitosas[0].data)

        desafio = DesafioLogin.objects.get(
            usuario=self.usuario
        )

        self.assertTrue(desafio.consumido)

        perfil.refresh_from_db()

        self.assertIsNotNone(perfil.last_otp_at)
class AdministracionProfesionalesTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Administrador
        self.usuario_admin = User.objects.create_user(
            username='admin_test',
            email='admin@servihome.test',
            password='ClaveAdmin123!',
            is_staff=True
        )

        # Usuario normal
        self.usuario_normal = User.objects.create_user(
            username='usuario_normal_test',
            password='ClaveNormal123!'
        )

        # Profesional pendiente
        self.usuario_profesional = User.objects.create_user(
            username='profesional_pendiente_test',
            email='profesional@servihome.test',
            password='ClaveProfesional123!'
        )

        self.perfil_profesional = self.usuario_profesional.perfil
        self.perfil_profesional.rol = 'profesional'
        self.perfil_profesional.estado_verificacion = 'pendiente'
        self.perfil_profesional.disponible = False
        self.perfil_profesional.save()

        self.url_lista = '/api/usuarios/admin/profesionales/'
        self.url_estado = (
            f'/api/usuarios/admin/profesionales/'
            f'{self.perfil_profesional.pk}/'
        )

    def test_usuario_normal_no_puede_listar_profesionales_pendientes(self):
        self.client.force_authenticate(user=self.usuario_normal)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 403)

    def test_usuario_normal_no_puede_aprobar_profesional(self):
        self.client.force_authenticate(user=self.usuario_normal)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_verificacion': 'aprobado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

        self.perfil_profesional.refresh_from_db()
        self.assertEqual(
            self.perfil_profesional.estado_verificacion,
            'pendiente'
        )

    def test_administrador_puede_listar_profesionales_pendientes(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 200)

        ids = [item['id'] for item in respuesta.data]

        self.assertIn(self.perfil_profesional.pk, ids)

    def test_administrador_puede_aprobar_profesional(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_verificacion': 'aprobado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.perfil_profesional.refresh_from_db()

        self.assertEqual(
            self.perfil_profesional.estado_verificacion,
            'aprobado'
        )

        # La aprobación no activa automáticamente la disponibilidad.
        self.assertFalse(self.perfil_profesional.disponible)

    def test_administrador_puede_rechazar_profesional(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_verificacion': 'rechazado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.perfil_profesional.refresh_from_db()

        self.assertEqual(
            self.perfil_profesional.estado_verificacion,
            'rechazado'
        )

        self.assertFalse(self.perfil_profesional.disponible)

    def test_no_se_puede_aprobar_un_profesional_ya_revisado(self):
        self.perfil_profesional.estado_verificacion = 'aprobado'
        self.perfil_profesional.save(
            update_fields=['estado_verificacion']
        )

        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_verificacion': 'rechazado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_se_acepta_un_estado_de_verificacion_invalido(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_verificacion': 'en_revision'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)