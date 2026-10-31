import { Link, NavLink } from 'react-router-dom';

function Navbar() {
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

      <button
        type="button"
        className="boton-secundario"
        onClick={() => window.alert('El inicio de sesión se implementará más adelante.')}
      >
        Iniciar sesión
      </button>
    </header>
  );
}

export default Navbar;