
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

from usuarios.models import DesafioLogin
from usuarios.views import validar_codigo_totp_unico


class LoginMFATests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Usuario temporal para las pruebas
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

    # PRUEBA 1: cuatro intentos incorrectos no bloquean
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

    # PRUEBA 2: el quinto intento bloquea el desafío
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

    # PRUEBA 3: el sexto intento no incrementa el contador
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

        # Realizar los cinco intentos permitidos
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

        # Realizar el sexto intento
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
