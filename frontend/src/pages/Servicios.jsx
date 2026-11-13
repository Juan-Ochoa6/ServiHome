import { Link, useNavigate } from 'react-router-dom';
import { listarCategorias, listarServicios } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPrecio } from '../utils/formato.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import IconoCategoria from '../components/IconoCategoria.jsx';

function Servicios() {
  const navigate = useNavigate();
  const categorias = useCargar(listarCategorias);
  const servicios = useCargar(listarServicios);

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">NUESTROS SERVICIOS</span>
        <h2>¿Qué necesitas para tu hogar?</h2>
        <p>Explora nuestras categorías.</p>
      </div>

      <EstadoCarga
        cargando={categorias.cargando}
        error={categorias.error}
        onReintentar={categorias.recargar}
        texto="Cargando categorías…"
      />

      {!categorias.cargando && !categorias.error && categorias.datos && (
        categorias.datos.length === 0 ? (
          <p className="sin-resultados">Todavía no hay categorías disponibles.</p>
        ) : (
          <div className="categorias-grid">
            {categorias.datos.map((categoria) => (
              <button
                type="button"
                className="categoria"
                key={categoria.id}
                onClick={() => navigate(`/profesionales?categoria=${categoria.id}`)}
              >
                <span className="categoria-icono">
                  <IconoCategoria nombre={categoria.nombre} />
                </span>
                <span>{categoria.nombre}</span>
                <span className="flecha" aria-hidden="true">↗</span>
              </button>
            ))}
          </div>
        )
      )}

      <div className="encabezado-seccion encabezado-servicios">
        <h2>Servicios disponibles</h2>
        <p>Consulta el valor base de cada servicio y quién lo ofrece.</p>
      </div>

      <EstadoCarga
        cargando={servicios.cargando}
        error={servicios.error}
        onReintentar={servicios.recargar}
        texto="Cargando servicios…"
      />

      {!servicios.cargando && !servicios.error && servicios.datos && (
        servicios.datos.length === 0 ? (
          <p className="sin-resultados">Todavía no hay servicios disponibles.</p>
        ) : (
          <div className="servicios-lista">
            {servicios.datos.map((servicio) => (
              <article className="tarjeta-servicio" key={servicio.id}>
                <span className="oficio">{servicio.categoria_nombre}</span>
                <h3>{servicio.nombre}</h3>
                <p>{servicio.descripcion}</p>
                <div className="servicio-pie">
                  <span className="oferta-precio">
                    Valor base: {formatearPrecio(servicio.precio_base)}
                  </span>
                  <Link
                    className="boton-secundario"
                    to={`/profesionales?servicio=${servicio.id}`}
                  >
                    Ver profesionales
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )
      )}
    </section>
  );
}

export default Servicios;