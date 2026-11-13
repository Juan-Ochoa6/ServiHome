import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  listarDocumentosAdmin,
  listarIncidentes,
  listarOfertasPendientes,
  listarPagosAdmin,
  listarProfesionalesPendientes,
} from '../services/admin.js';
import { useCargar } from '../hooks/useCargar.js';
import { useAuth } from '../auth/useAuth.js';

const ABIERTO = (incidente) => ['pendiente', 'en_revision'].includes(incidente.estado);
const PENDIENTE = (elemento) => elemento.estado === 'pendiente';

function InicioAdmin() {
  const { sesion } = useAuth();

  const profesionales = useCargar(listarProfesionalesPendientes);
  const ofertas = useCargar(listarOfertasPendientes);
  const cargarDocumentos = useCallback(() => listarDocumentosAdmin('pendiente'), []);
  const documentos = useCargar(cargarDocumentos);
  const pagos = useCargar(listarPagosAdmin);
  const incidentes = useCargar(listarIncidentes);

  const contar = (consulta, predicado = () => true) =>
    consulta.datos ? consulta.datos.filter(predicado).length : null;

  const cantidades = {
    documentos: contar(documentos),
    profesionales: contar(profesionales),
    ofertas: contar(ofertas),
    pagos: contar(pagos, PENDIENTE),
    incidentes: contar(incidentes, ABIERTO),
  };

  const valores = Object.values(cantidades);
  const listos = valores.every((valor) => valor !== null);
  const total = listos ? valores.reduce((suma, valor) => suma + valor, 0) : null;
  const mostrar = (valor) => (valor === null ? '—' : valor);

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
        <Link className="dato-tablero" to="/panel?pestana=documentos">
          <span>Documentos</span>
          <strong>{mostrar(cantidades.documentos)}</strong>
          <span>por revisar</span>
        </Link>
        <Link className="dato-tablero" to="/panel?pestana=profesionales">
          <span>Profesionales</span>
          <strong>{mostrar(cantidades.profesionales)}</strong>
          <span>por aprobar</span>
        </Link>
        <Link className="dato-tablero" to="/panel?pestana=ofertas">
          <span>Ofertas</span>
          <strong>{mostrar(cantidades.ofertas)}</strong>
          <span>por aprobar</span>
        </Link>
        <Link className="dato-tablero" to="/panel?pestana=pagos">
          <span>Pagos</span>
          <strong>{mostrar(cantidades.pagos)}</strong>
          <span>por confirmar</span>
        </Link>
        <Link
          className={`dato-tablero ${cantidades.incidentes > 0 ? 'dato-alerta' : ''}`}
          to="/panel?pestana=incidentes"
        >
          <span>Incidentes</span>
          <strong>{mostrar(cantidades.incidentes)}</strong>
          <span>abiertos</span>
        </Link>
        <Link className="dato-tablero" to="/panel?pestana=finanzas">
          <span>Finanzas</span>
          <strong>$</strong>
          <span>ingresos y comisiones</span>
        </Link>
      </div>

      <div className="solicitud-acciones">
        <Link className="boton-contactar" to="/panel">Ir al panel</Link>
      </div>
    </section>
  );
}

export default InicioAdmin;