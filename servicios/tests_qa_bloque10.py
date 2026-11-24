from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from servicios.models import Categoria, Pago, Servicio, SolicitudServicio
from usuarios.models import DocumentoVerificacion


class ReglasNuevasMainQATests(APITestCase):
    """Reglas nuevas de main: facturas del profesional, cedula del cliente
    y aprobacion de profesionales (commits 1dd6075 y d7b11f7)."""

    CLAVE = 'ClaveQa10Segura!'

    def _usuario(self, nombre, rol, ident='pendiente',
                 verif='pendiente', disponible=False):
        usuario = User.objects.create_user(
            username=nombre, password=self.CLAVE
        )
        perfil = usuario.perfil
        perfil.rol = rol
        perfil.estado_identidad = ident
        perfil.estado_verificacion = verif
        perfil.disponible = disponible
        perfil.save(update_fields=[
            'rol', 'estado_identidad', 'estado_verificacion', 'disponible',
        ])
        return usuario, perfil

    def setUp(self):
        self.admin = User.objects.create_user(
            username='qa10_admin', password=self.CLAVE, is_staff=True
        )
        self.u_cliente, self.cliente = self._usuario(
            'qa10_cliente', 'cliente', disponible=True
        )
        self.u_prof, self.prof = self._usuario(
            'qa10_prof', 'profesional', 'aprobado', 'aprobado', True
        )
        self.u_otro, self.otro = self._usuario(
            'qa10_otro', 'profesional', 'aprobado', 'aprobado', True
        )
        categoria = Categoria.objects.create(
            nombre='Categoria QA10', descripcion='Pruebas QA'
        )
        servicio = Servicio.objects.create(
            categoria=categoria, nombre='Servicio QA10',
            descripcion='Pruebas QA', precio_base=Decimal('50000.00'),
        )
        solicitud = SolicitudServicio.objects.create(
            cliente=self.cliente, profesional=self.prof, servicio=servicio,
            descripcion='Trabajo QA10', direccion_servicio='Calle QA10',
            fecha_solicitada=timezone.now() + timedelta(days=2),
            estado='completada', precio_acordado=Decimal('100000.00'),
        )
        self.pago = Pago.objects.create(
            solicitud=solicitud, monto_total=Decimal('100000.00'),
            porcentaje_comision=Decimal('10.00'),
            monto_comision=Decimal('10000.00'),
            monto_profesional=Decimal('90000.00'),
            metodo='transferencia', estado='pendiente',
            referencia='REF-QA10', fecha_pago=timezone.now(),
        )
        self.url_factura = '/api/pagos/%s/factura/' % self.pago.pk

    # ---- Facturas del profesional ----
    def test_profesional_ajeno_no_descarga_la_factura(self):
        self.pago.estado = 'pagado'
        self.pago.save()
        self.client.force_authenticate(user=self.u_otro)
        r = self.client.get(self.url_factura)
        self.assertEqual(r.status_code, 403)

    def test_profesional_dueno_con_pago_pendiente_da_400(self):
        self.client.force_authenticate(user=self.u_prof)
        r = self.client.get(self.url_factura)
        self.assertEqual(r.status_code, 400)

    # ---- Cedula del cliente ----
    def _documento_cliente(self):
        return DocumentoVerificacion.objects.create(
            perfil=self.cliente, tipo='identidad', archivo='qa10_cliente.pdf'
        )

    def test_admin_aprueba_cedula_del_cliente_solo_cambia_identidad(self):
        doc = self._documento_cliente()
        self.client.force_authenticate(user=self.admin)
        r = self.client.patch(
            '/api/usuarios/admin/documentos/%s/' % doc.pk,
            {'estado': 'aprobado'}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado_identidad, 'aprobado')
        self.assertEqual(self.cliente.estado_verificacion, 'pendiente')
        self.assertTrue(self.cliente.disponible)

    def test_admin_rechaza_cedula_del_cliente_solo_cambia_identidad(self):
        doc = self._documento_cliente()
        self.client.force_authenticate(user=self.admin)
        r = self.client.patch(
            '/api/usuarios/admin/documentos/%s/' % doc.pk,
            {'estado': 'rechazado'}, format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado_identidad, 'rechazado')
        self.assertEqual(self.cliente.estado_verificacion, 'pendiente')
        self.assertTrue(self.cliente.disponible)

    # ---- Aprobar profesionales ----
    def _aprobar(self, perfil, estado):
        self.client.force_authenticate(user=self.admin)
        return self.client.patch(
            '/api/usuarios/admin/profesionales/%s/' % perfil.pk,
            {'estado_verificacion': estado}, format='json',
        )

    def test_aprobar_profesional_sin_cedula_aprobada_da_400(self):
        _, pend = self._usuario('qa10_pend1', 'profesional')
        r = self._aprobar(pend, 'aprobado')
        self.assertEqual(r.status_code, 400)
        pend.refresh_from_db()
        self.assertEqual(pend.estado_verificacion, 'pendiente')
        self.assertFalse(pend.disponible)

    def test_aprobar_profesional_con_cedula_aprobada_lo_deja_disponible(self):
        _, pend = self._usuario(
            'qa10_pend2', 'profesional', ident='aprobado'
        )
        r = self._aprobar(pend, 'aprobado')
        self.assertEqual(r.status_code, 200)
        pend.refresh_from_db()
        self.assertEqual(pend.estado_verificacion, 'aprobado')
        self.assertTrue(pend.disponible)

    def test_rechazar_profesional_sin_cedula_aprobada_si_se_permite(self):
        _, pend = self._usuario('qa10_pend3', 'profesional')
        r = self._aprobar(pend, 'rechazado')
        self.assertEqual(r.status_code, 200)
        pend.refresh_from_db()
        self.assertEqual(pend.estado_verificacion, 'rechazado')
        self.assertFalse(pend.disponible)