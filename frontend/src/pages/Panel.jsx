import { useCallback, useState } from 'react';
import {
  cambiarEstadoDocumento,
  cambiarEstadoOferta,
  cambiarEstadoProfesional,
  listarDocumentosAdmin,
  listarOfertasPendientes,
  listarProfesionalesPendientes,
} from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha, formatearPrecio } from '../utils/formato.js';
import {
  ETIQUETAS_DOCUMENTO,
  TIPOS_DOCUMENTO,
  etiquetaVerificacion,
} from '../utils/verificacion.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';
import BotonDocumento from '../components/BotonDocumento.jsx';

function TarjetaDocumento({ documento, ocupado, onResolver }) {
  const [observacion, setObservacion] = useState(documento.observacion ?? '');
  const tipo = TIPOS_DOCUMENTO[documento.tipo] ?? documento.tipo;

  return (
    <article className="tarjeta-panel">
      <div className="tarjeta-panel-cabecera">
        <strong>{tipo}</strong>
        <span className={`estado-solicitud estado-verificacion-${documento.estado}`}>
          {ETIQUETAS_DOCUMENTO[documento.estado] ?? documento.estado}
        </span>
      </div>

      <dl className="datos-panel">
        <dt>Profesional</dt>
        <dd>{documento.username}</dd>
        <dt>Correo</dt>
        <dd>{documento.email || '—'}</dd>
        <dt>Subido</dt>
        <dd>{formatearFecha(documento.fecha_subida)}</dd>
      </dl>

      <div className="solicitud-acciones">
        <BotonDocumento documento={documento} className="boton-secundario">
          Abrir documento
        </BotonDocumento>
      </div>

      <div className="campo-formulario">
        <label htmlFor={`observacion-${documento.id}`}>Observación (opcional)</label>
        <input
          id={`observacion-${documento.id}`}
          type="text"
          placeholder="Ej. La foto está borrosa, súbela de nuevo."
          value={observacion}
          onChange={(evento) => setObservacion(evento.target.value)}
        />
      </div>

      <div className="solicitud-acciones">
        <button
          type="button"
          className="boton-contactar"
          disabled={ocupado}
          onClick={() => onResolver('aprobado', observacion.trim())}
        >
          {ocupado ? 'Procesando…' : 'Aprobar'}
        </button>
        <button
          type="button"
          className="boton-secundario boton-peligro"
          disabled={ocupado}
          onClick={() => onResolver('rechazado', observacion.trim())}
        >
          Rechazar
        </button>
      </div>
    </article>
  );
}

function Panel() {
  const [pestana, setPestana] = useState('documentos');
  const [filtroDocumentos, setFiltroDocumentos] = useState('pendiente');

  const profesionales = useCargar(listarProfesionalesPendientes);
  const ofertas = useCargar(listarOfertasPendientes);
  const cargarDocumentos = useCallback(
    () => listarDocumentosAdmin(filtroDocumentos),
    [filtroDocumentos],
  );
  const documentos = useCargar(cargarDocumentos);

  const [procesando, setProcesando] = useState(null);
  const [errorAccion, setErrorAccion] = useState('');
  const [exito, setExito] = useState('');

  async function ejecutar(clave, accion, confirmacion, mensajeExito) {
    if (!window.confirm(confirmacion)) return;

    setErrorAccion('');
    setExito('');
    setProcesando(clave);

    try {
      const respuesta = await accion();
      setExito(respuesta?.mensaje ?? mensajeExito ?? 'Cambio realizado.');
      // Un cambio en una pestaña puede afectar a las otras.
      profesionales.recargar();
      ofertas.recargar();
      documentos.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setProcesando(null);
    }
  }

  function resolverDocumento(documento, estado, observacion) {
    const verbo = estado === 'aprobado' ? 'Aprobar' : 'Rechazar';
    const tipo = TIPOS_DOCUMENTO[documento.tipo] ?? documento.tipo;
    let confirmacion = `¿${verbo} el documento "${tipo}" de ${documento.username}?`;

    if (documento.tipo === 'identidad') {
      confirmacion += ` Esto ${estado === 'aprobado' ? 'aprueba' : 'rechaza'} la identidad del profesional.`;
    }

    ejecutar(
      `doc-${documento.id}`,
      () => cambiarEstadoDocumento(documento.id, estado, observacion),
      confirmacion,
      'Documento actualizado.',
    );
  }

  const pestanas = [
    { id: 'documentos', texto: 'Documentos', total: documentos.datos?.length },
    { id: 'profesionales', texto: 'Profesionales', total: profesionales.datos?.length },
    { id: 'ofertas', texto: 'Ofertas', total: ofertas.datos?.length },
  ];

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">ADMINISTRACIÓN</span>
        <h2>Panel de administrador</h2>
        <p>Revisa y aprueba a los profesionales y los servicios que ofrecen.</p>
      </div>

      <p className="ayuda-pagina">
        Orden recomendado: primero revisa los documentos (la identidad aprobada habilita al
        profesional para ofrecer servicios), luego aprueba su perfil y, por último, sus ofertas.
      </p>

      <div className="pestanas" role="tablist" aria-label="Secciones del panel">
        {pestanas.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={pestana === item.id}
            className={`pestana ${pestana === item.id ? 'pestana-activa' : ''}`}
            onClick={() => setPestana(item.id)}
          >
            {item.texto}
            {item.total !== undefined ? ` (${item.total})` : ''}
          </button>
        ))}
      </div>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      {pestana === 'documentos' && (
        <>
          <div className="filtro-panel">
            <label htmlFor="filtro-documentos">Mostrar</label>
            <select
              id="filtro-documentos"
              value={filtroDocumentos}
              onChange={(evento) => setFiltroDocumentos(evento.target.value)}
            >
              <option value="pendiente">Pendientes</option>
              <option value="aprobado">Aprobados</option>
              <option value="rechazado">Rechazados</option>
              <option value="">Todos</option>
            </select>
          </div>

          <EstadoCarga
            cargando={documentos.cargando && !documentos.datos}
            error={documentos.error}
            onReintentar={documentos.recargar}
            texto="Cargando documentos…"
          />

          {documentos.datos && !documentos.error && (
            documentos.datos.length === 0 ? (
              <p className="sin-resultados">No hay documentos con ese estado.</p>
            ) : (
              <div className="panel-lista">
                {documentos.datos.map((documento) => (
                  <TarjetaDocumento
                    key={documento.id}
                    documento={documento}
                    ocupado={procesando === `doc-${documento.id}`}
                    onResolver={(estado, observacion) =>
                      resolverDocumento(documento, estado, observacion)
                    }
                  />
                ))}
              </div>
            )
          )}
        </>
      )}

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
                              `¿Aprobar el perfil de ${profesional.username}?`,
                            )
                          }
                        >
                          {ocupado ? 'Procesando…' : 'Aprobar perfil'}
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
                  const identidadAprobada = oferta.estado_identidad === 'aprobado';

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
                            className={`estado-solicitud estado-verificacion-${oferta.estado_identidad}`}
                          >
                            Identidad: {etiquetaVerificacion(oferta.estado_identidad)}
                          </span>
                        </dd>
                        <dt>Precio ofrecido</dt>
                        <dd>{formatearPrecio(oferta.precio)}</dd>
                      </dl>

                      {!identidadAprobada && (
                        <p className="solicitud-meta">
                          Para aprobar esta oferta, primero debe estar aprobada la identidad del
                          profesional.
                        </p>
                      )}

                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-contactar"
                          disabled={ocupado || !identidadAprobada}
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