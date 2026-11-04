import { enviar, peticionAutenticada } from './api.js';

// Públicos (no requieren sesión)
export function listarCategorias() {
  return enviar('/categorias/');
}

export function listarServicios() {
  return enviar('/servicios/');
}

export function listarOfertas() {
  return enviar('/ofertas/');
}

// Solicitudes (con sesión)
export function listarSolicitudes() {
  return peticionAutenticada('/solicitudes/');
}

export function crearSolicitud(datos) {
  return peticionAutenticada('/solicitudes/', {
    metodo: 'POST',
    cuerpo: datos,
  });
}

export function cambiarEstadoSolicitud(id, estado) {
  return peticionAutenticada(`/solicitudes/${id}/estado/`, {
    metodo: 'PATCH',
    cuerpo: { estado },
  });
}

// Negociación de precios (con sesión)
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