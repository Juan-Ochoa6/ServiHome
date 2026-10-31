import { useEffect, useState } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar.jsx';
import Footer from './components/Footer.jsx';
import Inicio from './pages/Inicio.jsx';
import Servicios from './pages/Servicios.jsx';
import Profesionales from './pages/Profesionales.jsx';
import PerfilProfesional from './pages/PerfilProfesional.jsx';
import Solicitudes from './pages/Solicitudes.jsx';
import NuevaSolicitud from './pages/NuevaSolicitud.jsx';

function App() {
  const [solicitudes, setSolicitudes] = useState([]);
  const { pathname } = useLocation();

  // Al cambiar de ventana, vuelve al inicio de la página
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [pathname]);

  function agregarSolicitud(solicitud) {
    setSolicitudes((actuales) => [solicitud, ...actuales]);
  }

  return (
    <div className="pagina">
      <Navbar />

      <main>
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/servicios" element={<Servicios />} />
          <Route path="/profesionales" element={<Profesionales />} />
          <Route path="/profesionales/:id" element={<PerfilProfesional />} />
          <Route path="/solicitudes" element={<Solicitudes solicitudes={solicitudes} />} />
          <Route
            path="/solicitudes/nueva/:id"
            element={<NuevaSolicitud agregarSolicitud={agregarSolicitud} />}
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