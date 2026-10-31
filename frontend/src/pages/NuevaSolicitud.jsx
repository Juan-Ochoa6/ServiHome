import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { profesionales } from '../data/datos.js';

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

function NuevaSolicitud({ agregarSolicitud }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const profesional = profesionales.find((p) => p.id === Number(id));

  const [solicitud, setSolicitud] = useState(solicitudInicial);
  const [enRevision, setEnRevision] = useState(false);
  const [fechaMinima] = useState(calcularFechaMinima);

  if (!profesional) {
    return (
      <section className="seccion panel-flujo">
        <div className="encabezado-seccion">
          <h2>Profesional no encontrado</h2>
          <p>Elige un profesional para crear tu solicitud.</p>
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
    setEnRevision(true);
  }

  function guardarSolicitud() {
    agregarSolicitud({
      id: Date.now(),
      profesional: {
        id: profesional.id,
        nombre: profesional.nombre,
        oficio: profesional.oficio,
        icono: profesional.icono,
      },
      ...solicitud,
      estado: 'Pendiente',
    });
    navigate('/solicitudes');
  }

  if (enRevision) {
    return (
      <section className="seccion panel-flujo">
        <div className="formulario-solicitud confirmacion-solicitud">
          <div className="confirmacion-icono" aria-hidden="true">✓</div>
          <span className="etiqueta">RESUMEN DE DEMOSTRACIÓN</span>
          <h2>¡Solicitud preparada!</h2>
          <p>Estos son los datos que completaste para {profesional.nombre}.</p>

          <dl className="resumen-solicitud">
            <dt>Profesional</dt>
            <dd>{profesional.nombre}</dd>
            <dt>Descripción</dt>
            <dd>{solicitud.descripcion}</dd>
            <dt>Dirección</dt>
            <dd>{solicitud.direccion}</dd>
            <dt>Fecha y hora</dt>
            <dd>{solicitud.fecha.replace('T', ' ')}</dd>
          </dl>

          <p className="aviso-local">
            La solicitud todavía no se envía a un servidor; se guardará solo en esta sesión.
          </p>

          <div className="acciones-confirmacion">
            <button type="button" className="boton-secundario" onClick={() => setEnRevision(false)}>
              Editar datos
            </button>
            <button type="button" className="boton-contactar" onClick={guardarSolicitud}>
              Guardar solicitud
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
          to={`/profesionales/${profesional.id}`}
        >
          ← Volver al perfil
        </Link>

        <div className="formulario-encabezado">
          <span className="etiqueta">NUEVA SOLICITUD</span>
          <h2>Solicitar servicio</h2>
          <p>Cuéntanos qué necesitas y cuándo te gustaría recibir ayuda.</p>
          <div className="profesional-elegido">
            <span className="profesional-elegido-icono">{profesional.icono}</span>
            <div>
              <strong>{profesional.nombre}</strong>
              <span>{profesional.oficio}</span>
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

          <p className="aviso-local">
            Esta es una demostración: los datos no se envían al backend ni se guardan permanentemente.
          </p>

          <button type="submit" className="boton-contactar">
            Revisar solicitud
          </button>
        </form>
      </div>
    </section>
  );
}

export default NuevaSolicitud;