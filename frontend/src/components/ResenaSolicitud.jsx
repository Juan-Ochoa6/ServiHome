import { useCallback, useState } from 'react';
import { crearResena, listarResenasProfesional } from '../services/catalogo.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha } from '../utils/formato.js';
import EstadoCarga from './EstadoCarga.jsx';
import Estrellas from './Estrellas.jsx';
import Mensaje from './Mensaje.jsx';

// Solo se muestra en solicitudes completadas.
function ResenaSolicitud({ solicitud, esCliente }) {
  const cargar = useCallback(
    () => listarResenasProfesional(solicitud.profesional),
    [solicitud.profesional],
  );
  const resenas = useCargar(cargar);

  const [calificacion, setCalificacion] = useState(5);
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');

  const existente = resenas.datos?.find((resena) => resena.solicitud === solicitud.id);

  async function enviar(evento) {
    evento.preventDefault();
    setError('');
    setEnviando(true);

    try {
      await crearResena(solicitud.id, calificacion, comentario.trim());
      setComentario('');
      resenas.recargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="subbloque">
      <h4>{esCliente ? 'Tu reseña' : 'Reseña del cliente'}</h4>

      <EstadoCarga
        cargando={resenas.cargando && !resenas.datos}
        error={resenas.error}
        onReintentar={resenas.recargar}
        texto="Cargando reseña…"
      />

      {resenas.datos && !resenas.error && (
        existente ? (
          <>
            <Estrellas valor={existente.calificacion} />
            {existente.comentario && <p>{existente.comentario}</p>}
            <span className="solicitud-meta">{formatearFecha(existente.fecha_creacion)}</span>
          </>
        ) : esCliente ? (
          <form className="formulario-resena" onSubmit={enviar}>
            <fieldset className="calificacion-campo">
              <legend>¿Cómo calificas el servicio?</legend>
              {[1, 2, 3, 4, 5].map((valor) => (
                <label key={valor} className={calificacion === valor ? 'activa' : ''}>
                  <input
                    type="radio"
                    name={`calificacion-${solicitud.id}`}
                    value={valor}
                    checked={calificacion === valor}
                    onChange={() => setCalificacion(valor)}
                  />
                  {valor} ★
                </label>
              ))}
            </fieldset>

            <textarea
              rows={3}
              maxLength={1000}
              placeholder="Cuéntanos cómo te fue (opcional)"
              aria-label="Comentario de la reseña"
              value={comentario}
              onChange={(evento) => setComentario(evento.target.value)}
            />

            <Mensaje tipo="error">{error}</Mensaje>

            <div className="solicitud-acciones">
              <button type="submit" className="boton-contactar" disabled={enviando}>
                {enviando ? 'Enviando…' : 'Enviar reseña'}
              </button>
            </div>
          </form>
        ) : (
          <p>El cliente aún no ha dejado una reseña.</p>
        )
      )}
    </div>
  );
}

export default ResenaSolicitud;