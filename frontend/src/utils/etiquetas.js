export const METODOS_PAGO = {
  efectivo: 'Efectivo',
  transferencia: 'Transferencia',
  tarjeta: 'Tarjeta',
  pasarela: 'Pasarela de pago',
};

export const ETIQUETAS_PAGO = {
  pendiente: 'Pendiente',
  pagado: 'Pagado',
  fallido: 'Fallido',
  reembolsado: 'Reembolsado',
};

// Reutiliza los colores de los estados de solicitud.
export const CLASE_ESTADO_PAGO = {
  pendiente: '',
  pagado: 'estado-completada',
  fallido: 'estado-rechazada',
  reembolsado: 'estado-en_proceso',
};

export const TIPOS_INCIDENTE = {
  danos_materiales: 'Daños materiales',
  incumplimiento: 'Incumplimiento del servicio',
  comportamiento: 'Comportamiento inadecuado',
  cobro_indebido: 'Cobro indebido',
  emergencia: 'Emergencia',
  otro: 'Otro',
};

export const ETIQUETAS_INCIDENTE = {
  pendiente: 'Pendiente',
  en_revision: 'En revisión',
  resuelto: 'Resuelto',
  rechazado: 'Rechazado',
};