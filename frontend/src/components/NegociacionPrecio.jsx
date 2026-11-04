import { useCallback, useState } from 'react';
import {
  crearPropuesta,
  listarPropuestas,
  responderPropuesta,
} from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import EstadoCarga from './EstadoCarga.jsx';
import Mensaje from './Mensaje.jsx';

function NegociacionPrecio({ solicitud, miPerfilId, otraParte, precioReferencia, onCambio }) {
  const cargarPropuestas = useCallback(
    () => listarPropuestas(solicitud.id),
    [solicitud.id],
  );
  const { datos, cargando, error, recargar } = useCargar(cargarPropuestas);

  const [precio, setPrecio] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [errorAccion, setErrorAccion] = useState('');

  const enNegociacion = solicitud.estado === 'pendiente';
  const propuestas = datos ?? [];
  const pendiente = propuestas.find((propuesta) => propuesta.estado === 'pendiente');
  const esperandoRespuesta = Boolean(pendiente) && pendiente.proponente === miPerfilId;
  const debeResponder = Boolean(pendiente) && pendiente.proponente !== miPerfilId;

  async function ejecutar(accion) {
    setErrorAccion('');
    setEnviando(true);

    try {
      await accion();
      setPrecio('');
      recargar();
      onCambio();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setEnviando(false);
    }
  }

  function proponer(evento) {
    evento.preventDefault();
    ejecutar(() => crearPropuesta(solicitud.id, precio.trim()));
  }

  function aceptar() {
    const texto = `¿Aceptar el precio de ${formatearPrecio(pendiente.precio)}? La solicitud quedará aceptada.`;
    if (!window.confirm(texto)) return;
    ejecutar(() => responderPropuesta(solicitud.id, pendiente.id, 'aceptar'));
  }

  function rechazar() {
    if (!window.confirm('¿Rechazar esta propuesta de precio?')) return;
    ejecutar(() => responderPropuesta(solicitud.id, pendiente.id, 'rechazar'));
  }

  return (
    <div className="negociacion">
      {precioReferencia !== null && (
        <p className="solicitud-meta">
          Precio publicado por el profesional:{' '}
          <strong>{formatearPrecio(precioReferencia)}</strong>
        </p>
      )}

      <EstadoCarga
        cargando={cargando && !datos}
        error={error}
        onReintentar={recargar}
        texto="Cargando propuestas…"
      />

      {datos && (
        propuestas.length === 0 ? (
          <p className="solicitud-meta">Todavía no hay propuestas de precio.</p>
        ) : (
          <ul className="propuestas-lista">
            {propuestas.map((propuesta) => (
              <li className="propuesta-item" key={propuesta.id}>
                <div className="propuesta-info">
                  <strong>{formatearPrecio(propuesta.precio)}</strong>
                  <span className="solicitud-meta">
                    {propuesta.proponente === miPerfilId ? 'Tú' : propuesta.proponente_nombre}
                    {' · '}
                    {formatearFecha(propuesta.fecha_creacion)}
                  </span>
                </div>
                <span
                  className={`estado-solicitud estado-propuesta-${propuesta.estado}`}
                >
                  {propuesta.estado_display}
                </span>
              </li>
            ))}
          </ul>
        )
      )}

      {enNegociacion && datos && (
        <>
          {esperandoRespuesta && (
            <Mensaje tipo="info">Esperando la respuesta de {otraParte}.</Mensaje>
          )}

          {debeResponder && (
            <div className="negociacion-respuesta">
              <p>
                <strong>{otraParte}</strong> propone{' '}
                <strong>{formatearPrecio(pendiente.precio)}</strong>.
              </p>
              <div className="solicitud-acciones">
                <button
                  type="button"
                  className="boton-contactar"
                  onClick={aceptar}
                  disabled={enviando}
                >
                  Aceptar precio
                </button>
                <button
                  type="button"
                  className="boton-secundario boton-peligro"
                  onClick={rechazar}
                  disabled={enviando}
                >
                  Rechazar propuesta
                </button>
              </div>
            </div>
          )}

          {!esperandoRespuesta && (
            <form className="propuesta-formulario" onSubmit={proponer}>
              <label htmlFor={`precio-${solicitud.id}`}>
                {debeResponder ? 'O envía una contraoferta' : 'Proponer un precio'}
              </label>
              <div className="propuesta-campo">
                <input
                  id={`precio-${solicitud.id}`}
                  type="number"
                  min="1"
                  step="1"
                  inputMode="numeric"
                  placeholder="Ej. 50000"
                  value={precio}
                  onChange={(evento) => setPrecio(evento.target.value)}
                  required
                />
                <button type="submit" className="boton-secundario" disabled={enviando}>
                  {enviando
                    ? 'Enviando…'
                    : debeResponder
                      ? 'Contraofertar'
                      : 'Enviar propuesta'}
                </button>
              </div>
            </form>
          )}
        </>
      )}

      <Mensaje tipo="error">{errorAccion}</Mensaje>
    </div>
  );
}

export default NegociacionPrecio;