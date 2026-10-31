import { useState } from 'react';
import { Link } from 'react-router-dom';
import { cambiarEstadoSolicitud, listarSolicitudes } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';

const ESTADOS_CANCELABLES = ['pendiente', 'aceptada'];

function Solicitudes() {
  const { sesion } = useAuth();
  const { datos, cargando, error, recargar } = useCargar(listarSolicitudes);
  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');

  const solicitudes = datos
    ? [...datos].sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
    : [];

  async function cancelar(solicitud) {
    if (!window.confirm('¿Seguro que quieres cancelar esta solicitud?')) return;

    setErrorAccion('');
    setProcesando(solicitud.id);

    try {
      await cambiarEstadoSolicitud(solicitud.id, 'cancelada');
      recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setProcesando(null);
    }
  }

  return (
    <section className="seccion">
      <div className="encabezado-seccion encabezado-accion">
        <div>
          <span className="etiqueta">MIS SOLICITUDES</span>
          <h2>Solicitudes de servicio</h2>
          <p>Aquí verás las solicitudes y su estado.</p>
        </div>
        <Link className="boton-contactar" to="/profesionales">Nueva solicitud</Link>
      </div>

      <EstadoCarga
        cargando={cargando && !datos}
        error={error}
        onReintentar={recargar}
        texto="Cargando solicitudes…"
      />

      <Mensaje tipo="error">{errorAccion}</Mensaje>

      {datos && !error && (
        solicitudes.length === 0 ? (
          <div className="solicitudes-vacio">
            <span aria-hidden="true" style={{ fontSize: '2.4rem' }}>📋</span>
            <p>Todavía no tienes solicitudes. Elige un profesional para crear la primera.</p>
            <Link className="boton-secundario" to="/profesionales">Ver profesionales</Link>
          </div>
        ) : (
          <div className="solicitudes-lista">
            {solicitudes.map((solicitud) => {
              // La lista del backend ya viene filtrada por rol: comparo el usuario
              // para saber si en esta solicitud soy el cliente o el profesional.
              const esCliente = solicitud.cliente_nombre === sesion?.usuario;
              const puedeCancelar =
                esCliente && ESTADOS_CANCELABLES.includes(solicitud.estado);

              return (
                <article className="tarjeta-solicitud" key={solicitud.id}>
                  <span className="profesional-elegido-icono">📋</span>
                  <div className="solicitud-cuerpo">
                    <div className="solicitud-cabecera">
                      <strong>{solicitud.servicio_nombre}</strong>
                      <span className={`estado-solicitud estado-${solicitud.estado}`}>
                        {solicitud.estado_display}
                      </span>
                    </div>
                    <p className="solicitud-meta">
                      {esCliente
                        ? `Profesional: ${solicitud.profesional_nombre}`
                        : `Cliente: ${solicitud.cliente_nombre}`}
                    </p>
                    <p>{solicitud.descripcion}</p>
                    <p className="solicitud-meta">📍 {solicitud.direccion_servicio}</p>
                    <p className="solicitud-meta">🕒 {formatearFecha(solicitud.fecha_solicitada)}</p>
                    {solicitud.precio_acordado && (
                      <p className="solicitud-meta">
                        Precio acordado: {formatearPrecio(solicitud.precio_acordado)}
                      </p>
                    )}

                    {puedeCancelar && (
                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          onClick={() => cancelar(solicitud)}
                          disabled={procesando === solicitud.id}
                        >
                          {procesando === solicitud.id ? 'Cancelando…' : 'Cancelar solicitud'}
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )
      )}
    </section>
  );
}

export default Solicitudes;