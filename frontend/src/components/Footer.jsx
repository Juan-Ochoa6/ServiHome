import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="footer">
      <Link className="logo" to="/">Servi<span>Home</span></Link>
      <p>Conectamos personas. Cuidamos hogares.</p>
      <p>
        © 2026 ServiHome · Proyecto académico · Icono de casa por{' '}
        <a
          href="https://www.flaticon.es/icono-gratis/casa_532663"
          target="_blank"
          rel="noopener noreferrer"
        >
          Flaticon
        </a>
        <br>
        </br>
        <a href="https://www.flaticon.es/iconos-gratis/llave-inglesa" title="llave-inglesa iconos">Llave-inglesa iconos creados por Magnific - Flaticon</a>
        <a href="https://www.flaticon.es/iconos-gratis/alto-voltaje" title="alto voltaje iconos">Alto voltaje iconos creados por Muhammad Atif - Flaticon</a>
        <a href="https://www.flaticon.es/iconos-gratis/parasito" title="parásito iconos">Parásito iconos creados por Pixelmeetup - Flaticon</a>
        <a href="https://www.flaticon.es/iconos-gratis/buscar" title="buscar iconos">Buscar iconos creados por Magnific - Flaticon</a>
      </p>
    </footer>
  );
}

export default Footer;