import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  listarDocumentosAdmin,
  listarOfertasPendientes,
  listarProfesionalesPendientes,
} from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';

function InicioAdmin() {
  const { sesion } = useAuth();

  const profesionales = useCargar(listarProfesionalesPendientes);
  const ofertas = useCargar(listarOfertasPendientes);
  const cargarDocumentos = useCallback(() => listarDocumentosAdmin('pendiente'), []);
  const documentos = useCargar(cargarDocumentos);

  const cantidad = (consulta) => (consulta.datos ? consulta.datos.length : '—');

  const listos = [documentos, profesionales, ofertas].every((consulta) => consulta.datos);
  const total = listos
    ? documentos.datos.length + profesionales.datos.length + ofertas.datos.length
    : null;

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">ADMINISTRACIÓN</span>
        <h2>Hola, {sesion?.usuario}</h2>
        <p>
          {total === 0
            ? 'Todo está al día: no hay nada pendiente de revisión.'
            : 'Esto es lo que está esperando tu revisión.'}
        </p>
      </div>

      <div className="tablero">
        <Link className="dato-tablero" to="/panel">
          <span>Documentos</span>
          <strong>{cantidad(documentos)}</strong>
          <span>por revisar</span>
        </Link>
        <Link className="dato-tablero" to="/panel">
          <span>Profesionales</span>
          <strong>{cantidad(profesionales)}</strong>
          <span>por aprobar</span>
        </Link>
        <Link className="dato-tablero" to="/panel">
          <span>Ofertas</span>
          <strong>{cantidad(ofertas)}</strong>
          <span>por aprobar</span>
        </Link>
      </div>

      <div className="solicitud-acciones">
        <Link className="boton-contactar" to="/panel">Ir al panel</Link>
      </div>
    </section>
  );
}

export default InicioAdmin;