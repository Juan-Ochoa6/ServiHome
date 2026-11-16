from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from servicios.models import (
    Categoria,
    Servicio,
    ServicioProfesional,
    SolicitudServicio,
    PropuestaPrecio,
)


class PropuestasQATests(APITestCase):

    def setUp(self):
        self.usuario_cliente = User.objects.create_user(
            username='qa_cliente',
            password='ClaveQaCliente123!'
        )
        self.usuario_profesional = User.objects.create_user(
            username='qa_profesional',
            password='ClaveQaProfesional123!'
        )

        self.cliente = self.usuario_cliente.perfil
        self.cliente.rol = 'cliente'
        self.cliente.save(update_fields=['rol'])

        self.profesional = self.usuario_profesional.perfil
        self.profesional.rol = 'profesional'
        self.profesional.estado_verificacion = 'aprobado'
        self.profesional.estado_identidad = 'aprobado'
        self.profesional.disponible = True
        self.profesional.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
                'disponible',
            ]
        )

        self.categoria = Categoria.objects.create(
            nombre='Plomería QA',
            descripcion='Categoría para pruebas QA',
            activa=True
        )
        self.servicio = Servicio.objects.create(
            categoria=self.categoria,
            nombre='Reparación QA',
            descripcion='Servicio para pruebas QA',
            precio_base=Decimal('50000.00'),
            activo=True
        )
        ServicioProfesional.objects.create(
            servicio=self.servicio,
            profesional=self.profesional,
            precio=Decimal('50000.00'),
            estado_aprobacion='aprobado'
        )

        self.solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente,
            profesional=self.profesional,
            servicio=self.servicio,
            descripcion='Solicitud para pruebas QA',
            direccion_servicio='Dirección QA',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='pendiente'
        )

        self.url = f'/api/solicitudes/{self.solicitud.pk}/propuestas/'

    def test_cliente_crea_propuesta_valida(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.post(
            self.url, {'precio': '50000'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            PropuestaPrecio.objects.filter(solicitud=self.solicitud).count(),
            1
        )

    def test_precio_bajo_minimo_da_400(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.post(
            self.url, {'precio': '29999'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            PropuestaPrecio.objects.filter(solicitud=self.solicitud).count(),
            0
        )

    def test_contrapropuesta_reemplaza_la_pendiente(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        self.client.post(self.url, {'precio': '40000'}, format='json')

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url, {'precio': '45000'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        propuestas = PropuestaPrecio.objects.filter(
            solicitud=self.solicitud
        ).order_by('fecha_creacion')
        self.assertEqual(propuestas.count(), 2)
        self.assertEqual(propuestas[0].estado, 'reemplazada')
        self.assertEqual(propuestas[1].estado, 'pendiente')

    def test_proponente_no_puede_proponer_dos_veces_seguidas(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        self.client.post(self.url, {'precio': '40000'}, format='json')

        respuesta = self.client.post(
            self.url, {'precio': '42000'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        propuestas = PropuestaPrecio.objects.filter(solicitud=self.solicitud)
        self.assertEqual(propuestas.count(), 1)
        self.assertEqual(propuestas.first().estado, 'pendiente')

    def test_profesional_rechaza_propuesta_del_cliente(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        self.client.post(self.url, {'precio': '40000'}, format='json')
        propuesta = PropuestaPrecio.objects.get(solicitud=self.solicitud)

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            f'{self.url}{propuesta.pk}/',
            {'accion': 'rechazar'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        propuesta.refresh_from_db()
        self.assertEqual(propuesta.estado, 'rechazada')

    def test_tercero_ajeno_no_puede_proponer(self):
        usuario_ajeno = User.objects.create_user(
            username='qa_ajeno',
            password='ClaveQaAjeno123!'
        )
        perfil_ajeno = usuario_ajeno.perfil
        perfil_ajeno.rol = 'profesional'
        perfil_ajeno.estado_verificacion = 'aprobado'
        perfil_ajeno.estado_identidad = 'aprobado'
        perfil_ajeno.disponible = True
        perfil_ajeno.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
                'disponible',
            ]
        )

        self.client.force_authenticate(user=usuario_ajeno)
        respuesta = self.client.post(
            self.url, {'precio': '45000'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            PropuestaPrecio.objects.filter(solicitud=self.solicitud).count(),
            0
        )

    def test_proponente_no_puede_responder_su_propia_propuesta(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        self.client.post(self.url, {'precio': '40000'}, format='json')
        propuesta = PropuestaPrecio.objects.get(solicitud=self.solicitud)

        respuesta = self.client.patch(
            f'{self.url}{propuesta.pk}/',
            {'accion': 'aceptar'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

        propuesta.refresh_from_db()
        self.assertEqual(propuesta.estado, 'pendiente')

    def test_propuesta_no_se_responde_dos_veces(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        self.client.post(self.url, {'precio': '40000'}, format='json')
        propuesta = PropuestaPrecio.objects.get(solicitud=self.solicitud)

        self.client.force_authenticate(user=self.usuario_profesional)
        primera = self.client.patch(
            f'{self.url}{propuesta.pk}/',
            {'accion': 'aceptar'},
            format='json'
        )
        self.assertEqual(primera.status_code, status.HTTP_200_OK)

        segunda = self.client.patch(
            f'{self.url}{propuesta.pk}/',
            {'accion': 'rechazar'},
            format='json'
        )
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

        propuesta.refresh_from_db()
        self.assertEqual(propuesta.estado, 'aceptada')