export const TIPOS_DOCUMENTO = {
  identidad: 'Documento de identidad',
  experiencia: 'Certificado de experiencia',
  acreditacion: 'Certificación o acreditación',
};

export const ETIQUETAS_DOCUMENTO = {
  pendiente: 'Pendiente',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};

export const ETIQUETAS_VERIFICACION = {
  no_aplica: 'No aplica',
  pendiente: 'Pendiente de revisión',
  en_revision: 'En revisión',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};

export function etiquetaVerificacion(estado) {
  return ETIQUETAS_VERIFICACION[estado] ?? estado;
}

// Ruta del backend para descargar un documento protegido.
// Si la respuesta no trae url_descarga, se arma con el id del documento.
export function rutaDescarga(documento) {
  return documento.url_descarga ?? `/api/usuarios/documentos/${documento.id}/descargar/`;
}