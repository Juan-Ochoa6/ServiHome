import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  cambiarEstadoSolicitud,
  listarOfertas,
  listarSolicitudes,
} from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';
import NegociacionPrecio from '../components/NegociacionPrecio.jsx';

const ESTADOS_CANCELABLES = ['pendiente', 'aceptada'];

// Precio que el profesional publicó para ese servicio (solo como referencia).
function precioDeReferencia(ofertas, solicitud) {
  const oferta = ofertas?.find(
    (item) =>
      item.profesional === solicitud.profesional && item.servicio === solicitud.servicio,
  );
  return oferta ? oferta.precio : null;
}

function Solicitudes() {
  const { sesion } = useAuth();
  const esCliente = sesion?.rol === 'cliente';

  const { datos, cargando, error, recargar } = useCargar(listarSolicitudes);
  const ofertas = useCargar(listarOfertas);

  const [abierta, setAbierta] = useState(null); // id de la solicitud con la negociación abierta
  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');

  const solicitudes = datos
    ? [...datos].sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
    : [];

  async function cambiarEstado(solicitud, estado, confirmacion) {
    if (!window.confirm(confirmacion)) return;

    setErrorAccion('');
    setProcesando(solicitud.id);

    try {
      await cambiarEstadoSolicitud(solicitud.id, estado);
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
          <span className="etiqueta">
            {esCliente ? 'MIS SOLICITUDES' : 'SOLICITUDES RECIBIDAS'}
          </span>
          <h2>{esCliente ? 'Solicitudes de servicio' : 'Solicitudes que has recibido'}</h2>
          <p>
            {esCliente
              ? 'Aquí verás las solicitudes, su estado y la negociación del precio.'
              : 'Negocia el precio con el cliente y responde cada solicitud.'}
          </p>
        </div>
        {esCliente && (
          <Link className="boton-contactar" to="/profesionales">Nueva solicitud</Link>
        )}
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
            <p>
              {esCliente
                ? 'Todavía no tienes solicitudes. Elige un profesional para crear la primera.'
                : 'Todavía no has recibido solicitudes.'}
            </p>
            {esCliente && (
              <Link className="boton-secundario" to="/profesionales">Ver profesionales</Link>
            )}
          </div>
        ) : (
          <div className="solicitudes-lista">
            {solicitudes.map((solicitud) => {
              const miPerfilId = esCliente ? solicitud.cliente : solicitud.profesional;
              const otraParte = esCliente
                ? solicitud.profesional_nombre
                : solicitud.cliente_nombre;
              const puedeCancelar =
                esCliente && ESTADOS_CANCELABLES.includes(solicitud.estado);
              const puedeRechazar = !esCliente && solicitud.estado === 'pendiente';
              const abiertaAhora = abierta === solicitud.id;

              let textoNegociacion = 'Ver historial de precios';
              if (abiertaAhora) textoNegociacion = 'Ocultar precios';
              else if (solicitud.estado === 'pendiente') textoNegociacion = 'Negociar precio';

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
                      {esCliente ? 'Profesional' : 'Cliente'}: {otraParte}
                    </p>
                    <p>{solicitud.descripcion}</p>
                    <p className="solicitud-meta">📍 {solicitud.direccion_servicio}</p>
                    <p className="solicitud-meta">🕒 {formatearFecha(solicitud.fecha_solicitada)}</p>
                    {solicitud.precio_acordado && (
                      <p className="solicitud-meta">
                        Precio acordado: <strong>{formatearPrecio(solicitud.precio_acordado)}</strong>
                      </p>
                    )}

                    <div className="solicitud-acciones">
                      <button
                        type="button"
                        className="boton-secundario"
                        onClick={() => setAbierta(abiertaAhora ? null : solicitud.id)}
                      >
                        {textoNegociacion}
                      </button>

                      {puedeCancelar && (
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          onClick={() =>
                            cambiarEstado(
                              solicitud,
                              'cancelada',
                              '¿Seguro que quieres cancelar esta solicitud?',
                            )
                          }
                          disabled={procesando === solicitud.id}
                        >
                          {procesando === solicitud.id ? 'Cancelando…' : 'Cancelar solicitud'}
                        </button>
                      )}

                      {puedeRechazar && (
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          onClick={() =>
                            cambiarEstado(
                              solicitud,
                              'rechazada',
                              '¿Seguro que quieres rechazar esta solicitud?',
                            )
                          }
                          disabled={procesando === solicitud.id}
                        >
                          {procesando === solicitud.id ? 'Rechazando…' : 'Rechazar solicitud'}
                        </button>
                      )}
                    </div>

                    {abiertaAhora && (
                      <NegociacionPrecio
                        solicitud={solicitud}
                        miPerfilId={miPerfilId}
                        otraParte={otraParte}
                        precioReferencia={precioDeReferencia(ofertas.datos, solicitud)}
                        onCambio={recargar}
                      />
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