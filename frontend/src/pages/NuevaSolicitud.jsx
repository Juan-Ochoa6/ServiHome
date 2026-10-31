import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ErrorApi } from '../services/api.js';
import { crearSolicitud, listarOfertas } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearPrecio } from '../utils/formato.js';
import EstadoCarga from '../components/EstadoCarga.jsx';
import IconoCategoria from '../components/IconoCategoria.jsx';
import Mensaje from '../components/Mensaje.jsx';

const solicitudInicial = {
  descripcion: '',
  direccion: '',
  fecha: '',
};

function calcularFechaMinima() {
  return new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}

// Junta los mensajes de validación que devuelve el backend.
function textoDeError(err) {
  if (err instanceof ErrorApi && err.status === 400 && err.datos && typeof err.datos === 'object') {
    const mensajes = Object.values(err.datos)
      .flat()
      .filter((mensaje) => typeof mensaje === 'string');
    if (mensajes.length > 0) return mensajes.join(' ');
  }
  return err.message;
}

// El parámetro :id de la ruta es el id de la OFERTA (profesional + servicio).
function NuevaSolicitud() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { datos, cargando, error, recargar } = useCargar(listarOfertas);

  const [solicitud, setSolicitud] = useState(solicitudInicial);
  const [enRevision, setEnRevision] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState('');
  const [fechaMinima] = useState(calcularFechaMinima);

  const oferta = datos?.find((item) => item.id === Number(id));

  if (cargando || error) {
    return (
      <section className="seccion panel-flujo">
        <Link className="boton-secundario boton-volver" to="/profesionales">
          ← Volver a profesionales
        </Link>
        <EstadoCarga
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          texto="Cargando…"
        />
      </section>
    );
  }

  if (!oferta) {
    return (
      <section className="seccion panel-flujo">
        <div className="encabezado-seccion">
          <h2>Servicio no encontrado</h2>
          <p>Elige un profesional y un servicio para crear tu solicitud.</p>
        </div>
        <Link className="boton-contactar" to="/profesionales">Ir a profesionales</Link>
      </section>
    );
  }

  function actualizarSolicitud(evento) {
    const { name, value } = evento.target;
    setSolicitud((actual) => ({ ...actual, [name]: value }));
  }

  function revisarSolicitud(evento) {
    evento.preventDefault();
    setErrorEnvio('');
    setEnRevision(true);
  }

  async function enviarSolicitud() {
    setErrorEnvio('');
    setEnviando(true);

    try {
      await crearSolicitud({
        profesional: oferta.profesional,
        servicio: oferta.servicio,
        descripcion: solicitud.descripcion.trim(),
        direccion_servicio: solicitud.direccion.trim(),
        fecha_solicitada: new Date(solicitud.fecha).toISOString(),
      });
      navigate('/solicitudes');
    } catch (err) {
      setErrorEnvio(textoDeError(err));
    } finally {
      setEnviando(false);
    }
  }

  if (enRevision) {
    return (
      <section className="seccion panel-flujo">
        <div className="formulario-solicitud confirmacion-solicitud">
          <span className="etiqueta">REVISA TU SOLICITUD</span>
          <h2>Confirma los datos</h2>
          <p>Al enviarla, quedará en estado Pendiente hasta que el profesional responda.</p>

          <dl className="resumen-solicitud">
            <dt>Profesional</dt>
            <dd>{oferta.profesional_nombre}</dd>
            <dt>Servicio</dt>
            <dd>{oferta.servicio_nombre}</dd>
            <dt>Valor del servicio</dt>
            <dd>{formatearPrecio(oferta.precio)}</dd>
            <dt>Descripción</dt>
            <dd>{solicitud.descripcion}</dd>
            <dt>Dirección</dt>
            <dd>{solicitud.direccion}</dd>
            <dt>Fecha y hora</dt>
            <dd>{solicitud.fecha.replace('T', ' ')}</dd>
          </dl>

          <Mensaje tipo="error">{errorEnvio}</Mensaje>

          <div className="acciones-confirmacion">
            <button
              type="button"
              className="boton-secundario"
              onClick={() => setEnRevision(false)}
              disabled={enviando}
            >
              Editar datos
            </button>
            <button
              type="button"
              className="boton-contactar"
              onClick={enviarSolicitud}
              disabled={enviando}
            >
              {enviando ? 'Enviando…' : 'Enviar solicitud'}
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="seccion panel-flujo">
      <div className="formulario-solicitud">
        <Link
          className="boton-secundario boton-volver"
          to={`/profesionales/${oferta.profesional}`}
        >
          ← Volver al perfil
        </Link>

        <div className="formulario-encabezado">
          <span className="etiqueta">NUEVA SOLICITUD</span>
          <h2>Solicitar servicio</h2>
          <p>Cuéntanos qué necesitas y cuándo te gustaría recibir ayuda.</p>
          <div className="profesional-elegido">
            <span className="profesional-elegido-icono">
              <IconoCategoria nombre={oferta.categoria_nombre} />
            </span>
            <div>
              <strong>{oferta.profesional_nombre}</strong>
              <span>{oferta.servicio_nombre} · {formatearPrecio(oferta.precio)}</span>
            </div>
          </div>
        </div>

        <form onSubmit={revisarSolicitud}>
          <div className="campo-formulario">
            <label htmlFor="descripcion">Descripción del servicio</label>
            <textarea
              id="descripcion"
              name="descripcion"
              value={solicitud.descripcion}
              onChange={actualizarSolicitud}
              placeholder="Ej. Necesito reparar una fuga de agua en la cocina."
              rows={4}
              maxLength={1000}
              required
            />
          </div>

          <div className="campo-formulario">
            <label htmlFor="direccion">Dirección del servicio</label>
            <input
              id="direccion"
              name="direccion"
              type="text"
              autoComplete="street-address"
              value={solicitud.direccion}
              onChange={actualizarSolicitud}
              placeholder="Calle, número, barrio o apartamento"
              maxLength={250}
              required
            />
          </div>

          <div className="campo-formulario">
            <label htmlFor="fecha">Fecha y hora preferidas</label>
            <input
              id="fecha"
              name="fecha"
              type="datetime-local"
              min={fechaMinima}
              value={solicitud.fecha}
              onChange={actualizarSolicitud}
              required
            />
          </div>

          <button type="submit" className="boton-contactar">
            Revisar solicitud
          </button>
        </form>
      </div>
    </section>
  );
}

export default NuevaSolicitud;