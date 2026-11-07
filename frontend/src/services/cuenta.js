import { peticionAutenticada } from './api.js';

export function obtenerPerfil() {
  return peticionAutenticada('/usuarios/perfil/');
}

export function actualizarPerfil(datos) {
  return peticionAutenticada('/usuarios/perfil/', {
    metodo: 'PATCH',
    cuerpo: datos,
  });
}

export function obtenerMiVerificacion() {
  return peticionAutenticada('/usuarios/mi-verificacion/');
}

export function cambiarDisponibilidad(disponible) {
  return peticionAutenticada('/usuarios/disponibilidad/', {
    metodo: 'PATCH',
    cuerpo: { disponible },
  });
}

// El formulario lleva el archivo, por eso se envía como FormData.
export function subirDocumento(formulario) {
  return peticionAutenticada('/usuarios/mis-documentos/', {
    metodo: 'POST',
    cuerpo: formulario,
  });
}