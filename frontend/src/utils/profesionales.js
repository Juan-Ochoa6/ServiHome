// Agrupa las ofertas (profesional + servicio) por profesional.
export function agruparPorProfesional(ofertas) {
  const mapa = new Map();

  for (const oferta of ofertas) {
    if (!mapa.has(oferta.profesional)) {
      mapa.set(oferta.profesional, {
        id: oferta.profesional,
        nombre: oferta.profesional_nombre,
        descripcion: oferta.descripcion_profesional,
        experiencia: oferta.experiencia_anos,
        ofertas: [],
      });
    }
    mapa.get(oferta.profesional).ofertas.push(oferta);
  }

  return [...mapa.values()];
}

export function categoriasDe(profesional) {
  return [...new Set(profesional.ofertas.map((oferta) => oferta.categoria_nombre))];
}