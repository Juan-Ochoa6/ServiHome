import { useState } from 'react';
import { actualizarIncidente, listarIncidentes } from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha } from '../utils/formato.js';
import { ETIQUETAS_INCIDENTE, TIPOS_INCIDENTE } from '../utils/etiquetas.js';
import EstadoCarga from './EstadoCarga.jsx';
import Mensaje from './Mensaje.jsx';

const CLASE_ESTADO = {
  pendiente: '',
  en_revision: 'estado-en_proceso',
  resuelto: 'estado-completada',
  rechazado: 'estado-rechazada',
};

const FILTROS = [
  ['abiertos', 'Abiertos'],
  ['pendiente', 'Pendientes'],
  ['en_revision', 'En revisión'],
  ['resuelto', 'Resueltos'],
  ['rechazado', 'Rechazados'],
  ['todos', 'Todos'],
];

function coincide(incidente, filtro) {
  if (filtro === 'todos') return true;
  if (filtro === 'abiertos') return ['pendiente', 'en_revision'].includes(incidente.estado);
  return incidente.estado === filtro;
}

function TarjetaIncidente({ incidente, ocupado, onGuardar }) {
  const [estado, setEstado] = useState(incidente.estado);
  const [respuesta, setRespuesta] = useState(incidente.respuesta_administrador ?? '');
  const urgente = incidente.tipo === 'emergencia';

  return (
    <article className={`tarjeta-panel ${urgente ? 'tarjeta-urgente' : ''}`}>
      <div className="tarjeta-panel-cabecera">
        <strong>
          Incidente #{incidente.id} · {TIPOS_INCIDENTE[incidente.tipo] ?? incidente.tipo}
        </strong>
        <span className={`estado-solicitud ${CLASE_ESTADO[incidente.estado] ?? ''}`}>
          {ETIQUETAS_INCIDENTE[incidente.estado] ?? incidente.estado}
        </span>
      </div>

      <dl className="datos-panel">
        <dt>Solicitud</dt>
        <dd>#{incidente.solicitud}</dd>
        <dt>Reportado por</dt>
        <dd>Perfil #{incidente.reportado_por}</dd>
        <dt>Creado</dt>
        <dd>{formatearFecha(incidente.fecha_creacion)}</dd>
        <dt>Actualizado</dt>
        <dd>{formatearFecha(incidente.fecha_actualizacion)}</dd>
        <dt>Descripción</dt>
        <dd>{incidente.descripcion}</dd>
      </dl>

      <div className="campo-formulario">
        <label htmlFor={`estado-incidente-${incidente.id}`}>Estado</label>
        <select
          id={`estado-incidente-${incidente.id}`}
          value={estado}
          onChange={(evento) => setEstado(evento.target.value)}
        >
          {Object.entries(ETIQUETAS_INCIDENTE).map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </div>

      <div className="campo-formulario">
        <label htmlFor={`respuesta-incidente-${incidente.id}`}>
          Respuesta para el cliente (le llega por correo)
        </label>
        <textarea
          id={`respuesta-incidente-${incidente.id}`}
          rows={3}
          value={respuesta}
          onChange={(evento) => setRespuesta(evento.target.value)}
          placeholder="Ej. Revisamos el caso y nos comunicamos con el profesional."
        />
      </div>

      <div className="solicitud-acciones">
        <button
          type="button"
          className="boton-contactar"
          disabled={ocupado}
          onClick={() => onGuardar(estado, respuesta.trim())}
        >
          {ocupado ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </article>
  );
}

function PanelIncidentes() {
  const incidentes = useCargar(listarIncidentes);

  const [filtro, setFiltro] = useState('abiertos');
  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');
  const [exito, setExito] = useState('');

  const lista = (incidentes.datos ?? [])
    .filter((incidente) => coincide(incidente, filtro))
    .sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion));

  async function guardar(incidente, estado, respuesta) {
    setErrorAccion('');
    setExito('');
    setProcesando(incidente.id);

    try {
      await actualizarIncidente(incidente.id, estado, respuesta);
      setExito(`Incidente #${incidente.id} actualizado.`);
      incidentes.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setProcesando(null);
    }
  }

  return (
    <>
      <p className="nota-panel">
        Los reportes de los clientes llegan aquí. Al cambiar el estado o escribir una respuesta,
        el cliente recibe un correo con la actualización. Las emergencias aparecen resaltadas.
      </p>

      <div className="filtro-panel">
        <label htmlFor="filtro-incidentes">Mostrar</label>
        <select
          id="filtro-incidentes"
          value={filtro}
          onChange={(evento) => setFiltro(evento.target.value)}
        >
          {FILTROS.map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </div>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      <EstadoCarga
        cargando={incidentes.cargando && !incidentes.datos}
        error={incidentes.error}
        onReintentar={incidentes.recargar}
        texto="Cargando incidentes…"
      />

      {incidentes.datos && !incidentes.error && (
        lista.length === 0 ? (
          <p className="sin-resultados">No hay incidentes con ese estado.</p>
        ) : (
          <div className="panel-lista">
            {lista.map((incidente) => (
              <TarjetaIncidente
                key={incidente.id}
                incidente={incidente}
                ocupado={procesando === incidente.id}
                onGuardar={(estado, respuesta) => guardar(incidente, estado, respuesta)}
              />
            ))}
          </div>
        )
      )}
    </>
  );
}

export default PanelIncidentes;