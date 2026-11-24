

# ============================================================
# BLOQUE 9: casos de uso parciales (API) + H-3 + correo duplicado
# ============================================================
import os
from datetime import timedelta
from unittest.mock import patch as _patch

from django.contrib.auth.models import User as _User
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone as _tz
from rest_framework.test import APITestCase as _APITestCase

from servicios.models import (
    Categoria as _Categoria,
    Servicio as _Servicio,
    ServicioProfesional as _ServicioProfesional,
    SolicitudServicio as _SolicitudServicio,
)
from usuarios.security import get_fernet as _get_fernet


class CoberturaCasosUsoQATests(_APITestCase):
    """Cubre CU-04, 05, 06, 09, 13, 27, 41, H-3 y el correo duplicado."""

    def _usuario(self, nombre, rol, aprobado=False, disponible=True, email=''):
        u = _User.objects.create_user(
            username=nombre, password='ClaveSegura123!', email=email
        )
        p = u.perfil  # la señal crea el Perfil automáticamente
        p.rol = rol
        if rol == 'profesional':
            p.estado_verificacion = 'aprobado' if aprobado else 'pendiente'
            p.estado_identidad = 'aprobado' if aprobado else 'pendiente'
        p.disponible = disponible
        p.save()
        return u, p

    def setUp(self):
        self.cat_activa = _Categoria.objects.create(nombre='CatActiva9')
        self.cat_inactiva = _Categoria.objects.create(
            nombre='CatInactiva9', activa=False
        )
        self.srv_activo = _Servicio.objects.create(
            categoria=self.cat_activa, nombre='SrvActivo9',
            descripcion='d', precio_base=50000,
        )
        self.srv_inactivo = _Servicio.objects.create(
            categoria=self.cat_activa, nombre='SrvInactivo9',
            descripcion='d', precio_base=50000, activo=False,
        )
        self.u_cli1, self.cli1 = self._usuario('qa9_cli1', 'cliente', email='qa9cli1@x.com')
        self.u_cli2, self.cli2 = self._usuario('qa9_cli2', 'cliente', email='qa9cli2@x.com')
        self.u_pro, self.pro = self._usuario('qa9_pro', 'profesional', aprobado=True)
        self.u_pro2, self.pro2 = self._usuario('qa9_pro2', 'profesional', aprobado=True)
        self.u_pend, self.pend = self._usuario('qa9_pend', 'profesional', aprobado=False)
        self.u_admin = _User.objects.create_user(
            username='qa9_admin', password='ClaveSegura123!', is_staff=True
        )

    def _solicitud(self, cliente, profesional):
        return _SolicitudServicio.objects.create(
            cliente=cliente, profesional=profesional,
            servicio=self.srv_activo, descripcion='trabajo',
            direccion_servicio='Calle 1',
            fecha_solicitada=_tz.now() + timedelta(days=2),
        )

    # ---- CU-04, 05, 06: catálogo público ----
    def test_categorias_publicas_solo_activas_sin_sesion(self):
        r = self.client.get('/api/categorias/')
        self.assertEqual(r.status_code, 200)
        nombres = [c['nombre'] for c in r.json()]
        self.assertIn('CatActiva9', nombres)
        self.assertNotIn('CatInactiva9', nombres)

    def test_servicios_publicos_solo_activos_con_categoria(self):
        r = self.client.get('/api/servicios/')
        self.assertEqual(r.status_code, 200)
        datos = {s['nombre']: s for s in r.json()}
        self.assertIn('SrvActivo9', datos)
        self.assertNotIn('SrvInactivo9', datos)
        self.assertEqual(datos['SrvActivo9']['categoria_nombre'], 'CatActiva9')

    # ---- CU-09: ofertas públicas ----
    def test_ofertas_publicas_solo_aprobadas_de_profesionales_habilitados(self):
        visible = _ServicioProfesional.objects.create(
            servicio=self.srv_activo, profesional=self.pro,
            precio=60000, estado_aprobacion='aprobado',
        )
        _ServicioProfesional.objects.create(
            servicio=self.srv_activo, profesional=self.pro2,
            precio=60000, estado_aprobacion='pendiente',
        )
        self.pend.estado_identidad = 'aprobado'
        self.pend.save()
        _ServicioProfesional.objects.create(
            servicio=self.srv_activo, profesional=self.pend,
            precio=60000, estado_aprobacion='aprobado',
        )
        r = self.client.get('/api/ofertas/')
        self.assertEqual(r.status_code, 200)
        ids = [o['id'] for o in r.json()]
        self.assertEqual(ids, [visible.id])

    def test_ofertas_publicas_ocultan_profesional_no_disponible(self):
        _ServicioProfesional.objects.create(
            servicio=self.srv_activo, profesional=self.pro,
            precio=60000, estado_aprobacion='aprobado',
        )
        self.pro.disponible = False
        self.pro.save()
        r = self.client.get('/api/ofertas/')
        self.assertEqual(r.json(), [])

    # ---- CU-13 y CU-27: solicitudes propias y asignadas ----
    def test_cliente_ve_solo_sus_solicitudes(self):
        propia = self._solicitud(self.cli1, self.pro)
        self._solicitud(self.cli2, self.pro)
        self.client.force_authenticate(self.u_cli1)
        r = self.client.get('/api/solicitudes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s['id'] for s in r.json()], [propia.id])

    def test_profesional_ve_solo_solicitudes_asignadas(self):
        asignada = self._solicitud(self.cli1, self.pro)
        self._solicitud(self.cli1, self.pro2)
        self.client.force_authenticate(self.u_pro)
        r = self.client.get('/api/solicitudes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s['id'] for s in r.json()], [asignada.id])

    def test_solicitudes_sin_sesion_da_401(self):
        r = self.client.get('/api/solicitudes/')
        self.assertEqual(r.status_code, 401)

    def test_profesional_pendiente_no_puede_listar_solicitudes(self):
        self.client.force_authenticate(self.u_pend)
        r = self.client.get('/api/solicitudes/')
        self.assertEqual(r.status_code, 403)

    # ---- CU-41: profesionales pendientes (admin) ----
    def test_admin_lista_profesionales_pendientes(self):
        self.client.force_authenticate(self.u_admin)
        r = self.client.get('/api/usuarios/admin/profesionales/')
        self.assertEqual(r.status_code, 200)
        nombres = [p['username'] for p in r.json()]
        self.assertIn('qa9_pend', nombres)
        self.assertNotIn('qa9_pro', nombres)

    def test_cliente_no_puede_listar_profesionales_pendientes(self):
        self.client.force_authenticate(self.u_cli1)
        r = self.client.get('/api/usuarios/admin/profesionales/')
        self.assertEqual(r.status_code, 403)

    # ---- H-3: FERNET_KEY ----
    def test_sin_fernet_key_se_lanza_error_de_configuracion(self):
        with _patch.dict(os.environ, {}, clear=False):
            os.environ.pop('FERNET_KEY', None)
            with self.assertRaises(ImproperlyConfigured):
                _get_fernet()

    def test_fernet_key_de_ejemplo_se_rechaza(self):
        with _patch.dict(os.environ, {'FERNET_KEY': 'TU_CLAVE_GENERADA'}):
            with self.assertRaises(ImproperlyConfigured):
                _get_fernet()

    # ---- Correo duplicado en el perfil (era el candidato H-32) ----
    def test_perfil_correo_duplicado_se_rechaza(self):
        """Antes el PATCH aceptaba un correo ya usado por otro usuario.
        Hoy el sistema lo rechaza con 400 y no guarda el cambio."""
        self.client.force_authenticate(self.u_cli1)
        r = self.client.patch(
            '/api/usuarios/perfil/', {'email': 'qa9cli2@x.com'}, format='json'
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(_User.objects.filter(email='qa9cli2@x.com').count(), 1)
