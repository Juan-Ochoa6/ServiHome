import { useState } from 'react';
import {
  cambiarEstadoOferta,
  cambiarEstadoProfesional,
  listarOfertasPendientes,
  listarProfesionalesPendientes,
} from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPrecio } from '../utils/formato.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';

const ETIQUETAS_VERIFICACION = {
  pendiente: 'Pendiente de revisión',
  en_revision: 'En revisión',
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
};

function etiquetaVerificacion(estado) {
  return ETIQUETAS_VERIFICACION[estado] ?? estado;
}

function Panel() {
  const [pestana, setPestana] = useState('profesionales');
  const profesionales = useCargar(listarProfesionalesPendientes);
  const ofertas = useCargar(listarOfertasPendientes);

  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');
  const [exito, setExito] = useState('');

  async function ejecutar(clave, accion, confirmacion) {
    if (!window.confirm(confirmacion)) return;

    setErrorAccion('');
    setExito('');
    setProcesando(clave);

    try {
      const respuesta = await accion();
      setExito(respuesta?.mensaje ?? 'Cambio realizado.');
      // Aprobar o rechazar a un profesional también afecta a sus ofertas.
      profesionales.recargar();
      ofertas.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setProcesando(null);
    }
  }

  const totalProfesionales = profesionales.datos?.length;
  const totalOfertas = ofertas.datos?.length;

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">ADMINISTRACIÓN</span>
        <h2>Panel de administrador</h2>
        <p>Revisa y aprueba a los profesionales y los servicios que ofrecen.</p>
      </div>

      <div className="pestanas" role="tablist" aria-label="Secciones del panel">
        <button
          type="button"
          role="tab"
          aria-selected={pestana === 'profesionales'}
          className={`pestana ${pestana === 'profesionales' ? 'pestana-activa' : ''}`}
          onClick={() => setPestana('profesionales')}
        >
          Profesionales{totalProfesionales !== undefined ? ` (${totalProfesionales})` : ''}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={pestana === 'ofertas'}
          className={`pestana ${pestana === 'ofertas' ? 'pestana-activa' : ''}`}
          onClick={() => setPestana('ofertas')}
        >
          Ofertas{totalOfertas !== undefined ? ` (${totalOfertas})` : ''}
        </button>
      </div>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      {pestana === 'profesionales' && (
        <>
          <EstadoCarga
            cargando={profesionales.cargando && !profesionales.datos}
            error={profesionales.error}
            onReintentar={profesionales.recargar}
            texto="Cargando profesionales…"
          />

          {profesionales.datos && !profesionales.error && (
            profesionales.datos.length === 0 ? (
              <p className="sin-resultados">No hay profesionales pendientes de revisión.</p>
            ) : (
              <div className="panel-lista">
                {profesionales.datos.map((profesional) => {
                  const clave = `prof-${profesional.id}`;
                  const ocupado = procesando === clave;

                  return (
                    <article className="tarjeta-panel" key={profesional.id}>
                      <div className="tarjeta-panel-cabecera">
                        <strong>{profesional.username}</strong>
                        <span
                          className={`estado-solicitud estado-verificacion-${profesional.estado_verificacion}`}
                        >
                          {etiquetaVerificacion(profesional.estado_verificacion)}
                        </span>
                      </div>

                      <dl className="datos-panel">
                        <dt>Correo</dt>
                        <dd>{profesional.email || '—'}</dd>
                        <dt>Teléfono</dt>
                        <dd>{profesional.telefono || '—'}</dd>
                        <dt>Dirección</dt>
                        <dd>{profesional.direccion || '—'}</dd>
                        <dt>Experiencia</dt>
                        <dd>
                          {profesional.experiencia_anos}{' '}
                          {profesional.experiencia_anos === 1 ? 'año' : 'años'}
                        </dd>
                        <dt>Descripción</dt>
                        <dd>{profesional.descripcion_profesional || '—'}</dd>
                      </dl>

                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-contactar"
                          disabled={ocupado}
                          onClick={() =>
                            ejecutar(
                              clave,
                              () => cambiarEstadoProfesional(profesional.id, 'aprobado'),
                              `¿Aprobar a ${profesional.username}?`,
                            )
                          }
                        >
                          {ocupado ? 'Procesando…' : 'Aprobar'}
                        </button>
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          disabled={ocupado}
                          onClick={() =>
                            ejecutar(
                              clave,
                              () => cambiarEstadoProfesional(profesional.id, 'rechazado'),
                              `¿Rechazar a ${profesional.username}?`,
                            )
                          }
                        >
                          Rechazar
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )
          )}
        </>
      )}

      {pestana === 'ofertas' && (
        <>
          <EstadoCarga
            cargando={ofertas.cargando && !ofertas.datos}
            error={ofertas.error}
            onReintentar={ofertas.recargar}
            texto="Cargando ofertas…"
          />

          {ofertas.datos && !ofertas.error && (
            ofertas.datos.length === 0 ? (
              <p className="sin-resultados">No hay ofertas pendientes de aprobación.</p>
            ) : (
              <div className="panel-lista">
                {ofertas.datos.map((oferta) => {
                  const clave = `oferta-${oferta.id}`;
                  const ocupado = procesando === clave;
                  const profesionalAprobado = oferta.estado_profesional === 'aprobado';

                  return (
                    <article className="tarjeta-panel" key={oferta.id}>
                      <div className="tarjeta-panel-cabecera">
                        <strong>{oferta.servicio}</strong>
                        <span className="oficio">{oferta.categoria}</span>
                      </div>

                      <dl className="datos-panel">
                        <dt>Profesional</dt>
                        <dd>
                          {oferta.profesional}{' '}
                          <span
                            className={`estado-solicitud estado-verificacion-${oferta.estado_profesional}`}
                          >
                            {etiquetaVerificacion(oferta.estado_profesional)}
                          </span>
                        </dd>
                        <dt>Precio ofrecido</dt>
                        <dd>{formatearPrecio(oferta.precio)}</dd>
                      </dl>

                      {!profesionalAprobado && (
                        <p className="solicitud-meta">
                          Para aprobar esta oferta, primero debe estar aprobado el profesional.
                        </p>
                      )}

                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-contactar"
                          disabled={ocupado || !profesionalAprobado}
                          onClick={() =>
                            ejecutar(
                              clave,
                              () => cambiarEstadoOferta(oferta.id, 'aprobado'),
                              `¿Aprobar la oferta "${oferta.servicio}" de ${oferta.profesional}?`,
                            )
                          }
                        >
                          {ocupado ? 'Procesando…' : 'Aprobar'}
                        </button>
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          disabled={ocupado}
                          onClick={() =>
                            ejecutar(
                              clave,
                              () => cambiarEstadoOferta(oferta.id, 'rechazado'),
                              `¿Rechazar la oferta "${oferta.servicio}" de ${oferta.profesional}?`,
                            )
                          }
                        >
                          Rechazar
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )
          )}
        </>
      )}
    </section>
  );
}

export default Panel;