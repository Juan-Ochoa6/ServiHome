import { useState } from 'react';
import { cambiarEstadoSolicitud } from '../services/catalogo.js';
import Mensaje from './Mensaje.jsx';

// Cliente: ve el código y se lo entrega al profesional.
// Profesional: escribe el código que le da el cliente para iniciar o completar.
function CodigoServicio({ solicitud, esCliente, onCambio }) {
  const [codigo, setCodigo] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  const enInicio = solicitud.estado === 'aceptada';
  const nombre = enInicio ? 'inicio' : 'finalización';
  const codigoCliente = enInicio ? solicitud.codigo_inicio : solicitud.codigo_finalizacion;
  const siguiente = enInicio ? 'en_proceso' : 'completada';

  async function validar(evento) {
    evento.preventDefault();
    setError('');
    setEnviando(true);

    try {
      await cambiarEstadoSolicitud(solicitud.id, siguiente, codigo.trim());
      setCodigo('');
      onCambio();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  if (esCliente) {
    return (
      <div className="subbloque">
        <h4>Código de {nombre}</h4>
        {codigoCliente ? (
          <>
            <span className="codigo-servicio">{codigoCliente}</span>
            <p>
              {enInicio
                ? 'Entrégaselo al profesional cuando llegue a tu domicilio. Con este código se confirma que el servicio comenzó.'
                : 'Entrégaselo al profesional cuando el servicio esté terminado. Con este código se marca como completado.'}
            </p>
          </>
        ) : (
          <p>Este servicio todavía no tiene un código de {nombre}.</p>
        )}
      </div>
    );
  }

  return (
    <form className="subbloque" onSubmit={validar}>
      <h4>{enInicio ? 'Iniciar el servicio' : 'Completar el servicio'}</h4>
      <p>
        {enInicio
          ? 'Pídele al cliente su código de inicio de 6 dígitos cuando llegues.'
          : 'Pídele al cliente su código de finalización de 6 dígitos cuando termines.'}
      </p>

      <div className="codigo-form">
        <input
          type="text"
          inputMode="numeric"
          autoComplete="off"
          maxLength={6}
          placeholder="000000"
          aria-label={`Código de ${nombre}`}
          value={codigo}
          onChange={(evento) => setCodigo(evento.target.value.replace(/\D/g, ''))}
        />
        <button
          type="submit"
          className="boton-contactar"
          disabled={enviando || codigo.length !== 6}
        >
          {enviando ? 'Validando…' : enInicio ? 'Iniciar servicio' : 'Completar servicio'}
        </button>
      </div>

      <Mensaje tipo="error">{error}</Mensaje>
    </form>
  );
}

export default CodigoServicio;