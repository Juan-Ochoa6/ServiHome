import { useState } from 'react';
import { crearIncidente } from '../services/catalogo.js';
import { TIPOS_INCIDENTE } from '../utils/etiquetas.js';
import Mensaje from './Mensaje.jsx';

// Solo para clientes. Con el servicio en proceso se muestra como botón de pánico.
function ReporteIncidente({ solicitud }) {
  const urgente = solicitud.estado === 'en_proceso';

  const [abierto, setAbierto] = useState(false);
  const [tipo, setTipo] = useState(urgente ? 'emergencia' : 'otro');
  const [descripcion, setDescripcion] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [enviado, setEnviado] = useState(false);

  async function enviar(evento) {
    evento.preventDefault();
    setError('');
    setEnviando(true);

    try {
      await crearIncidente({
        solicitud: solicitud.id,
        tipo,
        descripcion: descripcion.trim(),
      });
      setDescripcion('');
      setAbierto(false);
      setEnviado(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="incidente">
      {enviado && (
        <Mensaje tipo="exito">
          Incidente enviado. Un administrador lo revisará y recibirás su respuesta por correo.
        </Mensaje>
      )}

      {!abierto && (
        <div className="solicitud-acciones">
          <button
            type="button"
            className={urgente ? 'boton-panico' : 'boton-secundario boton-peligro'}
            onClick={() => {
              setEnviado(false);
              setAbierto(true);
            }}
          >
            {urgente ? 'Botón de pánico' : 'Reportar un incidente'}
          </button>
        </div>
      )}

      {abierto && (
        <form className="subbloque" onSubmit={enviar}>
          <h4>{urgente ? 'Reportar una emergencia' : 'Reportar un incidente'}</h4>

          {urgente && (
            <p className="aviso-emergencia">
              Si estás en peligro, llama de inmediato a la línea de emergencias{' '}
              <a href="tel:123">123</a>.
            </p>
          )}

          <div className="codigo-form">
            <select
              aria-label="Tipo de incidente"
              value={tipo}
              onChange={(evento) => setTipo(evento.target.value)}
            >
              {Object.entries(TIPOS_INCIDENTE).map(([valor, texto]) => (
                <option key={valor} value={valor}>
                  {texto}
                </option>
              ))}
            </select>
          </div>

          <textarea
            rows={4}
            maxLength={2000}
            placeholder="Describe lo que pasó"
            aria-label="Descripción del incidente"
            value={descripcion}
            onChange={(evento) => setDescripcion(evento.target.value)}
            required
          />

          <Mensaje tipo="error">{error}</Mensaje>

          <div className="solicitud-acciones">
            <button type="submit" className="boton-contactar" disabled={enviando}>
              {enviando ? 'Enviando…' : 'Enviar reporte'}
            </button>
            <button type="button" className="boton-secundario" onClick={() => setAbierto(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default ReporteIncidente;