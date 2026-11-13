import { useCallback } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  listarOfertas,
  listarResenasProfesional,
  obtenerReputacion,
} from '../services/catalogo.js';
import { listarPortafolioPublico } from '../services/profesional.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import { agruparPorProfesional, categoriasDe } from '../utils/profesionales.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Estrellas from '../components/Estrellas.jsx';
import IconoCategoria from '../components/IconoCategoria.jsx';

function PerfilProfesional() {
  const { id } = useParams();
  const { sesion } = useAuth();
  const { datos, cargando, error, recargar } = useCargar(listarOfertas);

  const cargarPortafolio = useCallback(() => listarPortafolioPublico(id), [id]);
  const cargarReputacion = useCallback(() => obtenerReputacion(id), [id]);
  const cargarResenas = useCallback(() => listarResenasProfesional(id), [id]);
  const portafolio = useCargar(cargarPortafolio);
  const reputacion = useCargar(cargarReputacion);
  const resenas = useCargar(cargarResenas);

  // Solo los clientes (o quien aún no inició sesión) pueden solicitar servicios.
  const puedeSolicitar = !sesion || sesion.rol === 'cliente';

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
  const trabajos = portafolio.datos ?? [];
  const opiniones = resenas.datos ?? [];
  const resumen = reputacion.datos;

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

        {resumen && (
          resumen.total_resenas > 0 ? (
            <p className="perfil-calificacion">
              <Estrellas valor={resumen.promedio_calificacion} />{' '}
              {Number(resumen.promedio_calificacion).toFixed(1)} · {resumen.total_resenas}{' '}
              {resumen.total_resenas === 1 ? 'reseña' : 'reseñas'}
            </p>
          ) : (
            <p className="perfil-calificacion">Aún no tiene reseñas</p>
          )
        )}

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
              {puedeSolicitar && (
                <Link className="boton-contactar" to={`/solicitudes/nueva/${oferta.id}`}>
                  Solicitar servicio
                </Link>
              )}
            </div>
          ))}
        </div>

        {trabajos.length > 0 && (
          <>
            <h3 className="titulo-ofertas">Trabajos realizados</h3>
            <div className="trabajos-grid">
              {trabajos.map((trabajo) => (
                <article className="tarjeta-trabajo" key={trabajo.id}>
                  <img src={trabajo.imagen} alt={trabajo.titulo} loading="lazy" />
                  <div className="trabajo-cuerpo">
                    <h3>{trabajo.titulo}</h3>
                    {trabajo.servicio_nombre && (
                      <span className="oficio">{trabajo.servicio_nombre}</span>
                    )}
                    <p>{trabajo.descripcion}</p>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}

        {opiniones.length > 0 && (
          <>
            <h3 className="titulo-ofertas">Opiniones de clientes</h3>
            <div className="lista-resenas">
              {opiniones.map((resena) => (
                <article className="resena-item" key={resena.id}>
                  <div className="resena-cabecera">
                    <strong>{resena.cliente_nombre}</strong>
                    <Estrellas valor={resena.calificacion} />
                  </div>
                  {resena.comentario && <p>{resena.comentario}</p>}
                  <span className="solicitud-meta">{formatearFecha(resena.fecha_creacion)}</span>
                </article>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default PerfilProfesional;