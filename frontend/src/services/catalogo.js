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

// Con sesión
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