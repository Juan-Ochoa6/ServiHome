import { useEffect, useRef, useState } from 'react';
import './App.css';

const categorias = [
  { nombre: 'Plomería', icono: '🔧' },
  { nombre: 'Electricidad', icono: '💡' },
  { nombre: 'Limpieza', icono: '🧹' },
  { nombre: 'Pintura', icono: '🎨' },
  { nombre: 'Jardinería', icono: '🌱' },
  { nombre: 'Reparaciones', icono: '🛠️' },
];

const profesionales = [
  {
    nombre: 'Carlos Rodríguez',
    oficio: 'Plomería',
    descripcion: 'Instalaciones y reparaciones de tuberías.',
    calificacion: '4.9',
    icono: '🔧',
  },
  {
    nombre: 'Laura Martínez',
    oficio: 'Electricidad',
    descripcion: 'Instalaciones eléctricas para tu hogar.',
    calificacion: '4.8',
    icono: '💡',
  },
  {
    nombre: 'Andrés Gómez',
    oficio: 'Limpieza',
    descripcion: 'Limpieza general y mantenimiento del hogar.',
    calificacion: '4.9',
    icono: '🧹',
  },
];

const solicitudInicial = {
  descripcion: '',
  direccion: '',
  fecha: '',
};

function App() {
  const [busqueda, setBusqueda] = useState('');
  const [profesionalSeleccionado, setProfesionalSeleccionado] = useState(null);
  const [vista, setVista] = useState('perfil');
  const [solicitud, setSolicitud] = useState(solicitudInicial);
  const [solicitudEnviada, setSolicitudEnviada] = useState(false);
  const contenidoRef = useRef(null);

  const profesionalesFiltrados = profesionales.filter((profesional) => {
    const termino = busqueda.trim().toLowerCase();
    return (
      profesional.oficio.toLowerCase().includes(termino) ||
      profesional.nombre.toLowerCase().includes(termino)
    );
  });

  useEffect(() => {
    if (profesionalSeleccionado && contenidoRef.current) {
      contenidoRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  }, [profesionalSeleccionado, vista, solicitudEnviada]);

  function seleccionarProfesional(profesional) {
    setProfesionalSeleccionado(profesional);
    setVista('perfil');
    setSolicitud(solicitudInicial);
    setSolicitudEnviada(false);
  }

  function volverAProfesionales() {
    setProfesionalSeleccionado(null);
    setVista('perfil');
    setSolicitud(solicitudInicial);
    setSolicitudEnviada(false);
  }

  function actualizarSolicitud(evento) {
    const { name, value } = evento.target;
    setSolicitud((actual) => ({ ...actual, [name]: value }));
  }

  function enviarSolicitud(evento) {
    evento.preventDefault();
    setSolicitudEnviada(true);
  }

  function abrirFormulario() {
    setSolicitud(solicitudInicial);
    setSolicitudEnviada(false);
    setVista('formulario');
  }

  return (
    <div className="pagina">
      <header className="navbar">
        <a className="logo" href="#inicio" onClick={volverAProfesionales}>
          Servi<span>Home</span>
        </a>

        <nav className="menu" aria-label="Navegación principal">
          <a href="#inicio" onClick={volverAProfesionales}>Inicio</a>
          <a href="#categorias" onClick={volverAProfesionales}>Servicios</a>
          <a href="#profesionales" onClick={volverAProfesionales}>Profesionales</a>
        </nav>

        <button
          type="button"
          className="boton-secundario"
          onClick={() => window.alert('El inicio de sesión se implementará más adelante.')}
        >
          Iniciar sesión
        </button>
      </header>

      <main>
        <section className="hero" id="inicio">
          <div className="hero-contenido">
            <span className="etiqueta">TU HOGAR, EN BUENAS MANOS</span>
            <h1>Encuentra al profesional ideal para tu hogar</h1>
            <p>
              Conecta con profesionales independientes, solicita servicios y
              organiza las tareas de tu hogar en un solo lugar.
            </p>

            <form
              className="buscador"
              onSubmit={(evento) => {
                evento.preventDefault();
                document.getElementById('profesionales')?.scrollIntoView({
                  behavior: 'smooth',
                  block: 'start',
                });
              }}
            >
              <span aria-hidden="true">🔎</span>
              <input
                type="search"
                placeholder="¿Qué servicio necesitas?"
                aria-label="Buscar profesionales por oficio o nombre"
                value={busqueda}
                onChange={(evento) => setBusqueda(evento.target.value)}
              />
              <button type="submit">Buscar</button>
            </form>
            <p className="nota-buscador">Encuentra ayuda para las tareas de tu hogar.</p>
          </div>

          <div className="hero-ilustracion" aria-hidden="true">
            <div className="circulo"><span>🏡</span></div>
            <div className="burbuja burbuja-uno">🔧</div>
            <div className="burbuja burbuja-dos">✨</div>
            <div className="burbuja burbuja-tres">🪴</div>
          </div>
        </section>

        <section className="seccion" id="categorias">
          <div className="encabezado-seccion">
            <span className="etiqueta">NUESTROS SERVICIOS</span>
            <h2>¿Qué necesitas para tu hogar?</h2>
            <p>Explora algunas de nuestras categorías.</p>
          </div>

          <div className="categorias-grid">
            {categorias.map((categoria) => (
              <button
                type="button"
                className="categoria"
                key={categoria.nombre}
                onClick={() => {
                  setBusqueda(categoria.nombre);
                  document.getElementById('profesionales')?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                  });
                }}
              >
                <span className="categoria-icono">{categoria.icono}</span>
                <span>{categoria.nombre}</span>
                <span className="flecha" aria-hidden="true">↗</span>
              </button>
            ))}
          </div>
        </section>

        <section className="seccion profesionales" id="profesionales">
          <div className="encabezado-seccion">
            <span className="etiqueta">PERSONAS QUE TE AYUDAN</span>
            <h2>{busqueda ? `Resultados para "${busqueda}"` : 'Profesionales destacados'}</h2>
            <p>Conoce algunas de las personas que pueden ayudarte.</p>
          </div>

          <div className="profesionales-grid">
            {profesionalesFiltrados.map((profesional) => (
              <article className="tarjeta-profesional" key={profesional.nombre}>
                <div className="profesional-avatar">{profesional.icono}</div>
                <div className="profesional-info">
                  <span className="oficio">{profesional.oficio}</span>
                  <h3>{profesional.nombre}</h3>
                  <p>{profesional.descripcion}</p>
                  <div className="calificacion">⭐ {profesional.calificacion}</div>
                  <button
                    type="button"
                    className="boton-contactar"
                    onClick={() => seleccionarProfesional(profesional)}
                  >
                    Ver profesional
                  </button>
                </div>
              </article>
            ))}

            {profesionalesFiltrados.length === 0 && (
              <p className="sin-resultados">
                No encontramos profesionales con ese nombre u oficio. Prueba con otra búsqueda.
              </p>
            )}
          </div>
        </section>

        {profesionalSeleccionado && (
          <section className="seccion panel-flujo" id="flujo-profesional" ref={contenidoRef}>
            {vista === 'perfil' && !solicitudEnviada && (
              <>
                <button type="button" className="boton-secundario boton-volver" onClick={volverAProfesionales}>
                  ← Volver a profesionales
                </button>
                <div className="perfil-contenido">
                  <div className="profesional-avatar perfil-avatar">{profesionalSeleccionado.icono}</div>
                  <span className="oficio">{profesionalSeleccionado.oficio}</span>
                  <h2>{profesionalSeleccionado.nombre}</h2>
                  <p>{profesionalSeleccionado.descripcion}</p>
                  <p className="perfil-calificacion">⭐ {profesionalSeleccionado.calificacion} / 5</p>
                  <button type="button" className="boton-contactar" onClick={abrirFormulario}>
                    Solicitar servicio
                  </button>
                </div>
              </>
            )}

            {vista === 'formulario' && !solicitudEnviada && (
              <div className="formulario-solicitud">
                <button type="button" className="boton-secundario boton-volver" onClick={() => setVista('perfil')}>
                  ← Volver al perfil
                </button>
                <div className="formulario-encabezado">
                  <span className="etiqueta">NUEVA SOLICITUD</span>
                  <h2>Solicitar servicio</h2>
                  <p>Cuéntanos qué necesitas y cuándo te gustaría recibir ayuda.</p>
                  <div className="profesional-elegido">
                    <span className="profesional-elegido-icono">{profesionalSeleccionado.icono}</span>
                    <div>
                      <strong>{profesionalSeleccionado.nombre}</strong>
                      <span>{profesionalSeleccionado.oficio}</span>
                    </div>
                  </div>
                </div>

                <form onSubmit={enviarSolicitud}>
                  <div className="campo-formulario">
                    <label htmlFor="descripcion">Descripción del servicio</label>
                    <textarea
                      id="descripcion"
                      name="descripcion"
                      value={solicitud.descripcion}
                      onChange={actualizarSolicitud}
                      placeholder="Ej. Necesito reparar una fuga de agua en la cocina."
                      rows={4}
                      maxLength={1000}
                      required
                    />
                  </div>

                  <div className="campo-formulario">
                    <label htmlFor="direccion">Dirección del servicio</label>
                    <input
                      id="direccion"
                      name="direccion"
                      type="text"
                      autoComplete="street-address"
                      value={solicitud.direccion}
                      onChange={actualizarSolicitud}
                      placeholder="Calle, número, barrio o apartamento"
                      maxLength={250}
                      required
                    />
                  </div>

                  <div className="campo-formulario">
                    <label htmlFor="fecha">Fecha y hora preferidas</label>
                    <input
                      id="fecha"
                      name="fecha"
                      type="datetime-local"
                      min={new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16)}
                      value={solicitud.fecha}
                      onChange={actualizarSolicitud}
                      required
                    />
                  </div>

                  <p className="aviso-local">
                    Esta es una demostración: los datos no se envían al backend ni se guardan permanentemente.
                  </p>

                  <button type="submit" className="boton-contactar">
                    Revisar solicitud
                  </button>
                </form>
              </div>
            )}

            {solicitudEnviada && (
              <div className="formulario-solicitud confirmacion-solicitud">
                <div className="confirmacion-icono" aria-hidden="true">✓</div>
                <span className="etiqueta">RESUMEN DE DEMOSTRACIÓN</span>
                <h2>¡Solicitud preparada!</h2>
                <p>
                  Estos son los datos que completaste para {profesionalSeleccionado.nombre}.
                </p>
                <dl className="resumen-solicitud">
                  <dt>Profesional</dt>
                  <dd>{profesionalSeleccionado.nombre}</dd>
                  <dt>Descripción</dt>
                  <dd>{solicitud.descripcion}</dd>
                  <dt>Dirección</dt>
                  <dd>{solicitud.direccion}</dd>
                  <dt>Fecha y hora</dt>
                  <dd>{solicitud.fecha.replace('T', ' ')}</dd>
                </dl>
                <p className="aviso-local">
                  La solicitud todavía no se ha enviado ni guardado en un servidor.
                </p>
                <div className="acciones-confirmacion">
                  <button type="button" className="boton-secundario" onClick={() => setSolicitudEnviada(false)}>
                    Editar datos
                  </button>
                  <button type="button" className="boton-contactar" onClick={volverAProfesionales}>
                    Volver a profesionales
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <a className="logo" href="#inicio" onClick={volverAProfesionales}>Servi<span>Home</span></a>
        <p>Conectamos personas. Cuidamos hogares.</p>
        <p>© 2026 ServiHome · Proyecto académico</p>
      </footer>
    </div>
  );
}

export default App;
