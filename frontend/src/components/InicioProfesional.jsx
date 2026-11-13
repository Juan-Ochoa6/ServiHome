import { Link } from 'react-router-dom';
import { obtenerMiVerificacion } from '../services/cuenta.js';
import { listarSolicitudes } from '../services/catalogo.js';
import { listarMisOfertas } from '../services/profesional.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';
import { formatearFecha } from '../utils/formato.js';
import { etiquetaVerificacion } from '../utils/verificacion.js';
import EstadoCarga from './EstadoCarga.jsx';
import Mensaje from './Mensaje.jsx';

const PASO_POR_ESTADO = {
  pendiente: 'Negocia el precio o responde',
  aceptada: 'Inicia el servicio con el código del cliente',
  en_proceso: 'Complétalo con el código del cliente',
};

// Solo se muestra con el perfil aprobado: el backend rechaza estas consultas si no.
function ResumenProfesional({ verificacion }) {
  const solicitudes = useCargar(listarSolicitudes);
  const ofertas = useCargar(listarMisOfertas);

  const lista = solicitudes.datos ?? [];
  const contar = (estado) => lista.filter((item) => item.estado === estado).length;

  const atencion = lista
    .filter((item) => PASO_POR_ESTADO[item.estado])
    .sort((a, b) => new Date(a.fecha_solicitada) - new Date(b.fecha_solicitada))
    .slice(0, 5);

  const misOfertas = ofertas.datos ?? [];
  const ofertasPorAprobar = misOfertas.filter(
    (oferta) => oferta.estado_aprobacion === 'pendiente',
  ).length;

  return (
    <>
      {verificacion.estado_identidad !== 'aprobado' && (
        <Mensaje tipo="info">
          Tu identidad aún no está verificada.{' '}
          <Link to="/mi-cuenta">Sube tu documento de identidad</Link> para poder ofrecer servicios.
        </Mensaje>
      )}

      <EstadoCarga
        cargando={solicitudes.cargando && !solicitudes.datos}
        error={solicitudes.error}
        onReintentar={solicitudes.recargar}
        texto="Cargando tu resumen…"
      />

      {solicitudes.datos && !solicitudes.error && (
        <>
          <div className="tablero">
            <Link className="dato-tablero" to="/mi-cuenta">
              <span>Disponibilidad</span>
              <strong>{verificacion.disponible ? 'Disponible' : 'En pausa'}</strong>
              <span>Cámbiala en Mi cuenta</span>
            </Link>
            <Link className="dato-tablero" to="/solicitudes">
              <span>Por responder</span>
              <strong>{contar('pendiente')}</strong>
              <span>solicitudes pendientes</span>
            </Link>
            <Link className="dato-tablero" to="/solicitudes">
              <span>Por iniciar</span>
              <strong>{contar('aceptada')}</strong>
              <span>con precio acordado</span>
            </Link>
            <Link className="dato-tablero" to="/solicitudes">
              <span>En proceso</span>
              <strong>{contar('en_proceso')}</strong>
              <span>servicios en curso</span>
            </Link>
            <Link className="dato-tablero" to="/mis-servicios">
              <span>Mis servicios</span>
              <strong>{misOfertas.length}</strong>
              <span>
                {ofertasPorAprobar > 0 ? `${ofertasPorAprobar} por aprobar` : 'publicados'}
              </span>
            </Link>
          </div>

          <h3 className="titulo-tablero">Requiere tu atención</h3>
          {atencion.length === 0 ? (
            <p className="sin-resultados">No tienes solicitudes pendientes por ahora.</p>
          ) : (
            <ul className="lista-atencion">
              {atencion.map((solicitud) => (
                <li key={solicitud.id}>
                  <div>
                    <strong>{solicitud.servicio_nombre}</strong>
                    <span className="solicitud-meta">
                      Cliente: {solicitud.cliente_nombre} · {formatearFecha(solicitud.fecha_solicitada)}
                    </span>
                    <span className="solicitud-meta">{PASO_POR_ESTADO[solicitud.estado]}</span>
                  </div>
                  <Link className="boton-secundario" to="/solicitudes">
                    Abrir
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </>
  );
}

function InicioProfesional() {
  const { sesion } = useAuth();
  const verificacion = useCargar(obtenerMiVerificacion);
  const datos = verificacion.datos;
  const aprobado = datos?.estado_verificacion === 'aprobado';

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">TU ESPACIO DE TRABAJO</span>
        <h2>Hola, {sesion?.usuario}</h2>
        <p>Aquí ves el estado de tu perfil y lo que necesita tu atención.</p>
      </div>

      <EstadoCarga
        cargando={verificacion.cargando && !datos}
        error={verificacion.error}
        onReintentar={verificacion.recargar}
        texto="Cargando tu perfil…"
      />

      {datos && !verificacion.error && (
        aprobado ? (
          <ResumenProfesional verificacion={datos} />
        ) : (
          <div className="bloque-cuenta">
            <h3>Tu perfil está en revisión</h3>
            <p>
              Estado actual: <strong>{etiquetaVerificacion(datos.estado_verificacion)}</strong>.
              Cuando un administrador apruebe tu perfil podrás recibir solicitudes y publicar tus
              servicios.
            </p>
            <div className="solicitud-acciones">
              <Link className="boton-secundario" to="/mi-cuenta">Ver mi cuenta</Link>
            </div>
          </div>
        )
      )}
    </section>
  );
}

export default InicioProfesional;