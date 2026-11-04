import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth.js';

const INICIO = { ruta: '/', texto: 'Inicio', exacto: true };
const SERVICIOS = { ruta: '/servicios', texto: 'Servicios' };
const PROFESIONALES = { ruta: '/profesionales', texto: 'Profesionales' };
const SOLICITUDES = { ruta: '/solicitudes', texto: 'Solicitudes' };
const PANEL = { ruta: '/panel', texto: 'Panel' };

const ENLACES_POR_ROL = {
  cliente: [INICIO, SERVICIOS, PROFESIONALES, SOLICITUDES],
  profesional: [INICIO, SOLICITUDES],
  administrador: [INICIO, SERVICIOS, PROFESIONALES, PANEL],
};

const ENLACES_PUBLICOS = [INICIO, SERVICIOS, PROFESIONALES, SOLICITUDES];

function Navbar() {
  const { sesion, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  const enlaces = (sesion && ENLACES_POR_ROL[sesion.rol]) || ENLACES_PUBLICOS;

  function salir() {
    cerrarSesion();
    navigate('/');
  }

  return (
    <header className="navbar">
      <Link className="logo" to="/">
        Servi<span>Home</span>
      </Link>

      <nav className="menu" aria-label="Navegación principal">
        {enlaces.map((enlace) => (
          <NavLink key={enlace.ruta} to={enlace.ruta} end={enlace.exacto}>
            {enlace.texto}
          </NavLink>
        ))}
      </nav>

      {sesion ? (
        <div className="navbar-sesion">
          <span>Hola, {sesion.usuario}</span>
          <button type="button" className="boton-secundario" onClick={salir}>
            Cerrar sesión
          </button>
        </div>
      ) : (
        <Link className="boton-secundario" to="/login">
          Iniciar sesión
        </Link>
      )}
    </header>
  );
}

export default Navbar;