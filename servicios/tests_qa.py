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