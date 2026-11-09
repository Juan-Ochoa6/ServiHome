import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import imagenCasa from '../assets/casa.png';
import imagenLlave from '../assets/llave.png';
import imagenParasito from '../assets/parasito.png';
import imagenElectricidad from '../assets/electrico.png';
import imagenBuscar from '../assets/buscar.png';

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
          <span aria-hidden="true"><img className="icono-buscar" src={imagenBuscar} alt="" /></span>
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
        <div className="circulo">
          <img src={imagenCasa} alt="" />
        </div>
        <div className="burbuja burbuja-uno">
            <img src={imagenLlave} alt="" />
        </div>
        <div className="burbuja burbuja-dos">
            <img src={imagenElectricidad} alt="" />
        </div>
        <div className="burbuja burbuja-tres">
            <img src={imagenParasito} alt="" />
        </div>
      </div>
    </section>
  );
}

export default Inicio;