import { Link, useParams } from 'react-router-dom';
import { listarOfertas } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPrecio } from '../utils/formato.js';
import { agruparPorProfesional, categoriasDe } from '../utils/profesionales.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import IconoCategoria from '../components/IconoCategoria.jsx';

function PerfilProfesional() {
  const { id } = useParams();
  const { datos, cargando, error, recargar } = useCargar(listarOfertas);

  const profesional = datos
    ? agruparPorProfesional(datos).find((item) => item.id === Number(id))
    : null;

  if (cargando || error) {
    return (
      <section className="seccion panel-flujo">
        <Link className="boton-secundario boton-volver" to="/profesionales">
          ← Volver a profesionales
        </Link>
        <EstadoCarga
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          texto="Cargando perfil…"
        />
      </section>
    );
  }

  if (!profesional) {
    return (
      <section className="seccion panel-flujo">
        <div className="encabezado-seccion">
          <h2>Profesional no encontrado</h2>
          <p>Es posible que el perfil ya no esté disponible.</p>
        </div>
        <Link className="boton-contactar" to="/profesionales">Volver a profesionales</Link>
      </section>
    );
  }

  const categorias = categoriasDe(profesional);

  return (
    <section className="seccion panel-flujo">
      <Link className="boton-secundario boton-volver" to="/profesionales">
        ← Volver a profesionales
      </Link>

      <div className="perfil-contenido">
        <div className="profesional-avatar perfil-avatar">
          <IconoCategoria nombre={categorias[0]} />
        </div>
        <span className="oficio">{categorias.join(' · ')}</span>
        <h2>{profesional.nombre}</h2>
        <p>
          {profesional.descripcion ||
            'Este profesional aún no ha agregado una descripción.'}
        </p>
        {profesional.experiencia > 0 && (
          <p className="perfil-calificacion">
            {profesional.experiencia}{' '}
            {profesional.experiencia === 1 ? 'año' : 'años'} de experiencia
          </p>
        )}

        <h3 className="titulo-ofertas">Servicios que ofrece</h3>
        <div className="ofertas-lista">
          {profesional.ofertas.map((oferta) => (
            <div className="oferta-item" key={oferta.id}>
              <div className="oferta-info">
                <strong>{oferta.servicio_nombre}</strong>
                {oferta.servicio_descripcion && (
                  <span className="solicitud-meta">{oferta.servicio_descripcion}</span>
                )}
                <span className="oferta-precio">{formatearPrecio(oferta.precio)}</span>
              </div>
              <Link className="boton-contactar" to={`/solicitudes/nueva/${oferta.id}`}>
                Solicitar servicio
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PerfilProfesional;