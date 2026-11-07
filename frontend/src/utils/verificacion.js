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