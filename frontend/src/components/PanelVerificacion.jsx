import { useState } from 'react';
import {
  cambiarDisponibilidad,
  obtenerMiVerificacion,
  subirDocumento,
} from '../services/cuenta.js';
import { useCargar } from '../hooks/useCargar.js';
import { formatearFecha } from '../utils/formato.js';
import {
  ETIQUETAS_DOCUMENTO,
  TIPOS_DOCUMENTO,
  etiquetaVerificacion,
} from '../utils/verificacion.js';
import BotonDocumento from './BotonDocumento.jsx';
import Campo from './Campo.jsx';
import EstadoCarga from './EstadoCarga.jsx';
import Mensaje from './Mensaje.jsx';

const MAX_MB = 5;
const MAX_BYTES = MAX_MB * 1024 * 1024;
const EXTENSIONES = ['.pdf', '.jpg', '.jpeg', '.png'];

function PanelVerificacion() {
  const verificacion = useCargar(obtenerMiVerificacion);

  const [tipo, setTipo] = useState('identidad');
  const [archivo, setArchivo] = useState(null);
  const [claveArchivo, setClaveArchivo] = useState(0);
  const [errorArchivo, setErrorArchivo] = useState('');
  const [subiendo, setSubiendo] = useState(false);
  const [cambiando, setCambiando] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState('');
  const [exito, setExito] = useState('');

  const datos = verificacion.datos;
  // Mientras el perfil no está aprobado, el backend devuelve solo el estado del perfil.
  const completo = Boolean(datos && Array.isArray(datos.documentos));
  const perfilAprobado = datos?.estado_verificacion === 'aprobado';

  function limpiarMensajes() {
    setErrorGeneral('');
    setErrorArchivo('');
    setExito('');
  }

  function elegirArchivo(evento) {
    const elegido = evento.target.files?.[0] ?? null;
    setErrorArchivo('');

    if (!elegido) {
      setArchivo(null);
      return;
    }

    const nombre = elegido.name.toLowerCase();

    if (!EXTENSIONES.some((extension) => nombre.endsWith(extension))) {
      setErrorArchivo('Solo se permiten archivos PDF, JPG o PNG.');
      setArchivo(null);
      evento.target.value = '';
      return;
    }

    if (elegido.size > MAX_BYTES) {
      setErrorArchivo(`El archivo pesa más de ${MAX_MB} MB.`);
      setArchivo(null);
      evento.target.value = '';
      return;
    }

    setArchivo(elegido);
  }

  async function subir(evento) {
    evento.preventDefault();
    limpiarMensajes();

    if (!archivo) {
      setErrorArchivo('Elige un archivo para subir.');
      return;
    }

    setSubiendo(true);

    const formulario = new FormData();
    formulario.append('tipo', tipo);
    formulario.append('archivo', archivo);

    try {
      await subirDocumento(formulario);
      setArchivo(null);
      setClaveArchivo((actual) => actual + 1); // limpia el campo de archivo
      setExito('Documento enviado. Un administrador lo revisará.');
      verificacion.recargar();
    } catch (err) {
      setErrorGeneral(err.message);
    } finally {
      setSubiendo(false);
    }
  }

  async function alternarDisponibilidad() {
    limpiarMensajes();
    setCambiando(true);

    try {
      const respuesta = await cambiarDisponibilidad(!datos.disponible);
      setExito(respuesta.mensaje);
      verificacion.recargar();
    } catch (err) {
      setErrorGeneral(err.message);
    } finally {
      setCambiando(false);
    }
  }

  return (
    <>
      <EstadoCarga
        cargando={verificacion.cargando && !datos}
        error={verificacion.error}
        onReintentar={verificacion.recargar}
        texto="Cargando tu verificación…"
      />

      {datos && !verificacion.error && !completo && (
        <div className="bloque-cuenta">
          <h3>Verificación y disponibilidad</h3>

          <div className="estado-linea">
            <span>Aprobación del perfil</span>
            <span className={`estado-solicitud estado-verificacion-${datos.estado_verificacion}`}>
              {etiquetaVerificacion(datos.estado_verificacion)}
            </span>
          </div>

          <p>
            Tu perfil está pendiente de aprobación por un administrador. Cuando lo aprueben
            podrás subir tus documentos y ofrecer servicios.
          </p>
        </div>
      )}

      {completo && !verificacion.error && (
        <>
          <div className="bloque-cuenta">
            <h3>Verificación y disponibilidad</h3>

            <div className="estado-linea">
              <span>Identidad</span>
              <span className={`estado-solicitud estado-verificacion-${datos.estado_identidad}`}>
                {etiquetaVerificacion(datos.estado_identidad)}
              </span>
            </div>
            <div className="estado-linea">
              <span>Aprobación del perfil</span>
              <span className={`estado-solicitud estado-verificacion-${datos.estado_verificacion}`}>
                {etiquetaVerificacion(datos.estado_verificacion)}
              </span>
            </div>
            <div className="estado-linea">
              <span>Disponibilidad</span>
              <span
                className={`estado-solicitud ${
                  datos.disponible ? 'estado-verificacion-aprobado' : 'estado-verificacion-no_aplica'
                }`}
              >
                {datos.disponible ? 'Disponible' : 'En pausa'}
              </span>
            </div>

            <div className="solicitud-acciones">
              <button
                type="button"
                className={datos.disponible ? 'boton-secundario' : 'boton-contactar'}
                disabled={!perfilAprobado || cambiando}
                onClick={alternarDisponibilidad}
              >
                {cambiando
                  ? 'Guardando…'
                  : datos.disponible
                    ? 'Pausar disponibilidad'
                    : 'Activar disponibilidad'}
              </button>
            </div>

            {!perfilAprobado && (
              <p>
                Podrás activar tu disponibilidad cuando un administrador apruebe tu perfil.
              </p>
            )}

            <ol className="pasos-verificacion">
              <li>Sube tu documento de identidad.</li>
              <li>Un administrador revisa tus documentos y aprueba tu identidad y tu perfil.</li>
              <li>Al aprobar tu perfil quedas disponible; puedes pausarlo cuando quieras.</li>
              <li>Publica tus servicios en &quot;Mis servicios&quot;.</li>
            </ol>
          </div>

          <div className="bloque-cuenta">
            <h3>Mis documentos</h3>

            {datos.documentos.length === 0 ? (
              <p>Todavía no has subido documentos.</p>
            ) : (
              <ul className="documentos-lista">
                {datos.documentos.map((documento) => (
                  <li className="documento-item" key={documento.id}>
                    <div className="documento-info">
                      <strong>{TIPOS_DOCUMENTO[documento.tipo] ?? documento.tipo}</strong>
                      <span className="solicitud-meta">
                        Subido el {formatearFecha(documento.fecha_subida)}
                      </span>
                      <BotonDocumento documento={documento} />
                      {documento.observacion && (
                        <span className="documento-obs">Observación: {documento.observacion}</span>
                      )}
                    </div>
                    <span
                      className={`estado-solicitud estado-verificacion-${documento.estado}`}
                    >
                      {ETIQUETAS_DOCUMENTO[documento.estado] ?? documento.estado}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <form className="formulario-panel" onSubmit={subir}>
            <h3>Subir un documento</h3>

            <Campo id="documento-tipo" etiqueta="Tipo de documento">
              <select
                id="documento-tipo"
                value={tipo}
                onChange={(evento) => setTipo(evento.target.value)}
              >
                {Object.entries(TIPOS_DOCUMENTO).map(([valor, texto]) => (
                  <option key={valor} value={valor}>
                    {texto}
                  </option>
                ))}
              </select>
            </Campo>

            <Campo
              id="documento-archivo"
              etiqueta={`Archivo (PDF, JPG o PNG, máximo ${MAX_MB} MB)`}
              error={errorArchivo}
            >
              <input
                key={claveArchivo}
                id="documento-archivo"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={elegirArchivo}
              />
            </Campo>

            <Mensaje tipo="exito">{exito}</Mensaje>
            <Mensaje tipo="error">{errorGeneral}</Mensaje>

            <button type="submit" className="boton-contactar" disabled={subiendo}>
              {subiendo ? 'Subiendo…' : 'Subir documento'}
            </button>
          </form>
        </>
      )}
    </>
  );
}

export default PanelVerificacion;