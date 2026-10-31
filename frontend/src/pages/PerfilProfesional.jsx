import { Link, useParams } from 'react-router-dom';
import { profesionales } from '../data/datos.js';

function PerfilProfesional() {
  const { id } = useParams();
  const profesional = profesionales.find((p) => p.id === Number(id));

  if (!profesional) {
    return (
      <section className="seccion panel-flujo">
        <div className="encabezado-seccion">
          <h2>Profesional no encontrado</h2>
          <p>Es posible que el perfil ya no esté disponible.</p>
        </div>
        <Link className="boton-contactar" to="/profesionales">Volver a profesionales</Link>
      </section>
    );
  }

  return (
    <section className="seccion panel-flujo">
      <Link className="boton-secundario boton-volver" to="/profesionales">
        ← Volver a profesionales
      </Link>

      <div className="perfil-contenido">
        <div className="profesional-avatar perfil-avatar">{profesional.icono}</div>
        <span className="oficio">{profesional.oficio}</span>
        <h2>{profesional.nombre}</h2>
        <p>{profesional.descripcion}</p>
        <p className="perfil-calificacion">⭐ {profesional.calificacion} / 5</p>
        <Link className="boton-contactar" to={`/solicitudes/nueva/${profesional.id}`}>
          Solicitar servicio
        </Link>
      </div>
    </section>
  );
}

export default PerfilProfesional;