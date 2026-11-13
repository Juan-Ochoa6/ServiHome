import BotonArchivo from './BotonArchivo.jsx';
import { rutaDescarga } from '../utils/verificacion.js';

function BotonDocumento({ documento, children = 'Ver archivo', className = 'boton-enlace' }) {
  return (
    <BotonArchivo ruta={rutaDescarga(documento)} className={className}>
      {children}
    </BotonArchivo>
  );
}

export default BotonDocumento;