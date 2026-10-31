import { Link, useSearchParams } from 'react-router-dom';
import { listarOfertas } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { normalizar } from '../utils/formato.js';
import { agruparPorProfesional, categoriasDe } from '../utils/profesionales.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import IconoCategoria from '../components/IconoCategoria.jsx';

function Profesionales() {
  const [params, setParams] = useSearchParams();
  const { datos, cargando, error, recargar } = useCargar(listarOfertas);

  const busqueda = params.get('buscar') ?? '';
  const categoria = params.get('categoria');
  const servicio = params.get('servicio');
  const hayFiltros = Boolean(categoria || servicio);

  function cambiarBusqueda(valor) {
    const nuevos = new URLSearchParams(params);
    if (valor) nuevos.set('buscar', valor);
    else nuevos.delete('buscar');
    setParams(nuevos, { replace: true });
  }

  function quitarFiltros() {
    const nuevos = new URLSearchParams(params);
    nuevos.delete('categoria');
    nuevos.delete('servicio');
    setParams(nuevos);
  }

  const termino = normalizar(busqueda.trim());

  const ofertasFiltradas = (datos ?? []).filter((oferta) => {
    if (categoria && String(oferta.categoria) !== categoria) return false;
    if (servicio && String(oferta.servicio) !== servicio) return false;
    if (!termino) return true;

    return [oferta.profesional_nombre, oferta.servicio_nombre, oferta.categoria_nombre].some(
      (texto) => normalizar(texto).includes(termino),
    );
  });

  const lista = agruparPorProfesional(ofertasFiltradas);

  return (
    <section className="seccion profesionales">
      <div className="encabezado-seccion">
        <span className="etiqueta">PERSONAS QUE TE AYUDAN</span>
        <h2>{busqueda ? `Resultados para "${busqueda}"` : 'Profesionales disponibles'}</h2>
        <p>Conoce a las personas que pueden ayudarte.</p>

        <div className="buscador buscador-pagina">
          <span aria-hidden="true">🔎</span>
          <input
            type="search"
            placeholder="Busca por oficio, servicio o nombre"
            aria-label="Buscar profesionales por oficio, servicio o nombre"
            value={busqueda}
            onChange={(evento) => cambiarBusqueda(evento.target.value)}
          />
        </div>

        {hayFiltros && (
          <div className="filtros-activos">
            <button type="button" className="boton-secundario" onClick={quitarFiltros}>
              Quitar filtros ✕
            </button>
          </div>
        )}
      </div>

      <EstadoCarga
        cargando={cargando}
        error={error}
        onReintentar={recargar}
        texto="Cargando profesionales…"
      />

      {!cargando && !error && (
        <div className="profesionales-grid">
          {lista.map((profesional) => {
            const categorias = categoriasDe(profesional);

            return (
              <article className="tarjeta-profesional" key={profesional.id}>
                <div className="profesional-avatar">
                  <IconoCategoria nombre={categorias[0]} />
                </div>
                <div className="profesional-info">
                  <span className="oficio">{categorias.join(' · ')}</span>
                  <h3>{profesional.nombre}</h3>
                  <p>
                    {profesional.descripcion ||
                      'Este profesional aún no ha agregado una descripción.'}
                  </p>
                  {profesional.experiencia > 0 && (
                    <div className="calificacion">
                      {profesional.experiencia}{' '}
                      {profesional.experiencia === 1 ? 'año' : 'años'} de experiencia
                    </div>
                  )}
                  <Link className="boton-contactar" to={`/profesionales/${profesional.id}`}>
                    Ver profesional
                  </Link>
                </div>
              </article>
            );
          })}

          {lista.length === 0 && (
            <p className="sin-resultados">
              No encontramos profesionales con esos criterios. Prueba con otra búsqueda.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export default Profesionales;