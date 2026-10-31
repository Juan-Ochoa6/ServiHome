import { Link } from 'react-router-dom';

function Solicitudes({ solicitudes }) {
  return (
    <section className="seccion">
      <div className="encabezado-seccion encabezado-accion">
        <div>
          <span className="etiqueta">MIS SOLICITUDES</span>
          <h2>Solicitudes de servicio</h2>
          <p>Aquí verás las solicitudes que has creado.</p>
        </div>
        <Link className="boton-contactar" to="/profesionales">Nueva solicitud</Link>
      </div>

      {solicitudes.length === 0 ? (
        <div className="solicitudes-vacio">
          <span aria-hidden="true" style={{ fontSize: '2.4rem' }}>📋</span>
          <p>Todavía no tienes solicitudes. Elige un profesional para crear la primera.</p>
          <Link className="boton-secundario" to="/profesionales">Ver profesionales</Link>
        </div>
      ) : (
        <div className="solicitudes-lista">
          {solicitudes.map((solicitud) => (
            <article className="tarjeta-solicitud" key={solicitud.id}>
              <span className="profesional-elegido-icono">{solicitud.profesional.icono}</span>
              <div className="solicitud-cuerpo">
                <div className="solicitud-cabecera">
                  <strong>{solicitud.profesional.nombre} · {solicitud.profesional.oficio}</strong>
                  <span className="estado-solicitud">{solicitud.estado}</span>
                </div>
                <p>{solicitud.descripcion}</p>
                <p className="solicitud-meta">📍 {solicitud.direccion}</p>
                <p className="solicitud-meta">🕒 {solicitud.fecha.replace('T', ' ')}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default Solicitudes;