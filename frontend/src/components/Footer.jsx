import { Link } from 'react-router-dom';

// Para agregar un crédito nuevo, añade una línea a esta lista.
const CREDITOS = [
  {
    url: 'https://www.flaticon.es/icono-gratis/casa_532663',
    titulo: 'casa icono',
    texto: 'Icono de casa por Flaticon',
  },
  {
    url: 'https://www.flaticon.es/iconos-gratis/llave-inglesa',
    titulo: 'llave-inglesa iconos',
    texto: 'Llave-inglesa iconos creados por Magnific - Flaticon',
  },
  {
    url: 'https://www.flaticon.es/iconos-gratis/alto-voltaje',
    titulo: 'alto voltaje iconos',
    texto: 'Alto voltaje iconos creados por Muhammad Atif - Flaticon',
  },
  {
    url: 'https://www.flaticon.es/iconos-gratis/parasito',
    titulo: 'parásito iconos',
    texto: 'Parásito iconos creados por Pixelmeetup - Flaticon',
  },
  {
    url: 'https://www.flaticon.es/iconos-gratis/buscar',
    titulo: 'buscar iconos',
    texto: 'Buscar iconos creados por Magnific - Flaticon',
  },
];

function Footer() {
  return (
    <footer className="footer">
      <Link className="logo" to="/">Servi<span>Home</span></Link>
      <p>Conectamos personas. Cuidamos hogares.</p>

      <div className="footer-legal">
        <p>© 2026 ServiHome · Proyecto académico</p>

        <ul className="footer-creditos" aria-label="Créditos de los iconos">
          {CREDITOS.map((credito) => (
            <li key={credito.url}>
              <a
                href={credito.url}
                title={credito.titulo}
                target="_blank"
                rel="noopener noreferrer"
              >
                {credito.texto}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}

export default Footer;