
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
    PropuestaPrecio,
    Resena,
    Pago,
    Incidente,
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
        self.profesional1.estado_identidad = 'aprobado'
        self.profesional1.disponible = True
        self.profesional1.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
                'disponible',
            ]
        )

        self.profesional2.rol = 'profesional'
        self.profesional2.estado_verificacion = 'aprobado'
        self.profesional2.estado_identidad = 'aprobado'
        self.profesional2.disponible = True
        self.profesional2.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
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
    def test_cliente_puede_consultar_detalle_solicitud(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.get(
            f'/api/solicitudes/{self.solicitud.pk}/'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            respuesta.data['id'],
            self.solicitud.pk
        )

    def test_profesional_asignado_puede_consultar_detalle(self):
        self.client.force_authenticate(
            user=self.usuario_profesional1
        )

        respuesta = self.client.get(
            f'/api/solicitudes/{self.solicitud.pk}/'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            respuesta.data['id'],
            self.solicitud.pk
        )

    def test_profesional_ajeno_no_puede_consultar_detalle(self):
        self.client.force_authenticate(
            user=self.usuario_profesional2
        )

        respuesta = self.client.get(
            f'/api/solicitudes/{self.solicitud.pk}/'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_cliente_ajeno_no_puede_consultar_detalle(self):
        otro_usuario = User.objects.create_user(
            username='otro_cliente_test',
            password='ClaveOtroCliente123!'
        )
        otro_usuario.perfil.rol = 'cliente'
        otro_usuario.perfil.save(update_fields=['rol'])

        self.client.force_authenticate(user=otro_usuario)

        respuesta = self.client.get(
            f'/api/solicitudes/{self.solicitud.pk}/'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_404_NOT_FOUND
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
    def test_cliente_no_puede_crear_solicitud_con_fecha_pasada(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        cantidad_antes = SolicitudServicio.objects.count()

        datos = {
            'profesional': self.profesional1.pk,
            'servicio': self.servicio.pk,
            'descripcion': 'Solicitud con fecha pasada',
            'direccion_servicio': 'Dirección de prueba',
            'fecha_solicitada': (
                timezone.now() - timedelta(days=1)
            ).isoformat(),
        }

        respuesta = self.client.post(
            self.url_solicitudes,
            datos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            SolicitudServicio.objects.count(),
            cantidad_antes
        )

    def test_cliente_puede_crear_solicitud_con_fecha_futura(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        cantidad_antes = SolicitudServicio.objects.count()

        datos = {
            'profesional': self.profesional1.pk,
            'servicio': self.servicio.pk,
            'descripcion': 'Solicitud con fecha futura',
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

        self.assertEqual(
            SolicitudServicio.objects.count(),
            cantidad_antes + 1
        )


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
        self.profesional.estado_identidad = 'aprobado'
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
class CodigosServicioTests(APITestCase):

    def setUp(self):
        self.usuario_cliente = User.objects.create_user(
            username='cliente_codigos_test',
            password='ClaveCliente123!'
        )

        self.usuario_profesional = User.objects.create_user(
            username='profesional_codigos_test',
            password='ClaveProfesional123!'
        )

        self.cliente = self.usuario_cliente.perfil
        self.profesional = self.usuario_profesional.perfil

        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.profesional.rol = 'profesional'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría códigos test',
            descripcion='Pruebas de códigos',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio códigos test',
            descripcion='Servicio para probar códigos',
            precio_base=Decimal('50000.00'),
            activo=True
        )

        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud códigos',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='pendiente'
        )

        self.propuesta = PropuestaPrecio.objects.create(
            solicitud=self.solicitud,
            proponente=self.profesional,
            precio=Decimal('50000.00')
        )

        self.url_respuesta = (
            f'/api/solicitudes/{self.solicitud.pk}/'
            f'propuestas/{self.propuesta.pk}/'
        )

        self.url_estado = (
            f'/api/solicitudes/{self.solicitud.pk}/estado/'
        )

    def test_aceptar_propuesta_genera_codigo_inicio(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.patch(
            self.url_respuesta,
            {'accion': 'aceptar'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.solicitud.refresh_from_db()

        self.assertEqual(self.solicitud.estado, 'aceptada')
        self.assertEqual(len(self.solicitud.codigo_inicio), 6)
        self.assertTrue(self.solicitud.codigo_inicio.isdigit())

    def test_codigo_inicio_incorrecto_no_inicia_servicio(self):
        self.solicitud.estado = 'aceptada'
        self.solicitud.codigo_inicio = '123456'
        self.solicitud.save()

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.patch(
            self.url_estado,
            {
                'estado': 'en_proceso',
                'codigo': '000000'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'aceptada')

    def test_codigo_inicio_correcto_inicia_y_genera_codigo_finalizacion(self):
        self.solicitud.estado = 'aceptada'
        self.solicitud.codigo_inicio = '123456'
        self.solicitud.save()

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.patch(
            self.url_estado,
            {
                'estado': 'en_proceso',
                'codigo': '123456'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.solicitud.refresh_from_db()

        self.assertEqual(self.solicitud.estado, 'en_proceso')
        self.assertEqual(len(self.solicitud.codigo_finalizacion), 6)
        self.assertTrue(
            self.solicitud.codigo_finalizacion.isdigit()
        )

    def test_codigo_finalizacion_incorrecto_no_completa_servicio(self):
        self.solicitud.estado = 'en_proceso'
        self.solicitud.codigo_finalizacion = '654321'
        self.solicitud.save()

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.patch(
            self.url_estado,
            {
                'estado': 'completada',
                'codigo': '000000'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'en_proceso')

    def test_codigo_finalizacion_correcto_completa_servicio(self):
        self.solicitud.estado = 'en_proceso'
        self.solicitud.codigo_finalizacion = '654321'
        self.solicitud.save()

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.patch(
            self.url_estado,
            {
                'estado': 'completada',
                'codigo': '654321'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'completada')
class ResenasTests(APITestCase):

    def setUp(self):
        self.usuario_cliente = User.objects.create_user(
            username='cliente_resenas',
            password='ClaveCliente123!'
        )

        self.usuario_profesional = User.objects.create_user(
            username='profesional_resenas',
            password='ClaveProfesional123!'
        )

        self.usuario_otro_cliente = User.objects.create_user(
            username='otro_cliente_resenas',
            password='ClaveOtro123!'
        )

        self.cliente = self.usuario_cliente.perfil
        self.profesional = self.usuario_profesional.perfil
        self.otro_cliente = self.usuario_otro_cliente.perfil

        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.otro_cliente.rol = 'cliente'
        self.otro_cliente.save(update_fields=['rol'])

        self.profesional.rol = 'profesional'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría reseñas test',
            descripcion='Pruebas de reseñas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio reseñas test',
            descripcion='Servicio para probar reseñas',
            precio_base=Decimal('50000.00'),
            activo=True
        )

        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud para reseña',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='completada'
        )

        self.url_crear = (
            f'/api/solicitudes/{self.solicitud.pk}/resena/'
        )

        self.url_reputacion = (
            f'/api/profesionales/{self.profesional.pk}/reputacion/'
        )

        self.url_resenas = (
            f'/api/profesionales/{self.profesional.pk}/resenas/'
        )

    def test_cliente_puede_crear_resena(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 5,
                'comentario': 'Excelente servicio.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(
            Resena.objects.filter(
                solicitud=self.solicitud
            ).exists()
        )

    def test_no_permite_resenar_solicitud_no_completada(self):
        self.solicitud.estado = 'en_proceso'
        self.solicitud.save()

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 5,
                'comentario': 'Buen servicio.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(
            Resena.objects.filter(
                solicitud=self.solicitud
            ).exists()
        )

    def test_no_permite_resenar_solicitud_ajena(self):
        self.client.force_authenticate(
            user=self.usuario_otro_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 4,
                'comentario': 'Buen servicio.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_profesional_no_puede_crear_resena(self):
        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 5,
                'comentario': 'Excelente.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_no_permite_resenas_duplicadas(self):
        Resena.objects.create(
            solicitud=self.solicitud,
            calificacion=5,
            comentario='Primera reseña.'
        )

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 4,
                'comentario': 'Segunda reseña.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_permite_calificacion_fuera_de_rango(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'calificacion': 6,
                'comentario': 'Calificación inválida.'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_consultar_reputacion_profesional(self):
        Resena.objects.create(
            solicitud=self.solicitud,
            calificacion=5,
            comentario='Excelente.'
        )

        respuesta = self.client.get(self.url_reputacion)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.data['promedio_calificacion'],
            5.0
        )
        self.assertEqual(
            respuesta.data['total_resenas'],
            1
        )

    def test_consultar_resenas_profesional(self):
        Resena.objects.create(
            solicitud=self.solicitud,
            calificacion=4,
            comentario='Buen trabajo.'
        )

        respuesta = self.client.get(self.url_resenas)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 1)
class PagosTests(APITestCase):

    def setUp(self):

        self.usuario_cliente = User.objects.create_user(
            username='cliente_pagos',
            password='ClaveCliente123!'
        )

        self.usuario_profesional = User.objects.create_user(
            username='profesional_pagos',
            password='ClaveProfesional123!'
        )

        self.usuario_otro_cliente = User.objects.create_user(
            username='otro_cliente_pagos',
            password='ClaveOtro123!'
        )

        self.usuario_admin = User.objects.create_user(
            username='admin_pagos',
            password='ClaveAdmin123!',
            is_staff=True
        )

        self.cliente = self.usuario_cliente.perfil
        self.profesional = self.usuario_profesional.perfil
        self.otro_cliente = self.usuario_otro_cliente.perfil

        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.otro_cliente.rol = 'cliente'
        self.otro_cliente.save(update_fields=['rol'])

        self.profesional.rol = 'profesional'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría pagos test',
            descripcion='Pruebas de pagos'
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio pagos test',
            descripcion='Servicio para probar pagos',
            precio_base=Decimal('50000.00')
        )

        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud para pago',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='completada',
            precio_acordado=Decimal('100000.00')
        )

        self.url_crear = (
            f'/api/solicitudes/{self.solicitud.pk}/pago/'
        )

        self.url_mis_pagos = '/api/mis-pagos/'

    def test_cliente_puede_registrar_pago(self):

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {'metodo': 'transferencia'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 201)

        pago = Pago.objects.get(
            solicitud=self.solicitud
        )

        self.assertEqual(
            pago.monto_total,
            Decimal('100000.00')
        )

        self.assertEqual(
            pago.monto_comision,
            Decimal('10000.00')
        )

        self.assertEqual(
            pago.monto_profesional,
            Decimal('90000.00')
        )

        self.assertEqual(pago.estado, 'pendiente')

    def test_no_permite_pagos_duplicados(self):

        Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('100000.00'),
            metodo='efectivo'
        )

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {'metodo': 'efectivo'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_permite_pagar_solicitud_ajena(self):

        self.client.force_authenticate(
            user=self.usuario_otro_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {'metodo': 'efectivo'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_no_permite_pagar_solicitud_no_completada(self):

        self.solicitud.estado = 'en_proceso'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {'metodo': 'transferencia'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_profesional_no_puede_registrar_pago(self):

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url_crear,
            {'metodo': 'efectivo'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_cliente_no_puede_modificar_monto_ni_estado(self):

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url_crear,
            {
                'metodo': 'transferencia',
                'monto_total': '1.00',
                'estado': 'pagado',
                'porcentaje_comision': '0'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 201)

        pago = Pago.objects.get(
            solicitud=self.solicitud
        )

        self.assertEqual(
            pago.monto_total,
            Decimal('100000.00')
        )

        self.assertEqual(pago.estado, 'pendiente')

        self.assertEqual(
            pago.porcentaje_comision,
            Decimal('10.00')
        )

    def test_usuario_normal_no_puede_confirmar_pago(self):

        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('100000.00'),
            metodo='transferencia'
        )

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.patch(
            f'/api/pagos/{pago.pk}/estado/',
            {'estado': 'pagado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_puede_confirmar_pago(self):

        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('100000.00'),
            metodo='transferencia'
        )

        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.patch(
            f'/api/pagos/{pago.pk}/estado/',
            {'estado': 'pagado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)

        pago.refresh_from_db()

        self.assertEqual(pago.estado, 'pagado')
        self.assertIsNotNone(pago.fecha_pago)

    def test_cliente_y_profesional_consultan_sus_pagos(self):

        Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('100000.00'),
            metodo='efectivo'
        )

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta_cliente = self.client.get(
            self.url_mis_pagos
        )

        self.assertEqual(respuesta_cliente.status_code, 200)
        self.assertEqual(len(respuesta_cliente.data), 1)

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta_profesional = self.client.get(
            self.url_mis_pagos
        )

        self.assertEqual(
            respuesta_profesional.status_code,
            200
        )

        self.assertEqual(
            len(respuesta_profesional.data),
            1
        )
class FinanzasTests(APITestCase):

    def setUp(self):
        self.usuario_admin = User.objects.create_user(
            username='admin_finanzas',
            password='ClaveAdmin123!',
            is_staff=True
        )

        self.usuario_normal = User.objects.create_user(
            username='usuario_finanzas',
            password='ClaveUsuario123!'
        )

        self.cliente = self.usuario_normal.perfil
        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.profesional_usuario = User.objects.create_user(
            username='profesional_finanzas',
            password='ClaveProfesional123!'
        )

        self.profesional = self.profesional_usuario.perfil
        self.profesional.rol = 'profesional'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría finanzas test',
            descripcion='Pruebas de finanzas'
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio finanzas test',
            descripcion='Servicio para probar finanzas',
            precio_base=Decimal('50000.00')
        )

        self.url = '/api/admin/finanzas/'

    def crear_pago(self, monto, fecha, estado='pagado'):
        solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud para pruebas financieras',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='completada',
            precio_acordado=monto
        )

        return Pago.objects.create(
            solicitud=solicitud,
            monto_total=monto,
            metodo='efectivo',
            estado=estado,
            fecha_pago=fecha if estado == 'pagado' else None
        )

    def test_administrador_puede_consultar_finanzas(self):
        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)

    def test_usuario_normal_no_puede_consultar_finanzas(self):
        self.client.force_authenticate(
            user=self.usuario_normal
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 403)

    def test_usuario_no_autenticado_no_puede_consultar_finanzas(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 401)

    def test_calcula_correctamente_los_totales(self):
        ahora = timezone.now()

        self.crear_pago(
            Decimal('100000.00'),
            ahora
        )

        self.crear_pago(
            Decimal('200000.00'),
            ahora
        )

        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)

        resumen = respuesta.data['resumen']

        self.assertEqual(
            resumen['total_pagado'],
            Decimal('300000.00')
        )

        self.assertEqual(
            resumen['ganancia_servihome'],
            Decimal('30000.00')
        )

        self.assertEqual(
            resumen['total_profesionales'],
            Decimal('270000.00')
        )

        self.assertEqual(resumen['cantidad_pagos'], 2)

    def test_no_cuenta_pagos_pendientes(self):
        ahora = timezone.now()

        self.crear_pago(
            Decimal('100000.00'),
            ahora
        )

        self.crear_pago(
            Decimal('50000.00'),
            ahora,
            estado='pendiente'
        )

        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.get(self.url)

        resumen = respuesta.data['resumen']

        self.assertEqual(
            resumen['total_pagado'],
            Decimal('100000.00')
        )

        self.assertEqual(resumen['cantidad_pagos'], 1)

    def test_acepta_los_cuatro_periodos(self):
        self.client.force_authenticate(
            user=self.usuario_admin
        )

        for periodo in ['dia', 'semana', 'mes', 'ano']:
            respuesta = self.client.get(
                self.url,
                {'periodo': periodo}
            )

            self.assertEqual(
                respuesta.status_code,
                200,
                msg=f'Falló el periodo: {periodo}'
            )

            self.assertEqual(
                respuesta.data['periodo_seleccionado'],
                periodo
            )

    def test_rechaza_periodo_invalido(self):
        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.get(
            self.url,
            {'periodo': 'invalido'}
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )
class IncidentesTests(APITestCase):

    def setUp(self):
        # Usuarios
        self.usuario_cliente = User.objects.create_user(
            username='cliente_incidente',
            password='ClaveCliente123!'
        )

        self.usuario_otro_cliente = User.objects.create_user(
            username='otro_cliente_incidente',
            password='ClaveCliente123!'
        )

        self.usuario_profesional = User.objects.create_user(
            username='profesional_incidente',
            password='ClaveProfesional123!'
        )

        self.usuario_admin = User.objects.create_superuser(
            username='admin_incidente',
            password='ClaveAdmin123!',
            email='admin_incidente@test.com'
        )

        # Perfiles
        self.cliente = self.usuario_cliente.perfil
        self.otro_cliente = self.usuario_otro_cliente.perfil
        self.profesional = self.usuario_profesional.perfil

        self.profesional.rol = 'profesional'
        self.profesional.save(update_fields=['rol'])

        # Categoría y servicio
        self.categoria = Categoria.objects.create(
            nombre='Categoría incidentes',
            descripcion='Categoría para pruebas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio incidentes',
            descripcion='Servicio para pruebas',
            precio_base=Decimal('50000.00'),
            activo=True
        )

        # Solicitud del cliente
        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud de prueba',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='pendiente'
        )

        self.url_crear = '/api/incidentes/'
        self.url_admin = '/api/admin/incidentes/'

    def datos_incidente(self):
        return {
            'solicitud': self.solicitud.pk,
            'tipo': 'danos_materiales',
            'descripcion': 'Se produjo un daño durante el servicio.'
        }

    def crear_incidente(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        return self.client.post(
            self.url_crear,
            self.datos_incidente(),
            format='json'
        )

    def test_cliente_puede_reportar_incidente(self):
        response = self.crear_incidente()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Incidente.objects.count(), 1)

        incidente = Incidente.objects.first()
        self.assertEqual(incidente.reportado_por, self.cliente)
        self.assertEqual(incidente.estado, 'pendiente')

    def test_cliente_no_puede_reportar_en_solicitud_ajena(self):
        otra_solicitud = SolicitudServicio.objects.create(
            cliente=self.otro_cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud de otro cliente',
            direccion_servicio='Otra dirección',
            fecha_solicitada=timezone.now() + timedelta(days=3),
            estado='pendiente'
        )

        self.client.force_authenticate(user=self.usuario_cliente)

        datos = self.datos_incidente()
        datos['solicitud'] = otra_solicitud.pk

        response = self.client.post(
            self.url_crear,
            datos,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Incidente.objects.count(), 0)

    def test_profesional_no_puede_reportar(self):
        self.client.force_authenticate(user=self.usuario_profesional)

        response = self.client.post(
            self.url_crear,
            self.datos_incidente(),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_usuario_anonimo_no_puede_reportar(self):
        response = self.client.post(
            self.url_crear,
            self.datos_incidente(),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_administrador_puede_listar_incidentes(self):
        self.crear_incidente()

        self.client.force_authenticate(user=self.usuario_admin)

        response = self.client.get(self.url_admin)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_usuario_normal_no_puede_listar_incidentes_admin(self):
        self.client.force_authenticate(user=self.usuario_cliente)

        response = self.client.get(self.url_admin)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_administrador_puede_gestionar_incidente(self):
        self.crear_incidente()

        incidente = Incidente.objects.first()

        self.client.force_authenticate(user=self.usuario_admin)

        response = self.client.patch(
            f'{self.url_admin}{incidente.pk}/',
            {
                'estado': 'resuelto',
                'respuesta_administrador': 'Incidente revisado y resuelto.'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        incidente.refresh_from_db()

        self.assertEqual(incidente.estado, 'resuelto')
        self.assertEqual(
            incidente.respuesta_administrador,
            'Incidente revisado y resuelto.'
        )

class FacturasPDFTests(APITestCase):

    def setUp(self):
        self.usuario_cliente = User.objects.create_user(
            username='cliente_factura',
            password='ClaveCliente123!'
        )

        self.usuario_otro_cliente = User.objects.create_user(
            username='otro_cliente_factura',
            password='ClaveOtro123!'
        )

        self.usuario_profesional = User.objects.create_user(
            username='profesional_factura',
            password='ClaveProfesional123!'
        )

        # Se crea como administrador sin Perfil asociado.
        self.usuario_admin = User.objects.create_user(
            username='admin_factura',
            password='ClaveAdmin123!',
            is_staff=True
        )

        self.cliente = self.usuario_cliente.perfil
        self.otro_cliente = self.usuario_otro_cliente.perfil
        self.profesional = self.usuario_profesional.perfil

        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.otro_cliente.rol = 'cliente'
        self.otro_cliente.save(update_fields=['rol'])

        self.profesional.rol = 'profesional'
        self.profesional.save(update_fields=['rol'])

        self.categoria = Categoria.objects.create(
            nombre='Categoría factura test',
            descripcion='Pruebas de facturas'
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio factura test',
            descripcion='Servicio para probar facturas',
            precio_base=Decimal('50000.00')
        )

        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Trabajo de prueba para factura',
            direccion_servicio='Dirección de prueba',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='completada',
            precio_acordado=Decimal('100000.00')
        )

        self.pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('100000.00'),
            porcentaje_comision=Decimal('10.00'),
            monto_comision=Decimal('10000.00'),
            monto_profesional=Decimal('90000.00'),
            metodo='transferencia',
            estado='pagado',
            referencia='REF-FACTURA-TEST',
            fecha_pago=timezone.now()
        )

        self.url = f'/api/pagos/{self.pago.pk}/factura/'

    def test_cliente_puede_descargar_su_factura(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta['Content-Type'],
            'application/pdf'
        )
        self.assertIn(
            'attachment;',
            respuesta['Content-Disposition']
        )
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

    def test_otro_cliente_no_puede_descargar_factura(self):
        self.client.force_authenticate(
            user=self.usuario_otro_cliente
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 403)

    def test_profesional_no_puede_descargar_factura(self):
        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_sin_perfil_puede_descargar_factura(self):
        self.client.force_authenticate(
            user=self.usuario_admin
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta['Content-Type'],
            'application/pdf'
        )
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

    def test_no_se_genera_factura_de_pago_pendiente(self):
        self.pago.estado = 'pendiente'
        self.pago.save(update_fields=['estado'])

        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 400)

class CrearOfertaTests(APITestCase):

    def setUp(self):
        self.url = '/api/mis-ofertas/'

        self.usuario_profesional = User.objects.create_user(
            username='profesional_crear_oferta',
            password='ClaveProfesional123!'
        )
        self.profesional = self.usuario_profesional.perfil
        self.profesional.rol = 'profesional'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.usuario_cliente = User.objects.create_user(
            username='cliente_crear_oferta',
            password='ClaveCliente123!'
        )
        self.cliente = self.usuario_cliente.perfil
        self.cliente.rol = 'cliente'
        self.cliente.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría ofertas test',
            descripcion='Categoría para pruebas de ofertas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio ofertas test',
            descripcion='Servicio para pruebas de creación',
            precio_base=Decimal('50000.00'),
            activo=True
        )

    def test_profesional_aprobado_puede_crear_oferta(self):
        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '50000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 201)

        oferta = ServicioProfesional.objects.get(
            profesional=self.profesional,
            servicio=self.servicio
        )

        self.assertEqual(oferta.precio, Decimal('50000.00'))
        self.assertEqual(oferta.estado_aprobacion, 'pendiente')

    def test_cliente_no_puede_crear_oferta(self):
        self.client.force_authenticate(
            user=self.usuario_cliente
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '50000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_profesional_sin_identidad_aprobada_no_puede_ofertar(self):
        self.profesional.estado_identidad = 'pendiente'
        self.profesional.save(update_fields=['estado_identidad'])

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '50000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_profesional_sin_verificacion_aprobada_no_puede_ofertar(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '50000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_precio_inferior_al_minimo_es_rechazado(self):
        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '25000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_se_puede_crear_oferta_duplicada(self):
        ServicioProfesional.objects.create(
            profesional=self.profesional,
            servicio=self.servicio,
            precio=Decimal('50000.00'),
            estado_aprobacion='aprobado'
        )

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '60000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_se_puede_ofertar_un_servicio_inactivo(self):
        self.servicio.activo = False
        self.servicio.save(update_fields=['activo'])

        self.client.force_authenticate(
            user=self.usuario_profesional
        )

        respuesta = self.client.post(
            self.url,
            {
                'servicio': self.servicio.pk,
                'precio': '50000.00'
            },
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)
class OfertaPublicaTests(APITestCase):

    def setUp(self):
        self.usuario_profesional = User.objects.create_user(
            username='profesional_publico_test',
            password='ClaveProfesional123!'
        )

        self.profesional = self.usuario_profesional.perfil
        self.profesional.rol = 'profesional'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save()

        self.categoria = Categoria.objects.create(
            nombre='Categoría pública test',
            descripcion='Prueba de ofertas públicas',
            activa=True
        )

        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Servicio público test',
            descripcion='Servicio para pruebas públicas',
            precio_base=Decimal('50000.00'),
            activo=True
        )

        self.oferta = ServicioProfesional.objects.create(
            servicio=self.servicio,
            profesional=self.profesional,
            precio=Decimal('50000.00'),
            estado_aprobacion='aprobado'
        )

        self.url = '/api/ofertas/'

    def test_oferta_aprobada_de_profesional_aprobado_aparece(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 1)
        self.assertEqual(respuesta.data[0]['id'], self.oferta.pk)

    def test_oferta_pendiente_no_aparece(self):
        self.oferta.estado_aprobacion = 'pendiente'
        self.oferta.save(update_fields=['estado_aprobacion'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)

    def test_oferta_rechazada_no_aparece(self):
        self.oferta.estado_aprobacion = 'rechazado'
        self.oferta.save(update_fields=['estado_aprobacion'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)

    def test_profesional_con_verificacion_pendiente_no_aparece(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)

    def test_profesional_con_verificacion_rechazada_no_aparece(self):
        self.profesional.estado_verificacion = 'rechazado'
        self.profesional.save(update_fields=['estado_verificacion'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)

    def test_profesional_no_disponible_no_aparece(self):
        self.profesional.disponible = False
        self.profesional.save(update_fields=['disponible'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)

    def test_servicio_inactivo_no_aparece(self):
        self.servicio.activo = False
        self.servicio.save(update_fields=['activo'])

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 0)