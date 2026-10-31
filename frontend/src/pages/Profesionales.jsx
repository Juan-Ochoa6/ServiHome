import { Link, useSearchParams } from 'react-router-dom';
import { profesionales } from '../data/datos.js';

function Profesionales() {
  const [params, setParams] = useSearchParams();
  const busqueda = params.get('buscar') ?? '';

  function cambiarBusqueda(valor) {
    setParams(valor ? { buscar: valor } : {}, { replace: true });
  }

  const termino = busqueda.trim().toLowerCase();
  const profesionalesFiltrados = profesionales.filter(
    (profesional) =>
      profesional.oficio.toLowerCase().includes(termino) ||
      profesional.nombre.toLowerCase().includes(termino),
  );

  return (
    <section className="seccion profesionales">
      <div className="encabezado-seccion">
        <span className="etiqueta">PERSONAS QUE TE AYUDAN</span>
        <h2>{busqueda ? `Resultados para "${busqueda}"` : 'Profesionales destacados'}</h2>
        <p>Conoce algunas de las personas que pueden ayudarte.</p>

        <div className="buscador buscador-pagina">
          <span aria-hidden="true">🔎</span>
          <input
            type="search"
            placeholder="Busca por oficio o nombre"
            aria-label="Buscar profesionales por oficio o nombre"
            value={busqueda}
            onChange={(evento) => cambiarBusqueda(evento.target.value)}
          />
        </div>
      </div>

      <div className="profesionales-grid">
        {profesionalesFiltrados.map((profesional) => (
          <article className="tarjeta-profesional" key={profesional.id}>
            <div className="profesional-avatar">{profesional.icono}</div>
            <div className="profesional-info">
              <span className="oficio">{profesional.oficio}</span>
              <h3>{profesional.nombre}</h3>
              <p>{profesional.descripcion}</p>
              <div className="calificacion">⭐ {profesional.calificacion}</div>
              <Link className="boton-contactar" to={`/profesionales/${profesional.id}`}>
                Ver profesional
              </Link>
            </div>
          </article>
        ))}

        {profesionalesFiltrados.length === 0 && (
          <p className="sin-resultados">
            No encontramos profesionales con ese nombre u oficio. Prueba con otra búsqueda.
          </p>
        )}
      </div>
    </section>
  );
}

export default Profesionales;