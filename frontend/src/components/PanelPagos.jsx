import { useState } from 'react';
import { cambiarEstadoPago, listarPagosAdmin } from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import { CLASE_ESTADO_PAGO, ETIQUETAS_PAGO, METODOS_PAGO } from '../utils/etiquetas.js';
import BotonArchivo from './BotonArchivo.jsx';
import EstadoCarga from './EstadoCarga.jsx';
import Mensaje from './Mensaje.jsx';

const FILTROS = [
  ['pendiente', 'Pendientes'],
  ['pagado', 'Pagados'],
  ['fallido', 'Fallidos'],
  ['reembolsado', 'Reembolsados'],
  ['', 'Todos'],
];

function PanelPagos() {
  const pagos = useCargar(listarPagosAdmin);

  const [filtro, setFiltro] = useState('pendiente');
  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');
  const [exito, setExito] = useState('');

  const lista = (pagos.datos ?? [])
    .filter((pago) => !filtro || pago.estado === filtro)
    .sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion));

  async function cambiar(pago, estado, confirmacion, mensaje) {
    if (!window.confirm(confirmacion)) return;

    setErrorAccion('');
    setExito('');
    setProcesando(pago.id);

    try {
      await cambiarEstadoPago(pago.id, estado);
      setExito(mensaje);
      pagos.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setProcesando(null);
    }
  }

  return (
    <>
      <p className="nota-panel">
        El cliente registra el pago cuando el servicio se completa y aquí se confirma. Al
        confirmarlo, el cliente puede descargar su comprobante.
      </p>

      <div className="filtro-panel">
        <label htmlFor="filtro-pagos">Mostrar</label>
        <select
          id="filtro-pagos"
          value={filtro}
          onChange={(evento) => setFiltro(evento.target.value)}
        >
          {FILTROS.map(([valor, texto]) => (
            <option key={valor || 'todos'} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </div>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      <EstadoCarga
        cargando={pagos.cargando && !pagos.datos}
        error={pagos.error}
        onReintentar={pagos.recargar}
        texto="Cargando pagos…"
      />

      {pagos.datos && !pagos.error && (
        lista.length === 0 ? (
          <p className="sin-resultados">No hay pagos con ese estado.</p>
        ) : (
          <div className="panel-lista">
            {lista.map((pago) => {
              const ocupado = procesando === pago.id;

              return (
                <article className="tarjeta-panel" key={pago.id}>
                  <div className="tarjeta-panel-cabecera">
                    <strong>
                      Pago #{pago.id} · Solicitud #{pago.solicitud}
                    </strong>
                    <span className={`estado-solicitud ${CLASE_ESTADO_PAGO[pago.estado] ?? ''}`}>
                      {ETIQUETAS_PAGO[pago.estado] ?? pago.estado}
                    </span>
                  </div>

                  <dl className="datos-panel">
                    <dt>Cliente</dt>
                    <dd>{pago.cliente_nombre}</dd>
                    <dt>Profesional</dt>
                    <dd>{pago.profesional_nombre}</dd>
                    <dt>Valor total</dt>
                    <dd>{formatearPrecio(pago.monto_total)}</dd>
                    <dt>Comisión ({Number(pago.porcentaje_comision)} %)</dt>
                    <dd>{formatearPrecio(pago.monto_comision)}</dd>
                    <dt>Para el profesional</dt>
                    <dd>{formatearPrecio(pago.monto_profesional)}</dd>
                    <dt>Método</dt>
                    <dd>{METODOS_PAGO[pago.metodo] ?? pago.metodo}</dd>
                    <dt>Registrado</dt>
                    <dd>{formatearFecha(pago.fecha_creacion)}</dd>
                    {pago.fecha_pago && (
                      <>
                        <dt>Confirmado</dt>
                        <dd>{formatearFecha(pago.fecha_pago)}</dd>
                      </>
                    )}
                  </dl>

                  {pago.estado === 'pendiente' && (
                    <div className="solicitud-acciones">
                      <button
                        type="button"
                        className="boton-contactar"
                        disabled={ocupado}
                        onClick={() =>
                          cambiar(
                            pago,
                            'pagado',
                            `¿Confirmar el pago de ${formatearPrecio(pago.monto_total)} de ${pago.cliente_nombre}?`,
                            'Pago confirmado.',
                          )
                        }
                      >
                        {ocupado ? 'Procesando…' : 'Confirmar pago'}
                      </button>
                      <button
                        type="button"
                        className="boton-secundario boton-peligro"
                        disabled={ocupado}
                        onClick={() =>
                          cambiar(
                            pago,
                            'fallido',
                            '¿Marcar este pago como fallido?',
                            'Pago marcado como fallido.',
                          )
                        }
                      >
                        Marcar fallido
                      </button>
                    </div>
                  )}

                  {pago.estado === 'pagado' && (
                    <div className="solicitud-acciones">
                      <BotonArchivo
                        ruta={`/api/pagos/${pago.id}/factura/`}
                        className="boton-secundario"
                      >
                        Ver comprobante
                      </BotonArchivo>
                      <button
                        type="button"
                        className="boton-secundario boton-peligro"
                        disabled={ocupado}
                        onClick={() =>
                          cambiar(
                            pago,
                            'reembolsado',
                            '¿Reembolsar este pago? Esta acción no se puede deshacer.',
                            'Pago reembolsado.',
                          )
                        }
                      >
                        {ocupado ? 'Procesando…' : 'Reembolsar'}
                      </button>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )
      )}
    </>
  );
}

export default PanelPagos;