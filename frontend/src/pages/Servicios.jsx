import { useNavigate } from 'react-router-dom';
import { categorias } from '../data/datos.js';

function Servicios() {
  const navigate = useNavigate();

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">NUESTROS SERVICIOS</span>
        <h2>¿Qué necesitas para tu hogar?</h2>
        <p>Explora algunas de nuestras categorías.</p>
      </div>

      <div className="categorias-grid">
        {categorias.map((categoria) => (
          <button
            type="button"
            className="categoria"
            key={categoria.nombre}
            onClick={() =>
              navigate(`/profesionales?buscar=${encodeURIComponent(categoria.nombre)}`)
            }
          >
            <span className="categoria-icono">{categoria.icono}</span>
            <span>{categoria.nombre}</span>
            <span className="flecha" aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </section>
  );
}

export default Servicios;