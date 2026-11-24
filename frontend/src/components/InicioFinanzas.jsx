
import { Link } from 'react-router-dom';
import { useAuth } from '../auth/useAuth.js';

function InicioFinanzas() {
  const { sesion } = useAuth();

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">FINANZAS</span>
        <h2>Hola, {sesion?.usuario}</h2>
        <p>
          Consulta los ingresos, las comisiones de ServiHome
          y las estadísticas generales de la plataforma.
        </p>
      </div>

      <div className="solicitud-acciones">
        <Link className="boton-contactar" to="/finanzas">
          Ir al panel financiero
        </Link>
      </div>
    </section>
  );
}

export default InicioFinanzas;
