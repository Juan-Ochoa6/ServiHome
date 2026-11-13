import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  cambiarEstadoSolicitud,
  listarMisPagos,
  listarOfertas,
  listarSolicitudes,
} from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import CodigoServicio from '../components/CodigoServicio.jsx';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';
import NegociacionPrecio from '../components/NegociacionPrecio.jsx';
import PagoSolicitud from '../components/PagoSolicitud.jsx';
import ReporteIncidente from '../components/ReporteIncidente.jsx';
import ResenaSolicitud from '../components/ResenaSolicitud.jsx';

const ESTADOS_CANCELABLES = ['pendiente', 'aceptada'];
const ESTADOS_CON_INCIDENTE = ['aceptada', 'en_proceso', 'completada'];

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
  const pagos = useCargar(listarMisPagos);

  const [abierta, setAbierta] = useState(null); // solicitud con la negociación abierta
  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');

  const solicitudes = datos
    ? [...datos].sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
    : [];

  // Pagos indexados por el id de su solicitud.
  const pagoPorSolicitud = {};
  for (const pago of pagos.datos ?? []) {
    pagoPorSolicitud[pago.solicitud] = pago;
  }

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
              ? 'Aquí verás tus solicitudes, el precio, los códigos del servicio, el pago y tus reseñas.'
              : 'Negocia el precio, inicia y completa cada servicio con el código del cliente.'}
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
              const puedeReportar = esCliente && ESTADOS_CON_INCIDENTE.includes(solicitud.estado);
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

                    {(solicitud.estado === 'aceptada' || solicitud.estado === 'en_proceso') && (
                      <CodigoServicio
                        solicitud={solicitud}
                        esCliente={esCliente}
                        onCambio={recargar}
                      />
                    )}

                    {solicitud.estado === 'completada' && (
                      <>
                        <PagoSolicitud
                          solicitud={solicitud}
                          pago={pagoPorSolicitud[solicitud.id]}
                          esCliente={esCliente}
                          onCambio={pagos.recargar}
                        />
                        <ResenaSolicitud solicitud={solicitud} esCliente={esCliente} />
                      </>
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

                    {puedeReportar && <ReporteIncidente solicitud={solicitud} />}

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