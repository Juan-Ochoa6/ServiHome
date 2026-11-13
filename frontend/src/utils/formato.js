export function normalizar(texto = '') {
  return String(texto)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

export function formatearPrecio(valor) {
  const numero = Number(valor);
  if (Number.isNaN(numero)) return '';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(numero);
}

export function formatearFecha(iso) {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return '';
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(fecha);
}

// Etiqueta de un período de finanzas a partir de su fecha de inicio (AAAA-MM-DD).
export function formatearPeriodo(iso, periodo) {
  const [anio, mes, dia] = String(iso).slice(0, 10).split('-').map(Number);
  if (!anio || !mes || !dia) return String(iso);

  // Se arma con partes locales para que la zona horaria no mueva el día.
  const fecha = new Date(anio, mes - 1, dia);

  if (periodo === 'ano') return String(anio);
  if (periodo === 'mes') {
    return new Intl.DateTimeFormat('es-CO', { month: 'long', year: 'numeric' }).format(fecha);
  }
  if (periodo === 'semana') {
    const inicio = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' }).format(fecha);
    return `Semana del ${inicio}`;
  }
  return new Intl.DateTimeFormat('es-CO', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(fecha);
}