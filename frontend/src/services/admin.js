import { peticionAutenticada } from './api.js';

// Profesionales por verificar
export function listarProfesionalesPendientes() {
  return peticionAutenticada('/usuarios/admin/profesionales/');
}

export function cambiarEstadoProfesional(id, estado) {
  return peticionAutenticada(`/usuarios/admin/profesionales/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado_verificacion: estado },
  });
}

// Ofertas por aprobar
export function listarOfertasPendientes() {
  return peticionAutenticada('/admin/ofertas/');
}

export function cambiarEstadoOferta(id, estado) {
  return peticionAutenticada(`/admin/ofertas/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado_aprobacion: estado },
  });
}