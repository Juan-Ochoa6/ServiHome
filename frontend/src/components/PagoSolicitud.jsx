import { useState } from 'react';
import { crearPago } from '../services/catalogo.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import { CLASE_ESTADO_PAGO, ETIQUETAS_PAGO, METODOS_PAGO } from '../utils/etiquetas.js';
import BotonArchivo from './BotonArchivo.jsx';
import Mensaje from './Mensaje.jsx';

const AVISO_POR_ESTADO = {
  pendiente: 'Esperando la confirmación de ServiHome.',
  fallido: 'No se pudo confirmar el pago.',
  reembolsado: 'El pago fue reembolsado.',
};

// Solo se muestra en solicitudes completadas.
function PagoSolicitud({ solicitud, pago, esCliente, onCambio }) {
  const [metodo, setMetodo] = useState('transferencia');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  async function registrar(evento) {
    evento.preventDefault();
    setError('');
    setEnviando(true);

    try {
      await crearPago(solicitud.id, metodo);
      onCambio();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  if (pago) {
    return (
      <div className="subbloque">
        <div className="tarjeta-panel-cabecera">
          <h4>Pago</h4>
          <span className={`estado-solicitud ${CLASE_ESTADO_PAGO[pago.estado] ?? ''}`}>
            {ETIQUETAS_PAGO[pago.estado] ?? pago.estado}
          </span>
        </div>

        <dl className="datos-panel">
          <dt>Valor total</dt>
          <dd>{formatearPrecio(pago.monto_total)}</dd>
          <dt>Método</dt>
          <dd>{METODOS_PAGO[pago.metodo] ?? pago.metodo}</dd>
          {!esCliente && (
            <>
              <dt>Comisión ({Number(pago.porcentaje_comision)} %)</dt>
              <dd>{formatearPrecio(pago.monto_comision)}</dd>
              <dt>Recibes</dt>
              <dd>{formatearPrecio(pago.monto_profesional)}</dd>
            </>
          )}
          {pago.fecha_pago && (
            <>
              <dt>Fecha de pago</dt>
              <dd>{formatearFecha(pago.fecha_pago)}</dd>
            </>
          )}
        </dl>

        {AVISO_POR_ESTADO[pago.estado] && <p>{AVISO_POR_ESTADO[pago.estado]}</p>}

        {pago.estado === 'pagado' && esCliente && (
          <div className="solicitud-acciones">
            <BotonArchivo ruta={`/api/pagos/${pago.id}/factura/`} className="boton-secundario">
              Descargar comprobante
            </BotonArchivo>
          </div>
        )}
      </div>
    );
  }

  if (!esCliente) {
    return (
      <div className="subbloque">
        <h4>Pago</h4>
        <p>El cliente aún no ha registrado el pago.</p>
      </div>
    );
  }

  return (
    <form className="subbloque" onSubmit={registrar}>
      <h4>Registrar el pago</h4>
      <p>
        Valor del servicio: <strong>{formatearPrecio(solicitud.precio_acordado)}</strong>. Elige
        cómo pagaste; ServiHome confirmará el pago.
      </p>

      <div className="codigo-form">
        <select
          aria-label="Método de pago"
          value={metodo}
          onChange={(evento) => setMetodo(evento.target.value)}
        >
          {Object.entries(METODOS_PAGO).map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
        <button type="submit" className="boton-contactar" disabled={enviando}>
          {enviando ? 'Registrando…' : 'Registrar pago'}
        </button>
      </div>

      <Mensaje tipo="error">{error}</Mensaje>
    </form>
  );
}

export default PagoSolicitud;