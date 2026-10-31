import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Inicio() {
  const [busqueda, setBusqueda] = useState('');
  const navigate = useNavigate();

  function buscar(evento) {
    evento.preventDefault();
    const termino = busqueda.trim();
    navigate(termino ? `/profesionales?buscar=${encodeURIComponent(termino)}` : '/profesionales');
  }

  return (
    <section className="hero">
      <div className="hero-contenido">
        <span className="etiqueta">TU HOGAR, EN BUENAS MANOS</span>
        <h1>Encuentra al profesional ideal para tu hogar</h1>
        <p>
          Conecta con profesionales independientes, solicita servicios y
          organiza las tareas de tu hogar en un solo lugar.
        </p>

        <form className="buscador" onSubmit={buscar}>
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
  );
}

export default Inicio;