import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth.js';

function Navbar() {
  const { sesion, cerrarSesion } = useAuth();
  const navigate = useNavigate();

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
        <NavLink to="/" end>Inicio</NavLink>
        <NavLink to="/servicios">Servicios</NavLink>
        <NavLink to="/profesionales">Profesionales</NavLink>
        <NavLink to="/solicitudes">Solicitudes</NavLink>
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