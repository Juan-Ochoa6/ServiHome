import { useState } from 'react';
import { ErrorApi } from '../services/api.js';
import { listarServicios } from '../services/catalogo.js';
import {
  actualizarOferta,
  crearOferta,
  eliminarOferta,
  listarMisOfertas,
} from '../services/profesional.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPrecio } from '../utils/formato.js';
import Campo from '../components/Campo.jsx';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';

const ETIQUETAS_APROBACION = {
  pendiente: 'Pendiente de aprobación',
  aprobado: 'Aprobada',
  rechazado: 'Rechazada',
};

function primerMensaje(valor) {
  return Array.isArray(valor) ? valor[0] : (valor ?? '');
}

function MisServicios() {
  const ofertas = useCargar(listarMisOfertas);
  const servicios = useCargar(listarServicios);

  const [nuevo, setNuevo] = useState({ servicio: '', precio: '' });
  const [erroresNuevo, setErroresNuevo] = useState({});
  const [editando, setEditando] = useState(null);
  const [precioEdicion, setPrecioEdicion] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [errorAccion, setErrorAccion] = useState('');
  const [exito, setExito] = useState('');

  const misOfertas = ofertas.datos ?? [];
  // Servicios que todavía no ofrezco (el backend rechaza duplicados).
  const disponibles = (servicios.datos ?? []).filter(
    (servicio) => !misOfertas.some((oferta) => oferta.servicio === servicio.id),
  );

  function limpiarMensajes() {
    setErrorAccion('');
    setExito('');
    setErroresNuevo({});
  }

  function actualizarNuevo(evento) {
    const { name, value } = evento.target;
    setNuevo((actual) => ({ ...actual, [name]: value }));
  }

  async function agregar(evento) {
    evento.preventDefault();
    limpiarMensajes();
    setOcupado(true);

    try {
      await crearOferta(Number(nuevo.servicio), nuevo.precio.trim());
      setNuevo({ servicio: '', precio: '' });
      setExito('Oferta enviada. Se verá en el catálogo cuando un administrador la apruebe.');
      ofertas.recargar();
    } catch (err) {
      if (err instanceof ErrorApi && err.status === 400 && err.datos && typeof err.datos === 'object') {
        setErroresNuevo(err.datos);
      } else {
        setErrorAccion(err.message);
      }
    } finally {
      setOcupado(false);
    }
  }

  function empezarEdicion(oferta) {
    limpiarMensajes();
    setEditando(oferta.id);
    setPrecioEdicion(String(Number(oferta.precio)));
  }

  async function guardarPrecio(oferta) {
    if (oferta.estado_aprobacion === 'aprobado') {
      const aviso =
        'Al cambiar el precio, tu oferta volverá a revisión y dejará de verse en el catálogo hasta que la aprueben. ¿Continuar?';
      if (!window.confirm(aviso)) return;
    }

    limpiarMensajes();
    setOcupado(true);

    try {
      await actualizarOferta(oferta.id, { precio: precioEdicion.trim() });
      setEditando(null);
      setExito('Precio actualizado. Tu oferta quedó pendiente de aprobación.');
      ofertas.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setOcupado(false);
    }
  }

  async function eliminar(oferta) {
    if (!window.confirm(`¿Eliminar tu oferta "${oferta.servicio_nombre}"?`)) return;

    limpiarMensajes();
    setOcupado(true);

    try {
      await eliminarOferta(oferta.id);
      setExito('Oferta eliminada.');
      ofertas.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">MI TRABAJO</span>
        <h2>Mis servicios</h2>
        <p>Define qué servicios ofreces y a qué precio.</p>
      </div>

      <p className="ayuda-pagina">
        Para ofrecer servicios tu identidad debe estar aprobada. Cada oferta nueva o
        modificada pasa por la revisión de un administrador antes de aparecer en el catálogo.
      </p>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      <EstadoCarga
        cargando={servicios.cargando && !servicios.datos}
        error={servicios.error}
        onReintentar={servicios.recargar}
        texto="Cargando servicios…"
      />

      {servicios.datos && ofertas.datos && (
        disponibles.length === 0 ? (
          <p className="sin-resultados">Ya ofreces todos los servicios disponibles.</p>
        ) : (
          <form className="formulario-panel" onSubmit={agregar}>
            <h3>Ofrecer un servicio</h3>

            <Campo
              id="oferta-servicio"
              etiqueta="Servicio"
              error={primerMensaje(erroresNuevo.servicio)}
            >
              <select
                id="oferta-servicio"
                name="servicio"
                value={nuevo.servicio}
                onChange={actualizarNuevo}
                required
              >
                <option value="">Elige un servicio</option>
                {disponibles.map((servicio) => (
                  <option key={servicio.id} value={servicio.id}>
                    {servicio.categoria_nombre} · {servicio.nombre} (valor base{' '}
                    {formatearPrecio(servicio.precio_base)})
                  </option>
                ))}
              </select>
            </Campo>

            <Campo
              id="oferta-precio"
              etiqueta="Tu precio (COP)"
              error={primerMensaje(erroresNuevo.precio)}
            >
              <input
                id="oferta-precio"
                name="precio"
                type="number"
                min="1"
                step="1"
                inputMode="numeric"
                placeholder="Ej. 50000"
                value={nuevo.precio}
                onChange={actualizarNuevo}
                required
              />
            </Campo>

            <button type="submit" className="boton-contactar" disabled={ocupado}>
              {ocupado ? 'Enviando…' : 'Enviar oferta'}
            </button>
          </form>
        )
      )}

      <EstadoCarga
        cargando={ofertas.cargando && !ofertas.datos}
        error={ofertas.error}
        onReintentar={ofertas.recargar}
        texto="Cargando tus ofertas…"
      />

      {ofertas.datos && !ofertas.error && (
        misOfertas.length === 0 ? (
          <div className="solicitudes-vacio">
            <span aria-hidden="true" style={{ fontSize: '2.4rem' }}>🛠️</span>
            <p>Todavía no ofreces ningún servicio. Agrega el primero con el formulario de arriba.</p>
          </div>
        ) : (
          <div className="panel-lista">
            {misOfertas.map((oferta) => {
              const enEdicion = editando === oferta.id;

              return (
                <article className="tarjeta-panel" key={oferta.id}>
                  <div className="tarjeta-panel-cabecera">
                    <strong>{oferta.servicio_nombre}</strong>
                    <span
                      className={`estado-solicitud estado-verificacion-${oferta.estado_aprobacion}`}
                    >
                      {ETIQUETAS_APROBACION[oferta.estado_aprobacion] ?? oferta.estado_aprobacion}
                    </span>
                  </div>

                  {enEdicion ? (
                    <div className="propuesta-formulario">
                      <label htmlFor={`precio-${oferta.id}`}>Nuevo precio (COP)</label>
                      <div className="propuesta-campo">
                        <input
                          id={`precio-${oferta.id}`}
                          type="number"
                          min="1"
                          step="1"
                          inputMode="numeric"
                          value={precioEdicion}
                          onChange={(evento) => setPrecioEdicion(evento.target.value)}
                        />
                        <button
                          type="button"
                          className="boton-contactar"
                          disabled={ocupado}
                          onClick={() => guardarPrecio(oferta)}
                        >
                          Guardar
                        </button>
                        <button
                          type="button"
                          className="boton-secundario"
                          onClick={() => setEditando(null)}
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <span className="oferta-precio">{formatearPrecio(oferta.precio)}</span>
                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-secundario"
                          onClick={() => empezarEdicion(oferta)}
                        >
                          Cambiar precio
                        </button>
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          disabled={ocupado}
                          onClick={() => eliminar(oferta)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </>
                  )}
                </article>
              );
            })}
          </div>
        )
      )}
    </section>
  );
}

export default MisServicios;