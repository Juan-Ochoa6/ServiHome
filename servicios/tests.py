
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import Perfil
from servicios.models import (
    Categoria,
    Servicio,
    ServicioProfesional,
    SolicitudServicio,
)


class SolicitudPermisosTests(APITestCase):

    def setUp(self):
        # Usuarios
        self.usuario_cliente = User.objects.create_user(
            username='cliente_test',
            password='ClaveClienteTest123!'
        )
        self.usuario_profesional1 = User.objects.create_user(
            username='profesional1_test',
            password='ClaveProfesional123!'
        )
        self.usuario_profesional2 = User.objects.create_user(
            username='profesional2_test',
            password='ClaveProfesional456!'
        )
        self.usuario_sin_perfil = User.objects.create_user(
            username='sin_perfil_test',
            password='ClaveSinPerfil123!'
        )

        # Perfiles creados automáticamente por las señales
        self.cliente = self.usuario_cliente.perfil
        self.profesional1 = self.usuario_profesional1.perfil
        self.profesional2 = self.usuario_profesional2.perfil

        # Asignar roles
        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.profesional1.rol = 'profesional'
        self.profesional1.estado_verificacion = 'aprobado'
        self.profesional1.disponible = True
        self.profesional1.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'disponible',
            ]
        )

        self.profesional2.rol = 'profesional'
        self.profesional2.estado_verificacion = 'aprobado'
        self.profesional2.disponible = True
        self.profesional2.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'disponible',
            ]
        )

        # Categoría y servicio
        self.categoria = Categoria.objects.create(
            nombre='Plomería test',
            descripcion='Categoría para pruebas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Reparación de tuberías test',
            descripcion='Servicio utilizado en pruebas',
            precio_base=Decimal('50000.00'),
            activo=True
        )

        # Oferta aprobada del profesional 1
        self.oferta = ServicioProfesional.objects.create(
            servicio=self.servicio,
            profesional=self.profesional1,
            precio=Decimal('50000.00'),
            estado_aprobacion='aprobado'
        )

        # Solicitud asignada al profesional 1
        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional1,
            servicio=self.servicio,
            descripcion='Solicitud para pruebas',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='pendiente'
        )

        self.url_solicitudes = '/api/solicitudes/'
        self.url_estado = (
            f'/api/solicitudes/{self.solicitud.pk}/estado/'
        )

    def test_profesional_solo_ve_sus_solicitudes(self):
        self.client.force_authenticate(
            user=self.usuario_profesional2
        )

        respuesta = self.client.get(self.url_solicitudes)

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )

        resultados = respuesta.data
        self.assertEqual(len(resultados), 0)

    def test_cliente_solo_ve_sus_solicitudes(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.get(self.url_solicitudes)

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )

        resultados = respuesta.data
        self.assertEqual(len(resultados), 1)
        self.assertEqual(
            resultados[0]['id'],
            self.solicitud.pk
        )

    def test_profesional_no_puede_aceptar_solicitud_ajena(self):
        self.client.force_authenticate(
            user=self.usuario_profesional2
        )

        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'aceptada'},
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            respuesta.data['detail'],
            'Esta solicitud no te corresponde.'
        )

        self.solicitud.refresh_from_db()
        self.assertEqual(
            self.solicitud.estado,
            'pendiente'
        )

    def test_cliente_no_puede_crear_solicitud_para_otro_cliente(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        datos = {
            'cliente': self.profesional2.pk,
            'profesional': self.profesional1.pk,
            'servicio': self.servicio.pk,
            'descripcion': 'Prueba de creación',
            'direccion_servicio': 'Dirección de prueba',
            'fecha_solicitada': (
                timezone.now() + timedelta(days=3)
            ).isoformat(),
        }

        respuesta = self.client.post(
            self.url_solicitudes,
            datos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_201_CREATED
        )

        nueva = SolicitudServicio.objects.latest('id')

        # El cliente se asigna desde la sesión autenticada
        self.assertEqual(
            nueva.cliente_id,
            self.cliente.pk
        )
        self.assertEqual(nueva.estado, 'pendiente')
        self.assertIsNone(nueva.precio_acordado)

    def test_profesional_no_puede_crear_solicitudes(self):
        self.client.force_authenticate(
            user=self.usuario_profesional1
        )

        datos = {
            'profesional': self.profesional1.pk,
            'servicio': self.servicio.pk,
            'descripcion': 'Intento no permitido',
            'direccion_servicio': 'Dirección de prueba',
            'fecha_solicitada': (
                timezone.now() + timedelta(days=3)
            ).isoformat(),
        }

        respuesta = self.client.post(
            self.url_solicitudes,
            datos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_usuario_sin_perfil_no_puede_crear_solicitudes(self):
        # Eliminar el perfil creado automáticamente por la señal
        self.usuario_sin_perfil.perfil.delete()

        self.client.force_authenticate(
            user=self.usuario_sin_perfil
        )

        datos = {
            'profesional': self.profesional1.pk,
            'servicio': self.servicio.pk,
            'descripcion': 'Solicitud sin perfil',
            'direccion_servicio': 'Dirección de prueba',
            'fecha_solicitada': (
                timezone.now() + timedelta(days=3)
            ).isoformat(),
        }

        respuesta = self.client.post(
            self.url_solicitudes,
            datos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_no_se_puede_reabrir_solicitud_completada(self):
        self.solicitud.estado = 'completada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(
            user=self.usuario_profesional1
        )

        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'aceptada'},
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.solicitud.refresh_from_db()
        self.assertEqual(
            self.solicitud.estado,
            'completada'
        )

class AdministracionOfertasTests(APITestCase):

    def setUp(self):
        # Administrador
        self.usuario_admin = User.objects.create_user(
            username='admin_ofertas_test',
            password='ClaveAdmin123!',
            is_staff=True
        )

        # Usuario normal
        self.usuario_normal = User.objects.create_user(
            username='usuario_ofertas_test',
            password='ClaveNormal123!'
        )

        # Profesional aprobado
        self.usuario_profesional = User.objects.create_user(
            username='profesional_ofertas_test',
            password='ClaveProfesional123!'
        )

        self.profesional = self.usuario_profesional.perfil
        self.profesional.rol = 'profesional'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        # Categoría y servicio
        self.categoria = Categoria.objects.create(
            nombre='Electricidad administrativa test',
            descripcion='Categoría para pruebas administrativas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Instalación eléctrica test',
            descripcion='Servicio para pruebas administrativas',
            precio_base=Decimal('80000.00'),
            activo=True
        )

        # Oferta pendiente
        self.oferta = ServicioProfesional.objects.create(
            servicio=self.servicio,
            profesional=self.profesional,
            precio=Decimal('75000.00'),
            estado_aprobacion='pendiente'
        )

        self.url_lista = '/api/admin/ofertas/'
        self.url_estado = (
            f'/api/admin/ofertas/{self.oferta.pk}/'
        )

    def test_usuario_normal_no_puede_listar_ofertas_pendientes(self):
        self.client.force_authenticate(user=self.usuario_normal)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 403)

    def test_usuario_normal_no_puede_aprobar_ofertas(self):
        self.client.force_authenticate(user=self.usuario_normal)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'aprobado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

        self.oferta.refresh_from_db()

        self.assertEqual(
            self.oferta.estado_aprobacion,
            'pendiente'
        )

    def test_administrador_puede_listar_ofertas_pendientes(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 200)

        ids = [item['id'] for item in respuesta.data]

        self.assertIn(self.oferta.pk, ids)

    def test_administrador_puede_aprobar_oferta(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'aprobado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.oferta.refresh_from_db()

        self.assertEqual(
            self.oferta.estado_aprobacion,
            'aprobado'
        )

    def test_administrador_puede_rechazar_oferta(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'rechazado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.oferta.refresh_from_db()

        self.assertEqual(
            self.oferta.estado_aprobacion,
            'rechazado'
        )

    def test_no_se_puede_aprobar_oferta_de_profesional_no_aprobado(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(
            update_fields=['estado_verificacion']
        )

        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'aprobado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        self.oferta.refresh_from_db()

        self.assertEqual(
            self.oferta.estado_aprobacion,
            'pendiente'
        )

    def test_no_se_puede_revisar_una_oferta_ya_procesada(self):
        self.oferta.estado_aprobacion = 'aprobado'
        self.oferta.save(
            update_fields=['estado_aprobacion']
        )

        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'rechazado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_se_acepta_estado_de_oferta_invalido(self):
        self.client.force_authenticate(user=self.usuario_admin)

        respuesta = self.client.patch(
            self.url_estado,
            {'estado_aprobacion': 'pendiente'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)