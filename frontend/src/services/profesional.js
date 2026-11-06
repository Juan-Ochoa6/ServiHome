import { enviar, peticionAutenticada } from './api.js';

// ----- Mis servicios (ofertas del profesional) -----
export function listarMisOfertas() {
  return peticionAutenticada('/mis-ofertas/');
}

export function crearOferta(servicio, precio) {
  return peticionAutenticada('/mis-ofertas/', {
    metodo: 'POST',
    cuerpo: { servicio, precio },
  });
}

export function actualizarOferta(id, datos) {
  return peticionAutenticada(`/mis-ofertas/${id}/`, {
    metodo: 'PATCH',
    cuerpo: datos,
  });
}

export function eliminarOferta(id) {
  return peticionAutenticada(`/mis-ofertas/${id}/`, { metodo: 'DELETE' });
}

// ----- Portafolio (los envíos llevan imagen, por eso usan FormData) -----
export function listarMiPortafolio() {
  return peticionAutenticada('/mi-portafolio/');
}

export function crearTrabajo(formulario) {
  return peticionAutenticada('/mi-portafolio/', {
    metodo: 'POST',
    cuerpo: formulario,
  });
}

export function actualizarTrabajo(id, formulario) {
  return peticionAutenticada(`/mi-portafolio/${id}/`, {
    metodo: 'PATCH',
    cuerpo: formulario,
  });
}

export function eliminarTrabajo(id) {
  return peticionAutenticada(`/mi-portafolio/${id}/`, { metodo: 'DELETE' });
}

// Portafolio público de un profesional (no requiere sesión)
export function listarPortafolioPublico(perfilId) {
  return enviar(`/profesionales/${perfilId}/portafolio/`);
}