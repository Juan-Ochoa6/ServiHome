import { useState } from 'react';
import { ErrorApi } from '../services/api.js';
import { actualizarPerfil } from '../services/cuenta.js';
import Campo from './Campo.jsx';
import Mensaje from './Mensaje.jsx';

function primerMensaje(valor) {
  return Array.isArray(valor) ? valor[0] : (valor ?? '');
}

function FormularioPerfil({ perfil, esProfesional, onGuardado }) {
  const [datos, setDatos] = useState({
    first_name: perfil.first_name ?? '',
    last_name: perfil.last_name ?? '',
    email: perfil.email ?? '',
    telefono: perfil.telefono ?? '',
    direccion: perfil.direccion ?? '',
    descripcion_profesional: perfil.descripcion_profesional ?? '',
    experiencia_anos: String(perfil.experiencia_anos ?? 0),
  });
  const [errores, setErrores] = useState({});
  const [errorGeneral, setErrorGeneral] = useState('');
  const [exito, setExito] = useState('');
  const [guardando, setGuardando] = useState(false);

  function actualizar(evento) {
    const { name, value } = evento.target;
    setDatos((actual) => ({ ...actual, [name]: value }));
  }

  async function guardar(evento) {
    evento.preventDefault();
    setErrores({});
    setErrorGeneral('');
    setExito('');
    setGuardando(true);

    const cuerpo = {
      first_name: datos.first_name.trim(),
      last_name: datos.last_name.trim(),
      email: datos.email.trim(),
      telefono: datos.telefono.trim(),
      direccion: datos.direccion.trim(),
    };

    if (esProfesional) {
      cuerpo.descripcion_profesional = datos.descripcion_profesional.trim();
      cuerpo.experiencia_anos = Number(datos.experiencia_anos || 0);
    }

    try {
      await actualizarPerfil(cuerpo);
      setExito('Perfil actualizado.');
      onGuardado();
    } catch (err) {
      if (err instanceof ErrorApi && err.status === 400 && err.datos && typeof err.datos === 'object') {
        setErrores(err.datos);
      } else {
        setErrorGeneral(err.message);
      }
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form className="formulario-panel" onSubmit={guardar}>
      <h3>Mis datos</h3>
      <p className="solicitud-meta">
        Usuario: <strong>{perfil.username}</strong>
      </p>

      <Campo id="cuenta-nombres" etiqueta="Nombres" error={primerMensaje(errores.first_name)}>
        <input
          id="cuenta-nombres"
          name="first_name"
          type="text"
          autoComplete="given-name"
          value={datos.first_name}
          onChange={actualizar}
        />
      </Campo>

      <Campo id="cuenta-apellidos" etiqueta="Apellidos" error={primerMensaje(errores.last_name)}>
        <input
          id="cuenta-apellidos"
          name="last_name"
          type="text"
          autoComplete="family-name"
          value={datos.last_name}
          onChange={actualizar}
        />
      </Campo>

      <Campo id="cuenta-email" etiqueta="Correo electrónico" error={primerMensaje(errores.email)}>
        <input
          id="cuenta-email"
          name="email"
          type="email"
          autoComplete="email"
          value={datos.email}
          onChange={actualizar}
          required
        />
      </Campo>

      <Campo id="cuenta-telefono" etiqueta="Teléfono" error={primerMensaje(errores.telefono)}>
        <input
          id="cuenta-telefono"
          name="telefono"
          type="tel"
          autoComplete="tel"
          maxLength={20}
          value={datos.telefono}
          onChange={actualizar}
        />
      </Campo>

      <Campo id="cuenta-direccion" etiqueta="Dirección" error={primerMensaje(errores.direccion)}>
        <input
          id="cuenta-direccion"
          name="direccion"
          type="text"
          autoComplete="street-address"
          maxLength={255}
          value={datos.direccion}
          onChange={actualizar}
        />
      </Campo>

      {esProfesional && (
        <>
          <Campo
            id="cuenta-descripcion"
            etiqueta="Descripción profesional"
            error={primerMensaje(errores.descripcion_profesional)}
          >
            <textarea
              id="cuenta-descripcion"
              name="descripcion_profesional"
              rows={4}
              placeholder="Cuéntales a tus clientes quién eres y qué sabes hacer."
              value={datos.descripcion_profesional}
              onChange={actualizar}
            />
          </Campo>

          <Campo
            id="cuenta-experiencia"
            etiqueta="Años de experiencia"
            error={primerMensaje(errores.experiencia_anos)}
          >
            <input
              id="cuenta-experiencia"
              name="experiencia_anos"
              type="number"
              min="0"
              step="1"
              inputMode="numeric"
              value={datos.experiencia_anos}
              onChange={actualizar}
            />
          </Campo>
        </>
      )}

      <Mensaje tipo="exito">{exito}</Mensaje>
      <Mensaje tipo="error">{errorGeneral}</Mensaje>

      <button type="submit" className="boton-contactar" disabled={guardando}>
        {guardando ? 'Guardando…' : 'Guardar cambios'}
      </button>
    </form>
  );
}

export default FormularioPerfil;