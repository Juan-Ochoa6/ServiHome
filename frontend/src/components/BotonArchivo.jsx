import { useState } from 'react';
import { abrirArchivoProtegido } from '../services/api.js';

// Abre en una pestaña nueva un archivo que exige sesión (documentos, comprobantes).
// "ruta" es la del backend, por ejemplo /api/pagos/3/factura/
function BotonArchivo({ ruta, children = 'Ver archivo', className = 'boton-enlace' }) {
  const [abriendo, setAbriendo] = useState(false);
  const [error, setError] = useState('');

  async function abrir() {
    setError('');
    setAbriendo(true);

    try {
      await abrirArchivoProtegido(ruta);
    } catch (err) {
      setError(err.message);
    } finally {
      setAbriendo(false);
    }
  }

  return (
    <>
      <button type="button" className={className} onClick={abrir} disabled={abriendo}>
        {abriendo ? 'Abriendo…' : children}
      </button>
      {error && (
        <span className="error-campo" role="alert">
          {error}
        </span>
      )}
    </>
  );
}

export default BotonArchivo;