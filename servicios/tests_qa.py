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
    Pago,
)


class BaseQA(APITestCase):

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
        self.url_estado = f'/api/solicitudes/{self.solicitud.pk}/estado/'


class PropuestasQATests(BaseQA):

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


class EstadosQATests(BaseQA):

    def test_cliente_no_puede_iniciar_el_servicio(self):
        self.solicitud.estado = 'aceptada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'en_proceso', 'codigo': '123456'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'aceptada')

    def test_cliente_no_puede_cancelar_en_proceso(self):
        self.solicitud.estado = 'en_proceso'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'cancelada'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'en_proceso')

    def test_profesional_no_puede_saltarse_pasos(self):
        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'completada', 'codigo': '123456'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'pendiente')

    def test_profesional_ajeno_no_puede_cambiar_estado(self):
        usuario_ajeno = User.objects.create_user(
            username='qa_ajeno_estado',
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
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'rechazada'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'pendiente')

    def test_solicitud_cancelada_no_se_puede_reactivar(self):
        self.solicitud.estado = 'cancelada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'en_proceso', 'codigo': '123456'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'cancelada')

    def test_codigo_de_inicio_incorrecto_da_400(self):
        self.solicitud.estado = 'aceptada'
        self.solicitud.codigo_inicio = '123456'
        self.solicitud.save(update_fields=['estado', 'codigo_inicio'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'en_proceso', 'codigo': '654321'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'aceptada')

    def test_inicio_correcto_y_codigo_no_se_reutiliza(self):
        self.solicitud.estado = 'aceptada'
        self.solicitud.codigo_inicio = '123456'
        self.solicitud.save(update_fields=['estado', 'codigo_inicio'])

        self.client.force_authenticate(user=self.usuario_profesional)
        primera = self.client.patch(
            self.url_estado,
            {'estado': 'en_proceso', 'codigo': '123456'},
            format='json'
        )
        self.assertEqual(primera.status_code, status.HTTP_200_OK)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'en_proceso')
        self.assertEqual(len(self.solicitud.codigo_finalizacion), 6)

        segunda = self.client.patch(
            self.url_estado,
            {'estado': 'en_proceso', 'codigo': '123456'},
            format='json'
        )
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

    def test_solicitud_rechazada_no_se_puede_reactivar(self):
        self.solicitud.estado = 'rechazada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'cancelada'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'rechazada')

    def test_codigo_de_finalizacion_incorrecto_da_400(self):
        self.solicitud.estado = 'en_proceso'
        self.solicitud.codigo_finalizacion = '654321'
        self.solicitud.save(
            update_fields=['estado', 'codigo_finalizacion']
        )

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'completada', 'codigo': '111111'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'en_proceso')


class PagosQATests(BaseQA):

    def test_pago_fallido_no_tiene_salida(self):
        usuario_admin = User.objects.create_user(
            username='qa_admin',
            password='ClaveQaAdmin123!',
            is_staff=True
        )
        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('50000.00'),
            metodo='efectivo'
        )
        pago.estado = 'fallido'
        pago.save()

        self.client.force_authenticate(user=usuario_admin)
        respuesta = self.client.patch(
            f'/api/pagos/{pago.pk}/estado/',
            {'estado': 'pagado'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'fallido')

    def test_pago_pagado_se_reembolsa_y_reembolsado_no_tiene_salida(self):
        usuario_admin = User.objects.create_user(
            username='qa_admin',
            password='ClaveQaAdmin123!',
            is_staff=True
        )
        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('50000.00'),
            metodo='efectivo'
        )
        pago.estado = 'pagado'
        pago.save()

        self.client.force_authenticate(user=usuario_admin)
        url_pago = f'/api/pagos/{pago.pk}/estado/'

        primera = self.client.patch(
            url_pago, {'estado': 'reembolsado'}, format='json'
        )
        self.assertEqual(primera.status_code, status.HTTP_200_OK)

        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'reembolsado')

        segunda = self.client.patch(
            url_pago, {'estado': 'pagado'}, format='json'
        )
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'reembolsado')

    def test_pago_pagado_no_puede_pasar_a_fallido(self):
        usuario_admin = User.objects.create_user(
            username='qa_admin',
            password='ClaveQaAdmin123!',
            is_staff=True
        )
        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('50000.00'),
            metodo='efectivo'
        )
        pago.estado = 'pagado'
        pago.save()

        self.client.force_authenticate(user=usuario_admin)
        respuesta = self.client.patch(
            f'/api/pagos/{pago.pk}/estado/',
            {'estado': 'fallido'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'pagado')

    def test_cliente_y_profesional_no_pueden_cambiar_estado_de_pago(self):
        pago = Pago.objects.create(
            solicitud=self.solicitud,
            monto_total=Decimal('50000.00'),
            metodo='efectivo'
        )
        url_pago = f'/api/pagos/{pago.pk}/estado/'

        self.client.force_authenticate(user=self.usuario_cliente)
        como_cliente = self.client.patch(
            url_pago, {'estado': 'pagado'}, format='json'
        )
        self.assertEqual(como_cliente.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.usuario_profesional)
        como_profesional = self.client.patch(
            url_pago, {'estado': 'pagado'}, format='json'
        )
        self.assertEqual(
            como_profesional.status_code, status.HTTP_403_FORBIDDEN
        )

        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'pendiente')


class NegociacionQATests(BaseQA):

    def test_profesional_no_puede_aceptar_sin_propuesta_de_precio(self):
        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_estado,
            {'estado': 'aceptada'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'pendiente')



class OfertasQATests(BaseQA):

    def test_cliente_no_puede_gestionar_ofertas(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.get('/api/mis-ofertas/')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_editar_precio_de_oferta_aprobada_la_devuelve_a_pendiente(self):
        oferta = ServicioProfesional.objects.get(
            profesional=self.profesional,
            servicio=self.servicio
        )
        self.assertEqual(oferta.estado_aprobacion, 'aprobado')

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            f'/api/mis-ofertas/{oferta.pk}/',
            {'precio': '60000'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        oferta.refresh_from_db()
        self.assertEqual(oferta.precio, Decimal('60000.00'))
        self.assertEqual(oferta.estado_aprobacion, 'pendiente')

    def test_profesional_no_puede_ver_ni_tocar_oferta_de_otro(self):
        usuario_ajeno = User.objects.create_user(
            username='qa_ajeno_oferta',
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

        oferta = ServicioProfesional.objects.get(
            profesional=self.profesional,
            servicio=self.servicio
        )
        url_oferta = f'/api/mis-ofertas/{oferta.pk}/'

        self.client.force_authenticate(user=usuario_ajeno)
        ver = self.client.get(url_oferta)
        self.assertEqual(ver.status_code, status.HTTP_404_NOT_FOUND)

        editar = self.client.patch(
            url_oferta, {'precio': '70000'}, format='json'
        )
        self.assertEqual(editar.status_code, status.HTTP_404_NOT_FOUND)

        borrar = self.client.delete(url_oferta)
        self.assertEqual(borrar.status_code, status.HTTP_404_NOT_FOUND)

        oferta.refresh_from_db()
        self.assertEqual(oferta.precio, Decimal('50000.00'))
        self.assertEqual(oferta.estado_aprobacion, 'aprobado')



from servicios.models import TrabajoPortafolio


class PortafolioQATests(BaseQA):

    def crear_trabajo(self, titulo, activo=True):
        return TrabajoPortafolio.objects.create(
            profesional=self.profesional,
            titulo=titulo,
            descripcion='Trabajo para pruebas QA',
            imagen='portafolio_profesionales/qa.jpg',
            activo=activo
        )

    def lista_de_resultados(self, respuesta):
        datos = respuesta.json()
        if isinstance(datos, dict):
            return datos['results']
        return datos

    def test_cliente_no_puede_gestionar_portafolio(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.get('/api/mi-portafolio/')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_portafolio_publico_sin_sesion_solo_muestra_activos(self):
        self.crear_trabajo('Trabajo visible', activo=True)
        self.crear_trabajo('Trabajo oculto', activo=False)

        respuesta = self.client.get(
            f'/api/profesionales/{self.profesional.pk}/portafolio/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        titulos = [
            trabajo['titulo']
            for trabajo in self.lista_de_resultados(respuesta)
        ]
        self.assertEqual(titulos, ['Trabajo visible'])

    def test_portafolio_publico_vacio_si_profesional_no_esta_aprobado(self):
        self.crear_trabajo('Trabajo de profesional no aprobado')
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        respuesta = self.client.get(
            f'/api/profesionales/{self.profesional.pk}/portafolio/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.lista_de_resultados(respuesta), [])

    def test_profesional_no_puede_ver_ni_borrar_trabajo_de_otro(self):
        usuario_ajeno = User.objects.create_user(
            username='qa_ajeno_portafolio',
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

        trabajo = self.crear_trabajo('Trabajo ajeno')
        url_trabajo = f'/api/mi-portafolio/{trabajo.pk}/'

        self.client.force_authenticate(user=usuario_ajeno)
        ver = self.client.get(url_trabajo)
        self.assertEqual(ver.status_code, status.HTTP_404_NOT_FOUND)

        borrar = self.client.delete(url_trabajo)
        self.assertEqual(borrar.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(
            TrabajoPortafolio.objects.filter(pk=trabajo.pk).exists()
        )



from django.core.files.uploadedfile import SimpleUploadedFile
from usuarios.models import DocumentoVerificacion


class DocumentosQATests(BaseQA):

    def crear_profesional_ajeno(self, username):
        usuario = User.objects.create_user(
            username=username,
            password='ClaveQaAjeno123!'
        )
        perfil = usuario.perfil
        perfil.rol = 'profesional'
        perfil.estado_verificacion = 'aprobado'
        perfil.estado_identidad = 'aprobado'
        perfil.disponible = True
        perfil.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
                'disponible',
            ]
        )
        return usuario

    def crear_admin(self):
        return User.objects.create_user(
            username='qa_admin_documentos',
            password='ClaveQaAdmin123!',
            is_staff=True
        )

    def test_profesional_solo_ve_sus_propios_documentos(self):
        usuario_ajeno = self.crear_profesional_ajeno('qa_ajeno_documentos')

        propio = DocumentoVerificacion.objects.create(
            perfil=self.profesional,
            tipo='identidad',
            archivo='qa_propio.pdf'
        )
        DocumentoVerificacion.objects.create(
            perfil=usuario_ajeno.perfil,
            tipo='identidad',
            archivo='qa_ajeno.pdf'
        )

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.get('/api/usuarios/mis-documentos/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        datos = respuesta.json()
        if isinstance(datos, dict):
            datos = datos['results']
        self.assertEqual([doc['id'] for doc in datos], [propio.pk])

    def test_cliente_no_puede_subir_documento_que_no_es_identidad(self):
        archivo = SimpleUploadedFile(
            'qa_experiencia.pdf',
            b'%PDF-1.4 prueba qa',
            content_type='application/pdf'
        )

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.post(
            '/api/usuarios/mis-documentos/',
            {'tipo': 'experiencia', 'archivo': archivo},
            format='multipart'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            DocumentoVerificacion.objects.filter(perfil=self.cliente).count(),
            0
        )

    def test_admin_rechaza_identidad_y_se_actualiza_el_perfil(self):
        documento = DocumentoVerificacion.objects.create(
            perfil=self.profesional,
            tipo='identidad',
            archivo='qa_identidad.pdf'
        )

        self.client.force_authenticate(user=self.crear_admin())
        respuesta = self.client.patch(
            f'/api/usuarios/admin/documentos/{documento.pk}/',
            {'estado': 'rechazado'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        documento.refresh_from_db()
        self.assertEqual(documento.estado, 'rechazado')

        self.profesional.refresh_from_db()
        self.assertEqual(self.profesional.estado_identidad, 'rechazado')

    def test_cliente_y_profesional_no_pueden_aprobar_documentos(self):
        documento = DocumentoVerificacion.objects.create(
            perfil=self.profesional,
            tipo='identidad',
            archivo='qa_identidad.pdf'
        )
        url_documento = f'/api/usuarios/admin/documentos/{documento.pk}/'

        self.client.force_authenticate(user=self.usuario_cliente)
        como_cliente = self.client.patch(
            url_documento, {'estado': 'aprobado'}, format='json'
        )
        self.assertEqual(como_cliente.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.usuario_profesional)
        como_profesional = self.client.patch(
            url_documento, {'estado': 'aprobado'}, format='json'
        )
        self.assertEqual(
            como_profesional.status_code, status.HTTP_403_FORBIDDEN
        )

        documento.refresh_from_db()
        self.assertEqual(documento.estado, 'pendiente')

    def test_profesional_no_aprobado_solo_ve_su_estado_de_verificacion(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.get('/api/usuarios/mi-verificacion/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            respuesta.json(),
            {'estado_verificacion': 'pendiente'}
        )



class DisponibilidadQATests(BaseQA):

    url_disponibilidad = '/api/usuarios/disponibilidad/'

    def test_sin_sesion_no_puede_cambiar_disponibilidad(self):
        respuesta = self.client.patch(
            self.url_disponibilidad, {'disponible': False}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cliente_no_puede_cambiar_disponibilidad(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_disponibilidad, {'disponible': False}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_profesional_no_aprobado_no_puede_cambiar_disponibilidad(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.patch(
            self.url_disponibilidad, {'disponible': False}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

        self.profesional.refresh_from_db()
        self.assertTrue(self.profesional.disponible)

    def test_valor_que_no_es_true_o_false_da_400(self):
        self.client.force_authenticate(user=self.usuario_profesional)

        con_texto = self.client.patch(
            self.url_disponibilidad, {'disponible': 'si'}, format='json'
        )
        self.assertEqual(con_texto.status_code, status.HTTP_400_BAD_REQUEST)

        con_cuerpo_vacio = self.client.patch(
            self.url_disponibilidad, {}, format='json'
        )
        self.assertEqual(
            con_cuerpo_vacio.status_code, status.HTTP_400_BAD_REQUEST
        )

        self.profesional.refresh_from_db()
        self.assertTrue(self.profesional.disponible)

    def test_profesional_aprobado_pausa_y_reactiva_su_disponibilidad(self):
        self.client.force_authenticate(user=self.usuario_profesional)

        pausa = self.client.patch(
            self.url_disponibilidad, {'disponible': False}, format='json'
        )
        self.assertEqual(pausa.status_code, status.HTTP_200_OK)
        self.assertFalse(pausa.json()['disponible'])
        self.profesional.refresh_from_db()
        self.assertFalse(self.profesional.disponible)

        activa = self.client.patch(
            self.url_disponibilidad, {'disponible': True}, format='json'
        )
        self.assertEqual(activa.status_code, status.HTTP_200_OK)
        self.assertTrue(activa.json()['disponible'])
        self.profesional.refresh_from_db()
        self.assertTrue(self.profesional.disponible)



class PerfilQATests(BaseQA):

    url_perfil = '/api/usuarios/perfil/'

    def test_sin_sesion_no_puede_ver_el_perfil(self):
        respuesta = self.client.get(self.url_perfil)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cliente_actualiza_sus_datos_de_contacto(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_perfil,
            {
                'telefono': '3001234567',
                'direccion': 'Calle QA 123',
                'first_name': 'Qa',
            },
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        self.cliente.refresh_from_db()
        self.usuario_cliente.refresh_from_db()
        self.assertEqual(self.cliente.telefono, '3001234567')
        self.assertEqual(self.cliente.direccion, 'Calle QA 123')
        self.assertEqual(self.usuario_cliente.first_name, 'Qa')

    def test_no_se_pueden_cambiar_rol_ni_verificacion_ni_disponibilidad(self):
        self.client.force_authenticate(user=self.usuario_cliente)
        original_cliente = (
            self.cliente.rol,
            self.cliente.estado_verificacion,
            self.cliente.estado_identidad,
            self.cliente.disponible,
        )
        como_cliente = self.client.patch(
            self.url_perfil,
            {
                'rol': 'profesional',
                'estado_verificacion': 'aprobado',
                'estado_identidad': 'aprobado',
                'disponible': False,
            },
            format='json'
        )
        self.assertEqual(como_cliente.status_code, status.HTTP_200_OK)
        self.cliente.refresh_from_db()
        self.assertEqual(
            (
                self.cliente.rol,
                self.cliente.estado_verificacion,
                self.cliente.estado_identidad,
                self.cliente.disponible,
            ),
            original_cliente
        )

        self.client.force_authenticate(user=self.usuario_profesional)
        como_profesional = self.client.patch(
            self.url_perfil,
            {
                'rol': 'cliente',
                'estado_verificacion': 'rechazado',
                'estado_identidad': 'rechazado',
                'disponible': False,
            },
            format='json'
        )
        self.assertEqual(como_profesional.status_code, status.HTTP_200_OK)
        self.profesional.refresh_from_db()
        self.assertEqual(self.profesional.rol, 'profesional')
        self.assertEqual(self.profesional.estado_verificacion, 'aprobado')
        self.assertEqual(self.profesional.estado_identidad, 'aprobado')
        self.assertTrue(self.profesional.disponible)

    def test_profesional_no_aprobado_no_puede_ver_su_perfil(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.get(self.url_perfil)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_correo_con_formato_invalido_da_400(self):
        correo_original = self.usuario_cliente.email

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.patch(
            self.url_perfil,
            {'email': 'esto-no-es-un-correo'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

        self.usuario_cliente.refresh_from_db()
        self.assertEqual(self.usuario_cliente.email, correo_original)



class OfertasCreacionQATests(BaseQA):

    url_ofertas = '/api/mis-ofertas/'

    def crear_servicio(self, nombre, activo=True):
        return Servicio.objects.create(
            categoria=self.categoria,
            nombre=nombre,
            descripcion='Servicio para pruebas QA',
            precio_base=Decimal('50000.00'),
            activo=activo
        )

    def cantidad_de_ofertas(self):
        return ServicioProfesional.objects.filter(
            profesional=self.profesional
        ).count()

    def test_oferta_con_precio_bajo_el_minimo_da_400(self):
        otro_servicio = self.crear_servicio('Servicio QA precio bajo')

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url_ofertas,
            {'servicio': otro_servicio.pk, 'precio': '29999'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.cantidad_de_ofertas(), 1)

    def test_oferta_con_precio_exacto_del_minimo_se_acepta(self):
        otro_servicio = self.crear_servicio('Servicio QA precio minimo')

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url_ofertas,
            {'servicio': otro_servicio.pk, 'precio': '30000'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        oferta = ServicioProfesional.objects.get(
            profesional=self.profesional,
            servicio=otro_servicio
        )
        self.assertEqual(oferta.estado_aprobacion, 'pendiente')

    def test_no_se_puede_ofertar_un_servicio_inactivo(self):
        servicio_inactivo = self.crear_servicio(
            'Servicio QA inactivo', activo=False
        )

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url_ofertas,
            {'servicio': servicio_inactivo.pk, 'precio': '50000'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.cantidad_de_ofertas(), 1)

    def test_no_se_puede_ofertar_dos_veces_el_mismo_servicio(self):
        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url_ofertas,
            {'servicio': self.servicio.pk, 'precio': '50000'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.cantidad_de_ofertas(), 1)

    def test_profesional_no_aprobado_no_puede_crear_ofertas(self):
        otro_servicio = self.crear_servicio('Servicio QA no aprobado')
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.post(
            self.url_ofertas,
            {'servicio': otro_servicio.pk, 'precio': '50000'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.cantidad_de_ofertas(), 1)


class RegistroQATests(APITestCase):

    url_registro = '/api/usuarios/registro/'

    def setUp(self):
        self.existente = User.objects.create_user(
            username='qa_existente',
            email='qa_existente@example.com',
            password='ClaveQaExistente123!'
        )

    def datos(self, **cambios):
        datos = {
            'username': 'qa_nuevo',
            'email': 'qa_nuevo@example.com',
            'password': 'ClaveQaRegistro123!',
            'first_name': 'Qa',
            'last_name': 'Nuevo',
            'rol': 'cliente',
            'telefono': '3001234567',
            'direccion': 'Calle QA 123',
        }
        datos.update(cambios)
        return datos

    def test_username_duplicado_con_otras_mayusculas_da_400(self):
        respuesta = self.client.post(
            self.url_registro,
            self.datos(username='QA_EXISTENTE'),
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            User.objects.filter(email='qa_nuevo@example.com').exists()
        )

    def test_correo_duplicado_con_otras_mayusculas_da_400(self):
        respuesta = self.client.post(
            self.url_registro,
            self.datos(email='QA_Existente@Example.com'),
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='qa_nuevo').exists())

    def test_registro_sin_correo_da_400(self):
        datos = self.datos()
        datos.pop('email')

        respuesta = self.client.post(
            self.url_registro, datos, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='qa_nuevo').exists())

    def test_registro_con_contrasena_debil_da_400(self):
        respuesta = self.client.post(
            self.url_registro,
            self.datos(password='12345678'),
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='qa_nuevo').exists())

    def test_registro_con_rol_inventado_da_400(self):
        respuesta = self.client.post(
            self.url_registro,
            self.datos(rol='superman'),
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='qa_nuevo').exists())


from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class ResenasVisiblesQATests(BaseQA):

    def crear_resena(self, calificacion=4):
        self.solicitud.estado = 'completada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_cliente)
        respuesta = self.client.post(
            f'/api/solicitudes/{self.solicitud.pk}/resena/',
            {'calificacion': calificacion, 'comentario': 'Comentario QA'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=None)

    def test_resenas_publicas_se_ven_sin_sesion(self):
        self.crear_resena(calificacion=5)

        respuesta = self.client.get(
            f'/api/profesionales/{self.profesional.pk}/resenas/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        datos = respuesta.json()
        if isinstance(datos, dict):
            datos = datos['results']
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]['calificacion'], 5)
        self.assertEqual(datos[0]['cliente_nombre'], 'qa_cliente')
        self.assertEqual(datos[0]['profesional_nombre'], 'qa_profesional')

    def test_resenas_de_profesional_inexistente_da_404(self):
        respuesta = self.client.get('/api/profesionales/999999/resenas/')
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_resenas_del_id_de_un_cliente_da_404(self):
        respuesta = self.client.get(
            f'/api/profesionales/{self.cliente.pk}/resenas/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_reputacion_calcula_promedio_y_total(self):
        self.crear_resena(calificacion=4)

        respuesta = self.client.get(
            f'/api/profesionales/{self.profesional.pk}/reputacion/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        datos = respuesta.json()
        self.assertEqual(float(datos['promedio_calificacion']), 4.0)
        self.assertEqual(datos['total_resenas'], 1)

    def test_reputacion_del_id_de_un_cliente_da_404(self):
        respuesta = self.client.get(
            f'/api/profesionales/{self.cliente.pk}/reputacion/'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)


class RenovacionTokensQATests(BaseQA):

    url_refresh = '/api/usuarios/token/refresh/'

    def test_refresh_falso_da_401(self):
        respuesta = self.client.post(
            self.url_refresh, {'refresh': 'token-falso'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_vacio_da_400(self):
        respuesta = self.client.post(self.url_refresh, {}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_usado_como_refresh_da_401(self):
        access = str(
            RefreshToken.for_user(self.usuario_cliente).access_token
        )
        respuesta = self.client.post(
            self.url_refresh, {'refresh': access}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_valido_entrega_access_y_no_rota(self):
        refresh = str(RefreshToken.for_user(self.usuario_cliente))
        respuesta = self.client.post(
            self.url_refresh, {'refresh': refresh}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        datos = respuesta.json()
        self.assertIn('access', datos)
        self.assertNotIn('refresh', datos)

    def test_access_vencido_da_401_y_uno_valido_da_200(self):
        valido = AccessToken.for_user(self.usuario_cliente)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {valido}')
        con_token_valido = self.client.get('/api/usuarios/perfil/')
        self.assertEqual(con_token_valido.status_code, status.HTTP_200_OK)

        vencido = AccessToken.for_user(self.usuario_cliente)
        vencido.set_exp(from_time=timezone.now() - timedelta(hours=1))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {vencido}')
        con_token_vencido = self.client.get('/api/usuarios/perfil/')
        self.assertEqual(
            con_token_vencido.status_code, status.HTTP_401_UNAUTHORIZED
        )


class ProfesionalesDisponiblesQATests(BaseQA):

    url_profesionales = '/api/usuarios/profesionales/'

    def consultar(self, servicio_id=None):
        self.client.force_authenticate(user=self.usuario_cliente)
        if servicio_id is None:
            return self.client.get(self.url_profesionales)
        return self.client.get(
            self.url_profesionales, {'servicio_id': servicio_id}
        )

    def ids_de(self, respuesta):
        datos = respuesta.json()
        if isinstance(datos, dict):
            datos = datos['results']
        return [item['profesional_id'] for item in datos]

    def test_sin_sesion_da_401(self):
        respuesta = self.client.get(
            self.url_profesionales, {'servicio_id': self.servicio.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profesional_no_puede_consultar_profesionales(self):
        self.client.force_authenticate(user=self.usuario_profesional)
        respuesta = self.client.get(
            self.url_profesionales, {'servicio_id': self.servicio.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_falta_servicio_id_da_400(self):
        respuesta = self.consultar()
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_servicio_id_invalido_da_400(self):
        for valor in ['abc', '0', '-5']:
            with self.subTest(servicio_id=valor):
                respuesta = self.consultar(valor)
                self.assertEqual(
                    respuesta.status_code, status.HTTP_400_BAD_REQUEST
                )

    def test_cliente_ve_al_profesional_que_cumple_todo(self):
        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(respuesta), [self.profesional.pk])

        item = respuesta.json()[0]
        self.assertEqual(item['username'], 'qa_profesional')
        self.assertEqual(float(item['precio']), 50000.0)

    def test_profesional_no_disponible_no_aparece(self):
        self.profesional.disponible = False
        self.profesional.save(update_fields=['disponible'])

        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(respuesta), [])

    def test_oferta_pendiente_no_aparece(self):
        oferta = ServicioProfesional.objects.get(
            profesional=self.profesional,
            servicio=self.servicio
        )
        oferta.estado_aprobacion = 'pendiente'
        oferta.save(update_fields=['estado_aprobacion'])

        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(respuesta), [])

    def test_profesional_sin_aprobar_no_aparece(self):
        self.profesional.estado_verificacion = 'pendiente'
        self.profesional.save(update_fields=['estado_verificacion'])

        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(respuesta), [])

    def test_profesional_sin_identidad_aprobada_no_aparece(self):
        self.profesional.estado_identidad = 'pendiente'
        self.profesional.save(update_fields=['estado_identidad'])

        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.ids_de(respuesta), [])

    def test_resultados_salen_ordenados_por_precio(self):
        usuario_barato = User.objects.create_user(
            username='qa_profesional_barato',
            password='ClaveQaBarato123!'
        )
        perfil_barato = usuario_barato.perfil
        perfil_barato.rol = 'profesional'
        perfil_barato.estado_verificacion = 'aprobado'
        perfil_barato.estado_identidad = 'aprobado'
        perfil_barato.disponible = True
        perfil_barato.save(
            update_fields=[
                'rol',
                'estado_verificacion',
                'estado_identidad',
                'disponible',
            ]
        )
        ServicioProfesional.objects.create(
            servicio=self.servicio,
            profesional=perfil_barato,
            precio=Decimal('40000.00'),
            estado_aprobacion='aprobado'
        )

        respuesta = self.consultar(self.servicio.pk)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.ids_de(respuesta),
            [perfil_barato.pk, self.profesional.pk]
        )




import io
import re
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from servicios.notificaciones import enviar_correo


class CorreosQATests(BaseQA):

    def test_enviar_correo_sin_destinatario_no_envia_nada(self):
        with patch('servicios.notificaciones.send_mail') as enviar:
            resultado = enviar_correo('', 'Asunto', 'Mensaje')

        self.assertFalse(resultado)
        enviar.assert_not_called()

    def test_fallo_al_enviar_correo_no_lanza_error(self):
        with patch(
            'servicios.notificaciones.send_mail',
            side_effect=Exception('fallo de correo')
        ):
            resultado = enviar_correo(
                'alguien@example.com', 'Asunto', 'Mensaje'
            )

        self.assertIn(resultado, [True, False])

    def test_crear_propuesta_avisa_a_la_otra_parte(self):
        self.usuario_profesional.email = 'profesional@example.com'
        self.usuario_profesional.save()

        self.client.force_authenticate(user=self.usuario_cliente)
        with patch('servicios.views.enviar_correo') as enviar:
            with self.captureOnCommitCallbacks(execute=True):
                respuesta = self.client.post(
                    self.url, {'precio': '50000'}, format='json'
                )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        enviar.assert_called_once()
        self.assertEqual(
            enviar.call_args.kwargs['destinatario'],
            'profesional@example.com'
        )
        self.assertEqual(
            enviar.call_args.kwargs['asunto'],
            'Nueva propuesta de precio - ServiHome'
        )

    def test_propuesta_se_crea_aunque_falle_el_correo(self):
        self.usuario_profesional.email = 'profesional@example.com'
        self.usuario_profesional.save()

        self.client.force_authenticate(user=self.usuario_cliente)
        with patch(
            'servicios.notificaciones.send_mail',
            side_effect=Exception('fallo de correo')
        ):
            with self.captureOnCommitCallbacks(execute=True):
                respuesta = self.client.post(
                    self.url, {'precio': '50000'}, format='json'
                )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            PropuestaPrecio.objects.filter(solicitud=self.solicitud).count(),
            1
        )

    def test_crear_incidente_avisa_a_los_administradores(self):
        User.objects.create_user(
            username='qa_admin_correo',
            email='admin_correo@example.com',
            password='ClaveQaAdmin123!',
            is_staff=True,
            is_superuser=True
        )
        self.solicitud.estado = 'completada'
        self.solicitud.save(update_fields=['estado'])

        self.client.force_authenticate(user=self.usuario_cliente)
        with patch('servicios.views.enviar_correo') as enviar:
            with self.captureOnCommitCallbacks(execute=True):
                respuesta = self.client.post(
                    '/api/incidentes/',
                    {
                        'solicitud': self.solicitud.pk,
                        'tipo': 'danos_materiales',
                        'descripcion': 'Incidente de prueba QA',
                    },
                    format='json'
                )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        destinatarios = [
            llamada.kwargs['destinatario']
            for llamada in enviar.call_args_list
        ]
        self.assertIn('admin_correo@example.com', destinatarios)


class DatosDemoQATests(TestCase):

    def ejecutar_dry_run(self):
        salida = io.StringIO()
        call_command('poblar_datos_demo', '--dry-run', stdout=salida)
        return salida.getvalue()

    def contar(self):
        return {
            'usuarios': User.objects.count(),
            'categorias': Categoria.objects.count(),
            'servicios': Servicio.objects.count(),
            'ofertas': ServicioProfesional.objects.count(),
            'solicitudes': SolicitudServicio.objects.count(),
            'pagos': Pago.objects.count(),
        }

    def test_dry_run_no_guarda_nada(self):
        antes = self.contar()

        texto = self.ejecutar_dry_run()

        self.assertEqual(self.contar(), antes)
        self.assertIn('Simulación terminada', texto)

    def test_dry_run_informa_entre_100_y_150_registros(self):
        texto = self.ejecutar_dry_run()

        coincidencia = re.search(r'Total de registros nuevos:\s*(\d+)', texto)
        self.assertIsNotNone(coincidencia, texto)

        total = int(coincidencia.group(1))
        self.assertGreaterEqual(total, 100)
        self.assertLessEqual(total, 150)

    def test_no_hay_cambios_de_modelos_sin_migrar(self):
        try:
            call_command(
                'makemigrations', '--check', '--dry-run', verbosity=0
            )
        except SystemExit:
            self.fail('Hay cambios en los modelos que no tienen migración.')