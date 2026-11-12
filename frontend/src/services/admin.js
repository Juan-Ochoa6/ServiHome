import { peticionAutenticada } from './api.js';

// ----- Profesionales por verificar -----
export function listarProfesionalesPendientes() {
  return peticionAutenticada('/usuarios/admin/profesionales/');
}

export function cambiarEstadoProfesional(id, estado) {
  return peticionAutenticada(`/usuarios/admin/profesionales/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado_verificacion: estado },
  });
}

// ----- Documentos de verificación (estado: pendiente | aprobado | rechazado | vacío = todos) -----
export function listarDocumentosAdmin(estado) {
  const consulta = estado ? `?estado=${encodeURIComponent(estado)}` : '';
  return peticionAutenticada(`/usuarios/admin/documentos/${consulta}`);
}

export function cambiarEstadoDocumento(id, estado, observacion) {
  return peticionAutenticada(`/usuarios/admin/documentos/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado, observacion },
  });
}

// ----- Ofertas por aprobar -----
export function listarOfertasPendientes() {
  return peticionAutenticada('/admin/ofertas/');
}

export function cambiarEstadoOferta(id, estado) {
  return peticionAutenticada(`/admin/ofertas/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado_aprobacion: estado },
  });
}

// ----- Pagos (el backend devuelve todos al administrador) -----
export function listarPagosAdmin() {
  return peticionAutenticada('/mis-pagos/');
}

// estado: pagado | fallido | reembolsado
export function cambiarEstadoPago(id, estado) {
  return peticionAutenticada(`/pagos/${id}/estado/`, {
    metodo: 'PATCH',
    cuerpo: { estado },
  });
}

// ----- Incidentes -----
export function listarIncidentes() {
  return peticionAutenticada('/admin/incidentes/');
}

export function actualizarIncidente(id, estado, respuesta) {
  return peticionAutenticada(`/admin/incidentes/${id}/`, {
    metodo: 'PATCH',
    cuerpo: { estado, respuesta_administrador: respuesta },
  });
}

// ----- Finanzas (periodo: dia | semana | mes | ano) -----
export function obtenerFinanzas(periodo) {
  return peticionAutenticada(`/admin/finanzas/?periodo=${encodeURIComponent(periodo)}`);
}