import { useCallback, useState } from 'react';
import { obtenerFinanzas } from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPeriodo, formatearPrecio } from '../utils/formato.js';
import EstadoCarga from './EstadoCarga.jsx';

const PERIODOS = [
  ['dia', 'Por día (últimos 30 días)'],
  ['semana', 'Por semana (últimas 12 semanas)'],
  ['mes', 'Por mes (últimos 12 meses)'],
  ['ano', 'Por año (últimos 5 años)'],
];

function PanelFinanzas() {
  const [periodo, setPeriodo] = useState('mes');
  const cargar = useCallback(() => obtenerFinanzas(periodo), [periodo]);
  const finanzas = useCargar(cargar);

  const resumen = finanzas.datos?.resumen;
  const filas = finanzas.datos?.datos ?? [];
  const maxGanancia = Math.max(0, ...filas.map((fila) => Number(fila.ganancia_servihome)));

  return (
    <>
      <p className="nota-panel">
        Solo cuentan los pagos confirmados. Las tarjetas muestran el total histórico y la tabla
        detalla el período que elijas.
      </p>

      <div className="filtro-panel">
        <label htmlFor="periodo-finanzas">Agrupar</label>
        <select
          id="periodo-finanzas"
          value={periodo}
          onChange={(evento) => setPeriodo(evento.target.value)}
        >
          {PERIODOS.map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </div>

      <EstadoCarga
        cargando={finanzas.cargando && !finanzas.datos}
        error={finanzas.error}
        onReintentar={finanzas.recargar}
        texto="Cargando finanzas…"
      />

      {resumen && !finanzas.error && (
        <>
          <div className="tablero">
            <div className="dato-tablero">
              <span>Total pagado</span>
              <strong>{formatearPrecio(resumen.total_pagado)}</strong>
              <span>{resumen.cantidad_pagos} pagos confirmados</span>
            </div>
            <div className="dato-tablero">
              <span>Ganancia de ServiHome</span>
              <strong>{formatearPrecio(resumen.ganancia_servihome)}</strong>
              <span>en comisiones</span>
            </div>
            <div className="dato-tablero">
              <span>Para los profesionales</span>
              <strong>{formatearPrecio(resumen.total_profesionales)}</strong>
              <span>después de comisión</span>
            </div>
          </div>

          {filas.length === 0 ? (
            <p className="sin-resultados">Todavía no hay pagos confirmados en este período.</p>
          ) : (
            <div className="tabla-scroll">
              <table className="tabla-finanzas">
                <thead>
                  <tr>
                    <th scope="col">Período</th>
                    <th scope="col">Pagos</th>
                    <th scope="col">Total pagado</th>
                    <th scope="col">Comisión</th>
                    <th scope="col">Profesionales</th>
                  </tr>
                </thead>
                <tbody>
                  {filas.map((fila) => {
                    const ganancia = Number(fila.ganancia_servihome);
                    const ancho = maxGanancia > 0 ? (ganancia / maxGanancia) * 100 : 0;

                    return (
                      <tr key={fila.periodo}>
                        <td>{formatearPeriodo(fila.periodo, periodo)}</td>
                        <td>{fila.cantidad_pagos}</td>
                        <td>{formatearPrecio(fila.total_pagado)}</td>
                        <td>
                          {formatearPrecio(fila.ganancia_servihome)}
                          <span
                            className="barra-ganancia"
                            style={{ width: `${ancho}%` }}
                            aria-hidden="true"
                          />
                        </td>
                        <td>{formatearPrecio(fila.total_profesionales)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </>
  );
}

export default PanelFinanzas;