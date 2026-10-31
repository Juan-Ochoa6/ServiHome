import Cargando from './Cargando.jsx';
import Mensaje from './Mensaje.jsx';

function EstadoCarga({ cargando, error, onReintentar, texto }) {
  if (cargando) return <Cargando texto={texto} />;

  if (error) {
    return (
      <div className="bloque-error">
        <Mensaje tipo="error">{error}</Mensaje>
        {onReintentar && (
          <button type="button" className="boton-secundario" onClick={onReintentar}>
            Reintentar
          </button>
        )}
      </div>
    );
  }

  return null;
}

export default EstadoCarga;