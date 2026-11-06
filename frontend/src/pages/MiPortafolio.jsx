import { useState } from 'react';
import { ErrorApi } from '../services/api.js';
import { listarServicios } from '../services/catalogo.js';
import {
  actualizarTrabajo,
  crearTrabajo,
  eliminarTrabajo,
  listarMiPortafolio,
} from '../services/profesional.js';
import { useCargar } from '../hooks/useCargar.js';
import Campo from '../components/Campo.jsx';
import EstadoCarga from '../components/EstadoCarga.jsx';
import Mensaje from '../components/Mensaje.jsx';

const MAX_MB = 5;
const MAX_BYTES = MAX_MB * 1024 * 1024;

function primerMensaje(valor) {
  return Array.isArray(valor) ? valor[0] : (valor ?? '');
}

// Formulario compartido para agregar y para editar un trabajo.
function FormularioTrabajo({
  idBase,
  inicial,
  servicios,
  imagenObligatoria,
  tituloFormulario,
  textoBoton,
  onGuardar,
  onCancelar,
}) {
  const [titulo, setTitulo] = useState(inicial.titulo);
  const [descripcion, setDescripcion] = useState(inicial.descripcion);
  const [servicio, setServicio] = useState(inicial.servicio);
  const [activo, setActivo] = useState(inicial.activo);
  const [imagen, setImagen] = useState(null);
  const [errores, setErrores] = useState({});
  const [errorGeneral, setErrorGeneral] = useState('');
  const [enviando, setEnviando] = useState(false);

  function elegirArchivo(evento) {
    const archivo = evento.target.files?.[0] ?? null;

    if (archivo && archivo.size > MAX_BYTES) {
      setErrores({ imagen: [`La imagen pesa más de ${MAX_MB} MB.`] });
      setImagen(null);
      evento.target.value = '';
      return;
    }

    setErrores({});
    setImagen(archivo);
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErrores({});
    setErrorGeneral('');
    setEnviando(true);

    const datos = new FormData();
    datos.append('titulo', titulo.trim());
    datos.append('descripcion', descripcion.trim());
    datos.append('servicio', servicio); // vacío = sin servicio asociado
    datos.append('activo', activo ? 'true' : 'false');
    if (imagen) datos.append('imagen', imagen);

    try {
      await onGuardar(datos);
    } catch (err) {
      if (err instanceof ErrorApi && err.status === 400 && err.datos && typeof err.datos === 'object') {
        setErrores(err.datos);
      } else {
        setErrorGeneral(err.message);
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="formulario-panel" onSubmit={enviar}>
      {tituloFormulario && <h3>{tituloFormulario}</h3>}

      <Campo id={`${idBase}-titulo`} etiqueta="Título" error={primerMensaje(errores.titulo)}>
        <input
          id={`${idBase}-titulo`}
          type="text"
          maxLength={150}
          value={titulo}
          onChange={(evento) => setTitulo(evento.target.value)}
          required
        />
      </Campo>

      <Campo
        id={`${idBase}-descripcion`}
        etiqueta="Descripción"
        error={primerMensaje(errores.descripcion)}
      >
        <textarea
          id={`${idBase}-descripcion`}
          rows={3}
          value={descripcion}
          onChange={(evento) => setDescripcion(evento.target.value)}
          required
        />
      </Campo>

      <Campo
        id={`${idBase}-servicio`}
        etiqueta="Servicio relacionado (opcional)"
        error={primerMensaje(errores.servicio)}
      >
        <select
          id={`${idBase}-servicio`}
          value={servicio}
          onChange={(evento) => setServicio(evento.target.value)}
        >
          <option value="">Sin servicio específico</option>
          {servicios.map((item) => (
            <option key={item.id} value={item.id}>
              {item.categoria_nombre} · {item.nombre}
            </option>
          ))}
        </select>
      </Campo>

      <Campo
        id={`${idBase}-imagen`}
        etiqueta={imagenObligatoria ? 'Foto del trabajo' : 'Cambiar foto (opcional)'}
        error={primerMensaje(errores.imagen)}
      >
        <input
          id={`${idBase}-imagen`}
          type="file"
          accept="image/*"
          onChange={elegirArchivo}
          required={imagenObligatoria}
        />
      </Campo>

      <label className="campo-check" htmlFor={`${idBase}-activo`}>
        <input
          id={`${idBase}-activo`}
          type="checkbox"
          checked={activo}
          onChange={(evento) => setActivo(evento.target.checked)}
        />
        Visible en mi perfil público
      </label>

      <Mensaje tipo="error">{errorGeneral}</Mensaje>

      <div className="solicitud-acciones">
        <button type="submit" className="boton-contactar" disabled={enviando}>
          {enviando ? 'Guardando…' : textoBoton}
        </button>
        {onCancelar && (
          <button type="button" className="boton-secundario" onClick={onCancelar}>
            Cancelar
          </button>
        )}
      </div>
    </form>
  );
}

const TRABAJO_VACIO = { titulo: '', descripcion: '', servicio: '', activo: true };

function MiPortafolio() {
  const trabajos = useCargar(listarMiPortafolio);
  const servicios = useCargar(listarServicios);

  const [editando, setEditando] = useState(null);
  const [claveFormulario, setClaveFormulario] = useState(0);
  const [ocupado, setOcupado] = useState(false);
  const [exito, setExito] = useState('');
  const [errorAccion, setErrorAccion] = useState('');

  async function agregar(datos) {
    await crearTrabajo(datos);
    setErrorAccion('');
    setExito('Trabajo agregado a tu portafolio.');
    setClaveFormulario((actual) => actual + 1); // limpia el formulario
    trabajos.recargar();
  }

  async function guardarEdicion(id, datos) {
    await actualizarTrabajo(id, datos);
    setErrorAccion('');
    setExito('Trabajo actualizado.');
    setEditando(null);
    trabajos.recargar();
  }

  async function eliminar(trabajo) {
    if (!window.confirm(`¿Eliminar "${trabajo.titulo}" de tu portafolio?`)) return;

    setExito('');
    setErrorAccion('');
    setOcupado(true);

    try {
      await eliminarTrabajo(trabajo.id);
      setExito('Trabajo eliminado.');
      trabajos.recargar();
    } catch (err) {
      setErrorAccion(err.message);
    } finally {
      setOcupado(false);
    }
  }

  const listaServicios = servicios.datos ?? [];
  const lista = trabajos.datos ?? [];

  return (
    <section className="seccion">
      <div className="encabezado-seccion">
        <span className="etiqueta">MI TRABAJO</span>
        <h2>Mi portafolio</h2>
        <p>Muestra fotos de tus trabajos anteriores. Se ven en tu perfil público.</p>
      </div>

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorAccion}</Mensaje>

      <FormularioTrabajo
        key={claveFormulario}
        idBase="nuevo"
        inicial={TRABAJO_VACIO}
        servicios={listaServicios}
        imagenObligatoria
        tituloFormulario="Agregar un trabajo"
        textoBoton="Agregar al portafolio"
        onGuardar={agregar}
      />

      <EstadoCarga
        cargando={trabajos.cargando && !trabajos.datos}
        error={trabajos.error}
        onReintentar={trabajos.recargar}
        texto="Cargando tu portafolio…"
      />

      {trabajos.datos && !trabajos.error && (
        lista.length === 0 ? (
          <div className="solicitudes-vacio">
            <span aria-hidden="true" style={{ fontSize: '2.4rem' }}>🖼️</span>
            <p>Todavía no tienes trabajos en tu portafolio.</p>
          </div>
        ) : (
          <div className="trabajos-grid">
            {lista.map((trabajo) => (
              <article className="tarjeta-trabajo" key={trabajo.id}>
                {editando === trabajo.id ? (
                  <FormularioTrabajo
                    idBase={`trabajo-${trabajo.id}`}
                    inicial={{
                      titulo: trabajo.titulo,
                      descripcion: trabajo.descripcion,
                      servicio: trabajo.servicio === null ? '' : String(trabajo.servicio),
                      activo: trabajo.activo,
                    }}
                    servicios={listaServicios}
                    imagenObligatoria={false}
                    tituloFormulario="Editar trabajo"
                    textoBoton="Guardar cambios"
                    onGuardar={(datos) => guardarEdicion(trabajo.id, datos)}
                    onCancelar={() => setEditando(null)}
                  />
                ) : (
                  <>
                    <img src={trabajo.imagen} alt={trabajo.titulo} loading="lazy" />
                    <div className="trabajo-cuerpo">
                      <h3>{trabajo.titulo}</h3>
                      {trabajo.servicio_nombre && (
                        <span className="oficio">{trabajo.servicio_nombre}</span>
                      )}
                      <p>{trabajo.descripcion}</p>
                      {!trabajo.activo && (
                        <span className="estado-solicitud estado-cancelada">Oculto</span>
                      )}
                      <div className="solicitud-acciones">
                        <button
                          type="button"
                          className="boton-secundario"
                          onClick={() => {
                            setExito('');
                            setEditando(trabajo.id);
                          }}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="boton-secundario boton-peligro"
                          disabled={ocupado}
                          onClick={() => eliminar(trabajo)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </article>
            ))}
          </div>
        )
      )}
    </section>
  );
}

export default MiPortafolio;