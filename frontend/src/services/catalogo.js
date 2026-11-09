import { enviar, peticionAutenticada } from './api.js';

// ----- Públicos (no requieren sesión) -----
export function listarCategorias() {
  return enviar('/categorias/');
}

export function listarServicios() {
  return enviar('/servicios/');
}

export function listarOfertas() {
  return enviar('/ofertas/');
}

export function obtenerReputacion(perfilId) {
  return enviar(`/profesionales/${perfilId}/reputacion/`);
}

export function listarResenasProfesional(perfilId) {
  return enviar(`/profesionales/${perfilId}/resenas/`);
}

// ----- Solicitudes (con sesión) -----
export function listarSolicitudes() {
  return peticionAutenticada('/solicitudes/');
}

export function crearSolicitud(datos) {
  return peticionAutenticada('/solicitudes/', {
    metodo: 'POST',
    cuerpo: datos,
  });
}

// "codigo" solo se envía al iniciar o completar el servicio (lo escribe el profesional).
export function cambiarEstadoSolicitud(id, estado, codigo) {
  const cuerpo = codigo === undefined ? { estado } : { estado, codigo };

  return peticionAutenticada(`/solicitudes/${id}/estado/`, {
    metodo: 'PATCH',
    cuerpo,
  });
}

// ----- Negociación de precios (con sesión) -----
export function listarPropuestas(solicitudId) {
  return peticionAutenticada(`/solicitudes/${solicitudId}/propuestas/`);
}

export function crearPropuesta(solicitudId, precio) {
  return peticionAutenticada(`/solicitudes/${solicitudId}/propuestas/`, {
    metodo: 'POST',
    cuerpo: { precio },
  });
}

export function responderPropuesta(solicitudId, propuestaId, accion) {
  return peticionAutenticada(
    `/solicitudes/${solicitudId}/propuestas/${propuestaId}/`,
    {
      metodo: 'PATCH',
      cuerpo: { accion },
    },
  );
}

// ----- Reseñas (con sesión) -----
export function crearResena(solicitudId, calificacion, comentario) {
  return peticionAutenticada(`/solicitudes/${solicitudId}/resena/`, {
    metodo: 'POST',
    cuerpo: { calificacion, comentario },
  });
}

// ----- Pagos (con sesión) -----
export function listarMisPagos() {
  return peticionAutenticada('/mis-pagos/');
}

export function crearPago(solicitudId, metodo) {
  return peticionAutenticada(`/solicitudes/${solicitudId}/pago/`, {
    metodo: 'POST',
    cuerpo: { metodo },
  });
}

// ----- Incidentes (con sesión) -----
export function crearIncidente(datos) {
  return peticionAutenticada('/incidentes/', {
    metodo: 'POST',
    cuerpo: datos,
  });
}