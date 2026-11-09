const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';
const CLAVE_SESION = 'servihome.sesion';

export const EVENTO_SESION_EXPIRADA = 'servihome:sesion-expirada';

// ---------- Sesión guardada en el navegador ----------

export function leerSesion() {
  try {
    const texto = localStorage.getItem(CLAVE_SESION);
    return texto ? JSON.parse(texto) : null;
  } catch {
    return null;
  }
}

export function guardarSesion(sesion) {
  try {
    localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
  } catch {
    // Sin almacenamiento disponible: la sesión solo vive en memoria.
  }
}

export function borrarSesion() {
  try {
    localStorage.removeItem(CLAVE_SESION);
  } catch {
    // Nada que borrar.
  }
}

// ---------- Errores ----------

export class ErrorApi extends Error {
  constructor(status, datos, mensaje) {
    super(mensaje);
    this.name = 'ErrorApi';
    this.status = status;
    this.datos = datos;
  }
}

// Mensajes en inglés que devuelve Django REST Framework por defecto.
const TRADUCCIONES = {
  'Authentication credentials were not provided.': 'Debes iniciar sesión para continuar.',
  'You do not have permission to perform this action.':
    'No tienes permiso para realizar esta acción.',
  'Not found.': 'No encontramos lo que buscas.',
  'Invalid token.': 'Tu sesión no es válida. Inicia sesión de nuevo.',
  'Given token not valid for any token type': 'Tu sesión expiró. Inicia sesión de nuevo.',
  'Token is invalid or expired': 'Tu sesión expiró. Inicia sesión de nuevo.',
  'Method "GET" not allowed.': 'Esta acción no está disponible.',
};

function traducir(texto) {
  return TRADUCCIONES[texto] ?? texto;
}

function mensajeDeError(status, datos) {
  if (datos && typeof datos === 'object') {
    if (typeof datos.error === 'string') return traducir(datos.error);
    if (typeof datos.detail === 'string') return traducir(datos.detail);

    const primero = Object.values(datos)[0];
    const texto = Array.isArray(primero) ? primero[0] : primero;
    if (typeof texto === 'string') return traducir(texto);
  }

  if (status === 0) {
    return 'No se pudo conectar con el servidor. Revisa tu conexión o que el backend esté encendido.';
  }
  if (status === 401) return 'Tu sesión expiró o no estás autenticado. Inicia sesión de nuevo.';
  if (status === 403) return 'No tienes permiso para realizar esta acción.';
  if (status === 404) return 'No encontramos lo que buscas.';
  if (status === 429) {
    return 'Hiciste demasiados intentos seguidos. Espera un momento e inténtalo de nuevo.';
  }
  if (status >= 500) return 'El servidor tuvo un problema. Inténtalo de nuevo en unos minutos.';
  return 'Ocurrió un error inesperado.';
}

// ---------- Peticiones ----------

export async function enviar(ruta, { metodo = 'GET', cuerpo, token } = {}) {
  const encabezados = { Accept: 'application/json' };
  const esFormulario = typeof FormData !== 'undefined' && cuerpo instanceof FormData;

  // Con FormData, el navegador pone solo el Content-Type (con su "boundary").
  if (cuerpo !== undefined && !esFormulario) {
    encabezados['Content-Type'] = 'application/json';
  }
  if (token) encabezados.Authorization = `Bearer ${token}`;

  let cuerpoEnviado;
  if (cuerpo !== undefined) {
    cuerpoEnviado = esFormulario ? cuerpo : JSON.stringify(cuerpo);
  }

  let respuesta;
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, {
      method: metodo,
      headers: encabezados,
      body: cuerpoEnviado,
    });
  } catch {
    throw new ErrorApi(0, null, mensajeDeError(0, null));
  }

  let datos = null;
  try {
    datos = await respuesta.json();
  } catch {
    // La respuesta no trae cuerpo JSON (por ejemplo, un DELETE devuelve 204).
  }

  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, datos, mensajeDeError(respuesta.status, datos));
  }
  return datos;
}

let renovando = null;

async function renovarAcceso() {
  const sesion = leerSesion();
  if (!sesion?.refresh) {
    throw new ErrorApi(401, null, 'Tu sesión expiró. Inicia sesión de nuevo.');
  }

  if (!renovando) {
    renovando = enviar('/usuarios/token/refresh/', {
      metodo: 'POST',
      cuerpo: { refresh: sesion.refresh },
    })
      .then((datos) => {
        guardarSesion({
          ...sesion,
          access: datos.access,
          ...(datos.refresh ? { refresh: datos.refresh } : {}),
        });
        return datos.access;
      })
      .finally(() => {
        renovando = null;
      });
  }
  return renovando;
}

// Petición con token. Si el access venció, lo renueva y reintenta una vez.
export async function peticionAutenticada(ruta, opciones = {}) {
  const sesion = leerSesion();
  if (!sesion?.access) {
    throw new ErrorApi(401, null, 'Debes iniciar sesión.');
  }

  try {
    return await enviar(ruta, { ...opciones, token: sesion.access });
  } catch (error) {
    if (!(error instanceof ErrorApi) || error.status !== 401) throw error;

    try {
      const nuevoAcceso = await renovarAcceso();
      return await enviar(ruta, { ...opciones, token: nuevoAcceso });
    } catch (segundoError) {
      if (segundoError instanceof ErrorApi && segundoError.status === 401) {
        borrarSesion();
        window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA));
      }
      throw segundoError;
    }
  }
}

// ---------- Autenticación ----------

export function iniciarSesion(username, password) {
  return enviar('/usuarios/login/', {
    metodo: 'POST',
    cuerpo: { username, password },
  });
}

export function verificarCodigoLogin(challenge, codigo) {
  return enviar('/usuarios/login/mfa/', {
    metodo: 'POST',
    cuerpo: { challenge, codigo },
  });
}

export function registrarUsuario(datos) {
  return enviar('/usuarios/registro/', {
    metodo: 'POST',
    cuerpo: datos,
  });
}

// ---------- Archivos protegidos ----------

// Pide un archivo que exige sesión y lo devuelve como Blob.
// "ruta" es la que entrega el backend, por ejemplo /api/usuarios/documentos/4/descargar/
async function pedirArchivo(ruta, token) {
  const origen = new URL(API_URL, window.location.origin).origin;

  let respuesta;
  try {
    respuesta = await fetch(`${origen}${ruta}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ErrorApi(0, null, mensajeDeError(0, null));
  }

  if (!respuesta.ok) {
    let datos = null;
    try {
      datos = await respuesta.json();
    } catch {
      // La respuesta no trae cuerpo JSON.
    }
    throw new ErrorApi(respuesta.status, datos, mensajeDeError(respuesta.status, datos));
  }

  return respuesta.blob();
}

export async function descargarArchivoProtegido(ruta) {
  const sesion = leerSesion();
  if (!sesion?.access) {
    throw new ErrorApi(401, null, 'Debes iniciar sesión.');
  }

  try {
    return await pedirArchivo(ruta, sesion.access);
  } catch (error) {
    if (!(error instanceof ErrorApi) || error.status !== 401) throw error;

    try {
      const nuevoAcceso = await renovarAcceso();
      return await pedirArchivo(ruta, nuevoAcceso);
    } catch (segundoError) {
      if (segundoError instanceof ErrorApi && segundoError.status === 401) {
        borrarSesion();
        window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA));
      }
      throw segundoError;
    }
  }
}

// Reconoce el tipo real del archivo por sus primeros bytes. Solo se muestran
// en pantalla PDF, PNG y JPG; cualquier otra cosa se descarga.
async function conTipoReal(blob) {
  const inicio = new Uint8Array(await blob.slice(0, 8).arrayBuffer());
  let tipo = '';

  if (inicio[0] === 0x25 && inicio[1] === 0x50 && inicio[2] === 0x44 && inicio[3] === 0x46) {
    tipo = 'application/pdf';
  } else if (inicio[0] === 0x89 && inicio[1] === 0x50 && inicio[2] === 0x4e && inicio[3] === 0x47) {
    tipo = 'image/png';
  } else if (inicio[0] === 0xff && inicio[1] === 0xd8 && inicio[2] === 0xff) {
    tipo = 'image/jpeg';
  }

  return {
    blob: tipo ? new Blob([blob], { type: tipo }) : blob,
    visualizable: Boolean(tipo),
  };
}

// Abre un archivo protegido en una pestaña nueva.
export async function abrirArchivoProtegido(ruta) {
  // La pestaña se abre en el mismo clic, antes de esperar la descarga,
  // para que el navegador no la bloquee como ventana emergente.
  const ventana = window.open('', '_blank');

  try {
    const original = await descargarArchivoProtegido(ruta);
    const { blob, visualizable } = await conTipoReal(original);
    const url = URL.createObjectURL(blob);

    if (ventana && visualizable) {
      ventana.location.href = url;
    } else {
      if (ventana) ventana.close();
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = 'documento';
      enlace.click();
    }

    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) {
    if (ventana) ventana.close();
    throw error;
  }
}