import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="footer">
      <Link className="logo" to="/">Servi<span>Home</span></Link>
      <p>Conectamos personas. Cuidamos hogares.</p>
      <p>© 2026 ServiHome · Proyecto académico</p>
    </footer>
  );
}

export default Footer;