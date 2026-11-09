import { useEffect } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import RutaProtegida from './auth/RutaProtegida.jsx';
import Inicio from './pages/Inicio.jsx';
import Servicios from './pages/Servicios.jsx';
import Profesionales from './pages/Profesionales.jsx';
import PerfilProfesional from './pages/PerfilProfesional.jsx';
import Solicitudes from './pages/Solicitudes.jsx';
import NuevaSolicitud from './pages/NuevaSolicitud.jsx';
import MisServicios from './pages/MisServicios.jsx';
import MiPortafolio from './pages/MiPortafolio.jsx';
import MiCuenta from './pages/MiCuenta.jsx';
import Panel from './pages/Panel.jsx';
import Login from './pages/Login.jsx';
import Registro from './pages/Registro.jsx';

// El catálogo es para visitantes, clientes y administradores; los profesionales
// vuelven a su inicio.
function Catalogo({ children }) {
  return (
    <RutaProtegida visitante roles={['cliente', 'administrador']}>
      {children}
    </RutaProtegida>
  );
}

function App() {
  const { pathname } = useLocation();

  // Al cambiar de ventana, vuelve al inicio de la página
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [pathname]);

  return (
    <div className="pagina">
      <Navbar />

      <main>
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/servicios" element={<Catalogo><Servicios /></Catalogo>} />
          <Route path="/profesionales" element={<Catalogo><Profesionales /></Catalogo>} />
          <Route
            path="/profesionales/:id"
            element={<Catalogo><PerfilProfesional /></Catalogo>}
          />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route
            path="/solicitudes"
            element={
              <RutaProtegida roles={['cliente', 'profesional']}>
                <Solicitudes />
              </RutaProtegida>
            }
          />
          <Route
            path="/solicitudes/nueva/:id"
            element={
              <RutaProtegida roles={['cliente']}>
                <NuevaSolicitud />
              </RutaProtegida>
            }
          />
          <Route
            path="/mis-servicios"
            element={
              <RutaProtegida roles={['profesional']}>
                <MisServicios />
              </RutaProtegida>
            }
          />
          <Route
            path="/mi-portafolio"
            element={
              <RutaProtegida roles={['profesional']}>
                <MiPortafolio />
              </RutaProtegida>
            }
          />
          <Route
            path="/mi-cuenta"
            element={
              <RutaProtegida roles={['cliente', 'profesional']}>
                <MiCuenta />
              </RutaProtegida>
            }
          />
          <Route
            path="/panel"
            element={
              <RutaProtegida roles={['administrador']}>
                <Panel />
              </RutaProtegida>
            }
          />
          <Route
            path="*"
            element={
              <section className="seccion">
                <div className="encabezado-seccion">
                  <span className="etiqueta">ERROR 404</span>
                  <h2>Página no encontrada</h2>
                  <p>La ventana que buscas no existe.</p>
                </div>
                <Link className="boton-contactar" to="/">Volver al inicio</Link>
              </section>
            }
          />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

export default App;