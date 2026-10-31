import imagenLlave from '../assets/llave.png';
import imagenElectrico from '../assets/electrico.png';
import { normalizar } from '../utils/formato.js';

const EMOJIS = [
  ['plomer', '🔧'],
  ['electric', '💡'],
  ['limpiez', '🧹'],
  ['pintur', '🎨'],
  ['jardin', '🌱'],
  ['reparac', '🛠️'],
];

const IMAGENES = [
  ['plomer', imagenLlave],
  ['electric', imagenElectrico],
];

// Muestra la imagen de la categoría si existe; si no, un emoji.
function IconoCategoria({ nombre = '' }) {
  const clave = normalizar(nombre);

  const imagen = IMAGENES.find(([prefijo]) => clave.includes(prefijo))?.[1];
  if (imagen) {
    return <img className="icono-categoria-img" src={imagen} alt="" />;
  }

  const emoji = EMOJIS.find(([prefijo]) => clave.includes(prefijo))?.[1] ?? '🏠';
  return <>{emoji}</>;
}

export default IconoCategoria;